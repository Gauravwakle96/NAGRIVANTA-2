import base64
import importlib.util
import json
import os
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.cookies import SimpleCookie
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "server.py"
spec = importlib.util.spec_from_file_location("nagrivanta_server", MODULE_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(2)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        app.DB_PATH = root / "test.sqlite3"
        app.UPLOADS_DIR = root / "private-files"
        app.init_db()
        self.accounts = {}
        with app.db_session() as db:
            for role, email, name in [
                ("system_admin", "admin@example.test", "System Admin"),
                ("municipal_admin", "municipal@example.test", "Municipal Reviewer"),
                ("citizen", "citizen@example.test", "Citizen One"),
                ("citizen", "other@example.test", "Citizen Two"),
                ("field_worker", "worker@example.test", "Field Worker"),
                ("field_worker", "otherworker@example.test", "Other Worker"),
                ("inspector", "inspector@example.test", "Inspector One"),
            ]:
                self.accounts[role + email] = app.create_user(db,email,name,"Correct-Horse-2026!",role)["id"]
        self.admin = self.login("admin@example.test")
        self.municipal = self.login("municipal@example.test")
        self.citizen = self.login("citizen@example.test")
        self.other_citizen = self.login("other@example.test")
        self.worker = self.login("worker@example.test")
        self.other_worker = self.login("otherworker@example.test")
        self.inspector = self.login("inspector@example.test")

    def tearDown(self):
        self.temp.cleanup()

    def request(self, path, body=None, method="GET", session=None, origin=None):
        raw = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"}
        if session:
            headers["Cookie"] = f"nagrivanta_session={session['cookie']}"
            if session.get("csrf"):
                headers["X-CSRF-Token"] = session["csrf"]
        if origin:
            headers["Origin"] = origin
        req = urllib.request.Request(self.base + path, data=raw, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read()
                return response.status, self.decode(response.headers.get("Content-Type", ""), data), response.headers
        except urllib.error.HTTPError as error:
            data = error.read()
            return error.code, self.decode(error.headers.get("Content-Type", ""), data), error.headers

    @staticmethod
    def decode(content_type, data):
        if "application/json" in content_type:
            return json.loads(data or b"{}")
        return data

    def login(self, email):
        code, data, headers = self.request("/api/auth/login", {"email": email, "password": "Correct-Horse-2026!"}, "POST")
        self.assertEqual(code, 200, data)
        cookie = SimpleCookie(headers.get("Set-Cookie", ""))["nagrivanta_session"].value
        return {"cookie": cookie, "csrf": data["csrf_token"]}

    def new_report(self, session=None, **overrides):
        payload = {
            "title": "Blocked drain outside community clinic",
            "category": "Water Supply and Drainage",
            "subcategory": "Blocked drain",
            "description": "A blocked drain is pooling water over the public footpath outside the community clinic.",
            "area": "Ward Test",
            "address": "Cedar Street near clinic",
            "before_photo": app.sample_photo("test evidence"),
            "latitude": 18.5204,
            "longitude": 73.8567,
        }
        payload.update(overrides)
        return self.request("/api/reports", payload, "POST", session or self.citizen)

    def assign(self, report_id, worker=None):
        return self.request(f"/api/reports/{report_id}", {
            "action": "assign", "department": "Drainage",
            "worker_id": self.accounts["field_workerworker@example.test"] if worker is None else worker,
        }, "POST", self.municipal)

    def test_unauthenticated_api_data_and_mutations_are_blocked(self):
        self.assertEqual(self.request("/api/reports")[0], 401)
        self.assertEqual(self.request("/api/auth/me")[1]["authenticated"], False)
        code, data, _ = self.request("/api/reports", {}, "POST")
        self.assertEqual(code, 401)
        self.assertIn("Sign in", data["error"])
        code, _, _ = self.request("/api/analytics")
        self.assertEqual(code, 401)

    def test_admin_entry_route_serves_only_the_role_aware_sign_in_shell(self):
        code, page, headers = self.request("/admin")
        self.assertEqual(code, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn(b"Sign in to your workspace", page)
        # Dashboard data remains backend-protected regardless of the entry URL.
        self.assertEqual(self.request("/api/admin/users")[0], 401)

    def test_registration_creates_citizen_and_rejects_privileged_role(self):
        code, data, headers = self.request("/api/auth/register", {
            "email": "new.citizen@example.test", "display_name": "New Citizen", "password": "Another-Strong-2026!"
        }, "POST")
        self.assertEqual(code, 201, data)
        self.assertEqual(data["user"]["role"], "citizen")
        cookie = SimpleCookie(headers.get("Set-Cookie", ""))["nagrivanta_session"].value
        self.assertIn("HttpOnly", headers.get("Set-Cookie", ""))
        self.assertIn("SameSite=Lax", headers.get("Set-Cookie", ""))
        self.assertEqual(self.request("/api/auth/me", session={"cookie": cookie})[0], 200)
        code, data, _ = self.request("/api/auth/register", {
            "email": "attacker@example.test", "display_name": "Attacker",
            "password": "Another-Strong-2026!", "role": "system_admin"
        }, "POST")
        self.assertEqual(code, 400)
        self.assertIn("citizen", data["error"])

    def test_login_errors_logout_and_csrf(self):
        code, data, _ = self.request("/api/auth/login", {"email": "citizen@example.test", "password": "bad"}, "POST")
        self.assertEqual(code, 401)
        self.assertEqual(data["error"], "Email or password is incorrect.")
        no_csrf = {"cookie": self.citizen["cookie"], "csrf": ""}
        code, data, _ = self.request("/api/notifications", {}, "POST", no_csrf)
        self.assertEqual(code, 403)
        code, _, _ = self.request("/api/auth/logout", {}, "POST", no_csrf)
        self.assertEqual(code, 403)
        code, _, _ = self.request("/api/auth/logout", {}, "POST", self.citizen)
        self.assertEqual(code, 200)
        self.assertEqual(self.request("/api/auth/me", session=self.citizen)[1]["authenticated"], False)

    def test_password_change_rotates_session_and_revokes_prior_cookie(self):
        code, data, headers = self.request("/api/auth/password", {
            "current_password":"Correct-Horse-2026!","new_password":"Changed-Strong-2026!"
        }, "POST", self.citizen)
        self.assertEqual(code,200,data)
        fresh=SimpleCookie(headers.get("Set-Cookie",""))["nagrivanta_session"].value
        self.assertNotEqual(fresh,self.citizen["cookie"])
        self.assertEqual(self.request("/api/auth/me",session=self.citizen)[1]["authenticated"],False)
        self.assertEqual(self.request("/api/auth/me",session={"cookie":fresh})[0],200)
        code, _, _ = self.request("/api/auth/login", {
            "email":"citizen@example.test","password":"Changed-Strong-2026!"
        },"POST")
        self.assertEqual(code,200)

    def test_login_throttles_repeated_failures(self):
        for attempt in range(9):
            code, _, _ = self.request("/api/auth/login", {
                "email":"citizen@example.test","password":"wrong-password"
            },"POST")
            self.assertEqual(code,401,f"attempt {attempt+1}")
        code, data, _ = self.request("/api/auth/login", {
            "email":"citizen@example.test","password":"wrong-password"
        },"POST")
        self.assertEqual(code,429)
        self.assertIn("Too many",data["error"])

    def test_auth_rejects_cross_origin_and_reports_errors_without_tracebacks(self):
        code, data, _ = self.request("/api/auth/login", {
            "email":"admin@example.test","password":"Correct-Horse-2026!"
        },"POST",origin="https://attacker.invalid")
        self.assertEqual(code,403)
        self.assertIn("origin",data["error"].lower())
        code, data, _ = self.request("/api/auth/register", {
            "email":"bad","display_name":"Name","password":"Another-Strong-2026!"
        },"POST")
        self.assertEqual(code,400)
        self.assertNotIn("Traceback",str(data))

    def test_complete_workflow_access_control_notifications_and_persistence(self):
        code, result, _ = self.new_report()
        self.assertEqual(code, 201, result)
        report = result["report"]
        report_id = report["id"]
        self.assertTrue(report_id.startswith("NG-"))
        self.assertIsNotNone(report["before_evidence_id"])
        self.assertEqual((report["latitude"], report["longitude"]), (18.5204, 73.8567))
        self.assertEqual(self.request("/api/reports")[0], 401)
        own = self.request("/api/reports", session=self.citizen)[1]["reports"]
        self.assertEqual([item["id"] for item in own], [report_id])
        self.assertEqual(self.request(f"/api/reports/{report_id}", session=self.other_citizen)[0], 404)
        self.assertEqual(self.request(f"/api/evidence/{report['before_evidence_id']}", session=self.other_citizen)[0], 404)
        self.assertEqual(self.request(f"/api/evidence/{report['before_evidence_id']}", session=self.citizen)[0], 200)
        self.assertEqual(self.assign(report_id)[0], 200)
        self.assertEqual(self.request(f"/api/reports/{report_id}", {"action":"work_start"}, "POST", self.other_worker)[0], 404)
        code, assigned, _ = self.request(f"/api/reports/{report_id}", {"action":"assign","department":"Drainage","worker_id":self.accounts["field_workerworker@example.test"]}, "POST", self.worker)
        self.assertEqual(code, 403)
        self.assertIn("Municipal", assigned["error"])
        code, data, _ = self.request(f"/api/reports/{report_id}", {"action":"work_start"}, "POST", self.worker)
        self.assertEqual(code, 200, data)
        self.assertEqual(data["report"]["status"], "in_progress")
        code, data, _ = self.request(f"/api/reports/{report_id}", {
            "action":"repair", "repair_note":"Removed accumulated debris and checked water flow.",
            "after_photo":app.sample_photo("completed repair")
        }, "POST", self.worker)
        self.assertEqual(code, 200, data)
        self.assertEqual(data["report"]["status"], "repair_submitted")
        self.assertEqual(self.request(f"/api/reports/{report_id}", {"action":"verify"}, "POST", self.worker)[0], 403)
        checks = {str(i):True for i in range(1,6)}
        code, data, _ = self.request(f"/api/reports/{report_id}", {
            "action":"verify", "approved":True,"checks":{"1":True},"notes":"Checked work."
        }, "POST", self.inspector)
        self.assertEqual(code, 400)
        self.assertIn("five", data["error"].lower())
        code, data, _ = self.request(f"/api/reports/{report_id}", {
            "action":"verify", "approved":True,"checks":checks,"notes":"Drain is clear and the path is safe."
        }, "POST", self.inspector)
        self.assertEqual(code, 200, data)
        self.assertEqual(data["report"]["status"], "verified")
        citizen_report = self.request(f"/api/reports/{report_id}", session=self.citizen)[1]["report"]
        self.assertEqual(citizen_report["status"], "verified")
        self.assertEqual(self.request("/api/notifications", session=self.citizen)[1]["unread_count"], 4)
        self.assertGreaterEqual(self.request("/api/notifications", session=self.worker)[1]["unread_count"], 2)
        self.assertEqual(self.request("/api/analytics", session=self.municipal)[0], 200)
        self.assertEqual(self.request("/api/admin/users", session=self.municipal)[0], 403)
        self.assertEqual(self.request("/api/admin/users", session=self.admin)[0], 200)
        # Startup migration is additive; completed workflow state and files remain readable after restart.
        app.init_db()
        with app.db_session() as db:
            saved = db.execute("SELECT status,before_photo,after_photo FROM reports WHERE id=?", (report_id,)).fetchone()
            self.assertEqual(saved["status"], "verified")
            self.assertTrue(saved["before_photo"].startswith("evidence:"))
            self.assertTrue(saved["after_photo"].startswith("evidence:"))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM inspections WHERE report_id=?", (report_id,)).fetchone()[0],1)

    def test_rejected_inspection_preserves_rework_history(self):
        code, created, _ = self.new_report()
        rid = created["report"]["id"]
        self.assertEqual(self.assign(rid)[0], 200)
        self.assertEqual(self.request(f"/api/reports/{rid}", {"action":"work_start"}, "POST", self.worker)[0], 200)
        self.assertEqual(self.request(f"/api/reports/{rid}", {
            "action":"repair","repair_note":"Initial repair attempt.","after_photo":app.sample_photo("attempt one")
        }, "POST", self.worker)[0], 200)
        checks = {str(i):True for i in range(1,6)}
        checks["4"] = False
        code, data, _ = self.request(f"/api/reports/{rid}", {
            "action":"verify","approved":False,"checks":checks,"notes":"One inspection check failed; repair the uneven edge."
        }, "POST", self.inspector)
        self.assertEqual(code,200,data)
        self.assertEqual(data["report"]["status"],"needs_rework")
        self.assertEqual(self.assign(rid)[0],200)
        self.assertEqual(self.request(f"/api/reports/{rid}", {"action":"work_start"}, "POST", self.worker)[0],200)
        self.assertEqual(self.request(f"/api/reports/{rid}", {
            "action":"repair","repair_note":"Repaired the edge and checked the surface again.","after_photo":app.sample_photo("attempt two")
        }, "POST", self.worker)[0],200)
        self.assertEqual(self.request(f"/api/reports/{rid}", {
            "action":"verify","approved":True,"checks":{str(i):True for i in range(1,6)},"notes":"All five checks pass."
        }, "POST", self.inspector)[0],200)
        with app.db_session() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM inspections WHERE report_id=?",(rid,)).fetchone()[0],2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM repair_submissions WHERE report_id=?",(rid,)).fetchone()[0],2)

    def test_validation_triage_and_unsafe_upload_rejection(self):
        unsafe = "data:image/svg+xml;base64," + base64.b64encode(b'<svg onload="alert(1)"></svg>').decode()
        code, data, _ = self.new_report(before_photo=unsafe)
        self.assertEqual(code,400)
        self.assertIn("SVG",data["error"])
        code, data, _ = self.new_report(category=["Road damage"])
        self.assertEqual(code,400)
        self.assertIn("category",data["error"].lower())
        code, data, _ = self.new_report(latitude=999,longitude=73.8)
        self.assertEqual(code,400)
        self.assertIn("coordinate",data["error"].lower())
        code, data, _ = self.request("/api/triage",{"description":"Garbage is overflowing from a public bin."},"POST")
        self.assertEqual(code,200)
        self.assertEqual(data["recommendation"]["method"],"rule-based")
        self.assertIn("human review",data["recommendation"]["explanation"].lower())

    def test_admin_can_manage_accounts_and_routing_but_citizen_cannot(self):
        code, data, _ = self.request("/api/admin/users", {
            "email":"crew2@example.test","display_name":"Crew Two","password":"Temporary-Password-2026!","role":"field_worker"
        }, "POST", self.admin)
        self.assertEqual(code,201,data)
        worker_id=data["user"]["id"]
        code, _, _ = self.request(f"/api/admin/users/{worker_id}", {"role":"inspector","active":True}, "POST", self.admin)
        self.assertEqual(code,200)
        code, data, _ = self.request("/api/admin/config/categories", {
            "category":"Test Civic Category","subcategory":"Test route","department_id":"roads",
            "default_priority":55,"escalation_hours":72,"keywords":"test route","active":True
        }, "POST", self.admin)
        self.assertEqual(code,200,data)
        config=self.request("/api/admin/config",session=self.admin)[1]
        self.assertTrue(any(c["category"]=="Test Civic Category" for c in config["categories"]))
        self.assertEqual(self.request("/api/admin/config",session=self.citizen)[0],403)
        self.assertEqual(self.request("/api/admin/config/categories", {
            "category":"Forbidden","subcategory":"Route","department_id":"roads"
        }, "POST", self.citizen)[0],403)

    def test_department_routing_and_data_derived_analytics(self):
        code, created, _ = self.new_report(category="Heritage and Historical Sites",
            subcategory="Monument vandalism, graffiti or defacement",title="Graffiti on old stone gate")
        self.assertEqual(code,201,created)
        self.assertIn("Heritage",created["recommendation"]["department"])
        metrics=self.request("/api/analytics",session=self.municipal)[1]["analytics"]
        self.assertGreaterEqual(metrics["total"],1)
        self.assertEqual(metrics["verified_resolutions"],0)
        self.assertIsNone(metrics["average_resolution_hours"])
        self.assertIn("default 168 hours",metrics["definitions"]["overdue"])

    def test_fresh_database_startup_does_not_seed_demo_reports(self):
        with app.db_session() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM reports").fetchone()[0], 0)

    def test_demo_reset_requires_system_admin_and_explicit_flag(self):
        previous=os.environ.get("NAGRIVANTA_DEMO_RESET")
        try:
            os.environ.pop("NAGRIVANTA_DEMO_RESET",None)
            self.assertEqual(self.request("/api/demo/reset",{},"POST",self.admin)[0],403)
            self.assertEqual(self.request("/api/demo/reset",{},"POST",self.municipal)[0],403)
            os.environ["NAGRIVANTA_DEMO_RESET"]="1"
            self.assertEqual(self.request("/api/demo/reset",{},"POST",self.citizen)[0],403)
            code, data, _ = self.request("/api/demo/reset",{},"POST",self.admin)
            self.assertEqual(code,200,data)
            self.assertEqual(len(data["reports"]),4)
            self.assertTrue(all(report["synthetic"] for report in data["reports"]))
        finally:
            if previous is not None:
                os.environ["NAGRIVANTA_DEMO_RESET"]=previous
            else:
                os.environ.pop("NAGRIVANTA_DEMO_RESET",None)

    def test_bootstrap_creates_only_the_first_admin_and_never_promotes_a_citizen(self):
        keys = (
            "NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL",
            "NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD",
            "NAGRIVANTA_BOOTSTRAP_ADMIN_NAME",
        )
        previous_env = {key: os.environ.get(key) for key in keys}
        previous_db, previous_uploads = app.DB_PATH, app.UPLOADS_DIR
        with tempfile.TemporaryDirectory() as folder:
            try:
                for key in keys:
                    os.environ.pop(key, None)
                app.DB_PATH = Path(folder) / "bootstrap.sqlite3"
                app.UPLOADS_DIR = Path(folder) / "uploads"
                app.init_db()
                with app.db_session() as db:
                    app.create_user(db, "citizen@example.test", "Existing Citizen",
                                    "Citizen-Password-2026!", "citizen")

                os.environ["NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL"] = "citizen@example.test"
                os.environ["NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD"] = "Strong-Admin-2026!"
                with self.assertRaisesRegex(RuntimeError, "already belongs"):
                    app.bootstrap_admin()
                with app.db_session() as db:
                    row = db.execute("SELECT role FROM users WHERE email=?",
                                     ("citizen@example.test",)).fetchone()
                    self.assertEqual(row["role"], "citizen")
                    self.assertEqual(db.execute(
                        "SELECT COUNT(*) FROM users WHERE role='system_admin'").fetchone()[0], 0)

                os.environ["NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL"] = "initial-admin@example.test"
                app.bootstrap_admin()
                app.bootstrap_admin()
                with app.db_session() as db:
                    self.assertEqual(db.execute(
                        "SELECT COUNT(*) FROM users WHERE role='system_admin'").fetchone()[0], 1)

                # A later deployment with different bootstrap values must not
                # silently create a second admin or rotate the first account.
                os.environ["NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL"] = "second-admin@example.test"
                os.environ["NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD"] = "Different-Admin-2026!"
                app.bootstrap_admin()
                with app.db_session() as db:
                    self.assertEqual(db.execute(
                        "SELECT COUNT(*) FROM users WHERE role='system_admin'").fetchone()[0], 1)
                    self.assertIsNone(db.execute(
                        "SELECT 1 FROM users WHERE email='second-admin@example.test'").fetchone())
            finally:
                app.DB_PATH, app.UPLOADS_DIR = previous_db, previous_uploads
                for key, value in previous_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_sparse_legacy_migration_preserves_existing_complaint_identity(self):
        previous_db,previous_uploads=app.DB_PATH,app.UPLOADS_DIR
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"legacy.sqlite3"
            db=sqlite3.connect(path)
            db.execute("CREATE TABLE reports (id TEXT PRIMARY KEY, category TEXT NOT NULL, status TEXT NOT NULL, department TEXT)")
            db.execute("INSERT INTO reports(id,category,status,department) VALUES (?,?,?,?)",
                       ("NG-LEGACY-123","Road damage","submitted",None))
            db.commit();db.close()
            try:
                app.DB_PATH=path;app.UPLOADS_DIR=Path(folder)/"uploads";app.init_db()
                with app.db_session() as db:
                    row=db.execute("SELECT id,category,subcategory,suggested_department FROM reports WHERE id=?",
                                   ("NG-LEGACY-123",)).fetchone()
                self.assertEqual(row["id"],"NG-LEGACY-123")
                self.assertEqual(row["category"],"Road damage")
                self.assertEqual(row["suggested_department"],"Roads and Engineering")
            finally:
                app.DB_PATH=previous_db;app.UPLOADS_DIR=previous_uploads


if __name__ == "__main__":
    unittest.main(verbosity=2)
