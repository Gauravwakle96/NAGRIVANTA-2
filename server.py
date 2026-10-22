#!/usr/bin/env python3
"""Nagrivanta demo API: Python stdlib + SQLite, no third-party runtime dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json, os, re, sqlite3, uuid
from datetime import datetime, timezone
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(ROOT / "nagrivanta.sqlite3")))
PORT = int(os.environ.get("PORT", "8000"))
CATEGORIES = {"Road damage", "Water & drainage", "Streetlight", "Waste", "Other"}
MAX_BODY = 3_000_000


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def sample_photo(label, bg="#d9eee9", accent="#007d72"):
    # Clearly synthetic illustration, not a photograph or field evidence.
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520"><rect width="900" height="520" fill="{bg}"/><rect y="300" width="900" height="220" fill="#4c5964"/><path d="M0 390h900" stroke="#f5d46c" stroke-width="10" stroke-dasharray="55 35"/><rect x="78" y="146" width="220" height="154" rx="15" fill="#fff" opacity=".85"/><path d="M115 252l54-67 46 46 31-34 26 55z" fill="{accent}" opacity=".75"/><circle cx="244" cy="177" r="14" fill="#efad42"/><rect x="520" y="90" width="295" height="130" rx="24" fill="#fff" opacity=".88"/><text x="667" y="145" text-anchor="middle" font-family="Arial" font-size="24" font-weight="700" fill="#163245">SYNTHETIC DEMO</text><text x="667" y="182" text-anchor="middle" font-family="Arial" font-size="18" fill="#516273">{label}</text></svg>'''
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


@contextmanager
def db_session():
    db = connect()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    with db_session() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS reports (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL,
          description TEXT NOT NULL, area TEXT NOT NULL, address TEXT NOT NULL,
          before_photo TEXT NOT NULL, after_photo TEXT, status TEXT NOT NULL,
          completeness INTEGER NOT NULL, completeness_factors TEXT NOT NULL,
          priority INTEGER NOT NULL, priority_factors TEXT NOT NULL,
          master_id TEXT, duplicate_reason TEXT, department TEXT, crew TEXT,
          repair_note TEXT, verification TEXT, events TEXT NOT NULL,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          FOREIGN KEY(master_id) REFERENCES reports(id)
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')
        if db.execute('SELECT COUNT(*) FROM reports').fetchone()[0] == 0:
            seed_demo(db)


def tokenize(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def score_completeness(report):
    factors = [
      {"label":"Photo evidence attached", "points":30 if report.get("before_photo") else 0, "max":30},
      {"label":"Description has useful detail", "points":25 if len((report.get("description") or "").split()) >= 8 else 10, "max":25},
      {"label":"Area supplied", "points":20 if report.get("area", "").strip() else 0, "max":20},
      {"label":"Specific location supplied", "points":25 if report.get("address", "").strip() else 0, "max":25},
    ]
    return min(100, sum(f["points"] for f in factors)), factors


def priority_for(report, corroborating_count=1):
    category_points = {"Road damage":24, "Water & drainage":22, "Streetlight":17, "Waste":13, "Other":12}.get(report["category"], 12)
    safety_terms = ("school", "traffic", "accident", "danger", "open manhole", "injury", "electric shock", "flood")
    text = (report.get("title", "") + " " + report.get("description", "")).lower()
    safety = 22 if any(term in text for term in safety_terms) else 0
    corroboration = min(20, max(0, (corroborating_count - 1) * 7))
    evidence = 10 if report.get("before_photo") else 0
    age = 5
    points = min(100, category_points + safety + corroboration + evidence + age)
    factors = [
      {"label":f"Issue category: {report['category']}", "points":category_points},
      {"label":"Safety keyword present" if safety else "No safety keyword detected", "points":safety},
      {"label":f"Corroborating reports ({corroborating_count})", "points":corroboration},
      {"label":"Initial evidence attached" if evidence else "No initial evidence", "points":evidence},
      {"label":"Baseline age factor", "points":age},
    ]
    return points, factors


def event(actor, action, note=""):
    return {"at": now(), "actor": actor, "action": action, "note": note}


def pack(row):
    item = dict(row)
    for key in ("completeness_factors", "priority_factors", "verification", "events"):
        if item.get(key):
            item[key] = json.loads(item[key])
    return item


def all_reports(db):
    rows = db.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    return [pack(row) for row in rows]


def find_duplicate(db, report):
    candidates = db.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    target_tokens = tokenize(report["title"] + " " + report["description"])
    for row in candidates:
        old = dict(row)
        if old["category"] != report["category"]:
            continue
        same_area = old["area"].strip().casefold() == report["area"].strip().casefold()
        same_address = old["address"].strip().casefold() == report["address"].strip().casefold()
        if not same_area and not same_address:
            continue
        old_tokens = tokenize(old["title"] + " " + old["description"])
        union = target_tokens | old_tokens
        similarity = len(target_tokens & old_tokens) / max(1, len(union))
        if same_address or similarity >= 0.28:
            root = old["master_id"] or old["id"]
            reason = "same category + same specific location" if same_address else f"same category + area; text overlap {round(similarity * 100)}%"
            return root, reason
    return None, None


def insert_report(db, data, *, status="submitted", department=None, crew=None, after_photo=None, repair_note=None, verification=None, events=None, created_at=None):
    rid = data.get("id") or "NG-" + uuid.uuid4().hex[:7].upper()
    data = {**data, "id":rid}
    completeness, cf = score_completeness(data)
    master_id, reason = find_duplicate(db, data)
    provisional_count = 1
    if master_id:
        provisional_count = 1 + db.execute("SELECT COUNT(*) FROM reports WHERE master_id=? OR id=?", (master_id, master_id)).fetchone()[0]
    priority, pf = priority_for(data, provisional_count)
    created = created_at or now()
    ev = events or [event("Citizen", "Report submitted", "Synthetic demo record" if data.get("synthetic") else "")]
    if master_id:
        ev.append(event("System", "Linked to master issue", reason or "Possible duplicate"))
    db.execute('''INSERT INTO reports (id,title,category,description,area,address,before_photo,after_photo,status,
      completeness,completeness_factors,priority,priority_factors,master_id,duplicate_reason,department,crew,repair_note,
      verification,events,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (rid,data["title"],data["category"],data["description"],data["area"],data["address"],data["before_photo"],after_photo,status,
       completeness,json.dumps(cf),priority,json.dumps(pf),master_id,reason,department,crew,repair_note,
       json.dumps(verification) if verification is not None else None,json.dumps(ev),created,now()))
    # Recompute the master score after preserving each linked source report.
    root = master_id or rid
    group = db.execute("SELECT * FROM reports WHERE id=? OR master_id=?", (root, root)).fetchall()
    count = len(group)
    for member in group:
        p, factors = priority_for(dict(member), count)
        db.execute("UPDATE reports SET priority=?, priority_factors=?, updated_at=? WHERE id=?", (p,json.dumps(factors),now(),member["id"]))
    return rid, master_id, reason


def seed_demo(db):
    cases = [
      {"id":"NG-DEMO-101","title":"Pothole near school gate","category":"Road damage","description":"Deep pothole at the school gate creates a traffic and pedestrian safety risk. The road surface is broken and visible in the attached sample evidence.","area":"Ward 12","address":"Lake Road, near school gate","before_photo":sample_photo("Pothole • before", "#e5f0f8", "#e1a93c"),"synthetic":True},
      {"id":"NG-DEMO-102","title":"Road damage outside school gate","category":"Road damage","description":"Large pothole by the school gate on Lake Road; vehicles swerve around the damaged surface.","area":"Ward 12","address":"Lake Road, near school gate","before_photo":sample_photo("Corroborating report", "#e9f2e7", "#087e75"),"synthetic":True},
      {"id":"NG-DEMO-103","title":"Streetlight out on Market Lane","category":"Streetlight","description":"Streetlight has not worked for three evenings. The dark corner is beside the bus stop.","area":"Ward 8","address":"Market Lane, bus stop","before_photo":sample_photo("Streetlight • before", "#f3eddf", "#e1a93c"),"synthetic":True},
      {"id":"NG-DEMO-104","title":"Blocked drain after rain","category":"Water & drainage","description":"Drain is blocked and water is pooling across the footpath after rainfall.","area":"Ward 4","address":"Cedar Street, community clinic","before_photo":sample_photo("Drain • before", "#e4eef3", "#087e75"),"synthetic":True},
    ]
    for item in cases:
        if item["id"] == "NG-DEMO-103":
            insert_report(db,item,status="assigned",department="Electrical",crew="Crew B",events=[event("Citizen","Report submitted","Synthetic demo record"),event("Municipal","Work order assigned","Electrical • Crew B")])
        elif item["id"] == "NG-DEMO-104":
            insert_report(db,item,status="repair_submitted",department="Water & Sanitation",crew="Crew A",after_photo=sample_photo("Drain • after", "#e6f1e6", "#188a66"),repair_note="Removed debris from the drain; ready for inspection.",events=[event("Citizen","Report submitted","Synthetic demo record"),event("Municipal","Work order assigned","Water & Sanitation • Crew A"),event("Field Crew","Repair submitted","Synthetic after-evidence; inspect before closure")])
        else:
            insert_report(db,item)


def json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = "NagrivantaDemo/1.0"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY:
            raise ValueError("Request is too large (3 MB limit). Resize the image and try again.")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return json_response(self, {"ok":True,"service":"Nagrivanta demo API"})
        if path == "/api/reports":
            with db_session() as db:
                return json_response(self, {"reports":all_reports(db)})
        if path.startswith("/api/reports/"):
            rid = path.rsplit("/",1)[-1]
            with db_session() as db:
                row = db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
                if not row: return json_response(self,{"error":"Issue not found."},404)
                return json_response(self,{"report":pack(row)})
        return self.static_file(path)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.body()
            if path == "/api/reports":
                return self.create_report(data)
            if path == "/api/demo/reset":
                with db_session() as db:
                    db.execute("UPDATE reports SET master_id=NULL")
                    db.execute("DELETE FROM reports")
                    seed_demo(db)
                    return json_response(self,{"ok":True,"reports":all_reports(db)})
            if path.startswith("/api/reports/"):
                rid = path.split("/")[3]
                return self.transition(rid,data)
            return json_response(self,{"error":"Endpoint not found."},404)
        except ValueError as exc:
            return json_response(self,{"error":str(exc)},400)
        except Exception as exc:
            print("Request error:",repr(exc))
            return json_response(self,{"error":"The request could not be completed. Please retry."},500)

    def create_report(self, data):
        for key, label in (("title","Short title"),("description","Description"),("area","Ward / area"),("address","Specific location"),("before_photo","Photo evidence")):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError(f"{label} is required.")
        if data.get("category") not in CATEGORIES:
            raise ValueError("Choose a valid issue category.")
        if len(data["title"]) > 100 or len(data["description"]) > 1200:
            raise ValueError("Title or description is too long.")
        self.validate_photo(data["before_photo"],"Initial photo")
        data = {k:data[k].strip() if isinstance(data.get(k),str) else data.get(k) for k in ("title","category","description","area","address","before_photo")}
        with db_session() as db:
            rid, master, reason = insert_report(db,data)
            row = db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
            return json_response(self,{"report":pack(row),"duplicate":({"master_id":master,"reason":reason} if master else None)},201)

    @staticmethod
    def validate_photo(value, label):
        if not isinstance(value,str) or not value.startswith("data:image/") or len(value) > 1_500_000:
            raise ValueError(f"{label} must be an image under about 1 MB.")

    def transition(self, rid, data):
        action=data.get("action")
        actor=data.get("actor","Demo role")
        with db_session() as db:
            row=db.execute("SELECT * FROM reports WHERE id=?",(rid,)).fetchone()
            if not row: return json_response(self,{"error":"Issue not found."},404)
            r=pack(row)
            events=r["events"]
            if action == "assign":
                if r["status"] not in ("submitted","needs_rework"):
                    raise ValueError("Only new or returned issues can be assigned.")
                department=(data.get("department") or "").strip()
                crew=(data.get("crew") or "").strip()
                if not department or not crew: raise ValueError("Select a department and crew.")
                status="assigned"
                events.append(event(actor,"Work order assigned",f"{department} • {crew}"))
                db.execute("UPDATE reports SET department=?,crew=?,status=?,events=?,updated_at=? WHERE id=?",(department,crew,status,json.dumps(events),now(),rid))
            elif action == "repair":
                if r["status"] not in ("assigned","needs_rework"):
                    raise ValueError("This issue is not ready for repair evidence.")
                photo=data.get("after_photo")
                self.validate_photo(photo,"After photo")
                note=(data.get("repair_note") or "").strip()
                if not note: raise ValueError("Add a short repair note.")
                status="repair_submitted"
                events.append(event(actor,"Repair submitted","Before/after evidence sent for inspection"))
                db.execute("UPDATE reports SET after_photo=?,repair_note=?,status=?,verification=NULL,events=?,updated_at=? WHERE id=?",(photo,note,status,json.dumps(events),now(),rid))
            elif action == "verify":
                if r["status"] != "repair_submitted": raise ValueError("Only submitted repairs can be inspected.")
                checks=data.get("checks") or []
                notes=(data.get("notes") or "").strip()
                approved=bool(data.get("approved"))
                if approved and set(checks) != {"1", "2", "3", "4", "5"}: raise ValueError("All five inspection checks must pass before verified closure.")
                if not notes: raise ValueError("Add an inspection note for the audit trail.")
                verification={"checks":checks,"approved":approved,"notes":notes,"inspected_at":now()}
                status="verified" if approved else "needs_rework"
                events.append(event(actor,"Repair verified" if approved else "Returned for rework",notes))
                db.execute("UPDATE reports SET verification=?,status=?,events=?,updated_at=? WHERE id=?",(json.dumps(verification),status,json.dumps(events),now(),rid))
            else:
                raise ValueError("Choose a supported workflow action.")
            updated=db.execute("SELECT * FROM reports WHERE id=?",(rid,)).fetchone()
            return json_response(self,{"report":pack(updated)})

    def static_file(self,path):
        rel="index.html" if path in ("/","/") else path.lstrip("/")
        target=(PUBLIC/rel).resolve()
        if PUBLIC.resolve() not in target.parents and target != PUBLIC.resolve():
            return json_response(self,{"error":"Not found."},404)
        if not target.is_file():
            return json_response(self,{"error":"Not found."},404)
        content_type="text/html; charset=utf-8" if target.suffix==".html" else "text/css; charset=utf-8" if target.suffix==".css" else "text/javascript; charset=utf-8" if target.suffix==".js" else "application/octet-stream"
        body=target.read_bytes()
        self.send_response(200); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_OPTIONS(self):
        return json_response(self,{"ok":True})


if __name__ == "__main__":
    init_db()
    print(f"Nagrivanta running at http://127.0.0.1:{PORT}")
    print(f"SQLite database: {DB_PATH}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
