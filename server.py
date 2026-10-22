#!/usr/bin/env python3
"""Nagrivanta demo API: Python stdlib + SQLite, no third-party runtime dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import base64, json, os, re, sqlite3, uuid
from datetime import datetime, timezone
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(ROOT / "nagrivanta.sqlite3")))
PORT = int(os.environ.get("PORT", "8000"))
LEGACY_CATEGORY_GROUPS = {
    "Road damage": "Roads and Public Infrastructure",
    "Water & drainage": "Water Supply and Drainage",
    "Streetlight": "Electricity and Streetlights",
    "Waste": "Solid Waste Management and Sanitation",
    "Other": "Public Facilities and Municipal Services",
}
DEFAULT_DEPARTMENTS = [
    ("roads", "Roads and Engineering"),
    ("heritage", "Heritage Cell / Competent Authority"),
    ("water", "Water Supply"),
    ("drainage", "Drainage"),
    ("waste", "Solid Waste Management"),
    ("environment", "Gardens and Environment"),
    ("electrical", "Electrical / Street Lighting"),
    ("health", "Public Health"),
    ("encroachment", "Encroachment / Building Permission"),
    ("fire", "Fire Brigade / Disaster Management"),
    ("facilities", "Public Facilities / Municipal Services"),
    ("general", "General Municipal Services"),
]
DEFAULT_CATEGORIES = [
    ("Roads and Public Infrastructure", "Potholes and damaged roads", "roads", 60, "pothole road damage"),
    ("Roads and Public Infrastructure", "Broken footpaths and pavements", "roads", 50, "footpath pavement"),
    ("Roads and Public Infrastructure", "Damaged bridges and public structures", "roads", 75, "bridge structure"),
    ("Roads and Public Infrastructure", "Missing or damaged manhole covers", "roads", 75, "manhole cover"),
    ("Roads and Public Infrastructure", "Damaged road signs", "roads", 45, "road sign"),
    ("Roads and Public Infrastructure", "Unsafe road construction", "roads", 75, "unsafe construction"),
    ("Roads and Public Infrastructure", "Damaged public infrastructure", "roads", 50, "public infrastructure"),
    ("Heritage and Historical Sites", "Damage to historical buildings or structures", "heritage", 65, "heritage historical monument"),
    ("Heritage and Historical Sites", "Suspected unauthorized alteration (requires assessment)", "heritage", 65, "alteration construction"),
    ("Heritage and Historical Sites", "Monument vandalism, graffiti or defacement", "heritage", 60, "vandalism graffiti defacement"),
    ("Heritage and Historical Sites", "Neglected heritage location or precinct", "heritage", 45, "neglected precinct"),
    ("Heritage and Historical Sites", "Construction-related impact (unverified report)", "heritage", 65, "construction impact"),
    ("Water Supply and Drainage", "Water leakage", "water", 60, "water leak"),
    ("Water Supply and Drainage", "Water supply interruption or low pressure", "water", 50, "water supply pressure"),
    ("Water Supply and Drainage", "Discoloured or potentially contaminated water", "water", 80, "discoloured contaminated water"),
    ("Water Supply and Drainage", "Blocked drain", "drainage", 65, "blocked drain"),
    ("Water Supply and Drainage", "Sewage overflow", "drainage", 85, "sewage overflow"),
    ("Water Supply and Drainage", "Flooding or waterlogging", "drainage", 85, "flood waterlogging"),
    ("Water Supply and Drainage", "Damaged water infrastructure", "water", 65, "water infrastructure"),
    ("Solid Waste Management and Sanitation", "Garbage accumulation", "waste", 50, "garbage waste"),
    ("Solid Waste Management and Sanitation", "Overflowing public bin", "waste", 55, "overflowing bin"),
    ("Solid Waste Management and Sanitation", "Missed waste collection", "waste", 45, "missed collection"),
    ("Solid Waste Management and Sanitation", "Illegal dumping (reported; unverified)", "waste", 60, "dumping debris"),
    ("Solid Waste Management and Sanitation", "Construction debris", "waste", 55, "construction debris"),
    ("Solid Waste Management and Sanitation", "Public toilet maintenance", "waste", 45, "public toilet"),
    ("Solid Waste Management and Sanitation", "Open waste burning", "waste", 75, "waste burning smoke"),
    ("Solid Waste Management and Sanitation", "Unsanitary public space", "waste", 55, "unsanitary sanitation"),
    ("Gardens and Environment", "Damaged public garden or park equipment", "environment", 45, "garden park equipment"),
    ("Gardens and Environment", "Fallen tree or dangerous branch", "environment", 75, "fallen tree branch"),
    ("Gardens and Environment", "Damaged green space", "environment", 45, "green space"),
    ("Gardens and Environment", "Suspected illegal tree cutting (requires review)", "environment", 65, "tree cutting"),
    ("Gardens and Environment", "Pollution affecting a public area", "environment", 65, "pollution"),
    ("Gardens and Environment", "Neglected lake or water body", "environment", 55, "lake water body"),
    ("Gardens and Environment", "Damage to a designated natural feature", "environment", 60, "natural feature"),
    ("Electricity and Streetlights", "Non-functional streetlight", "electrical", 45, "streetlight lighting"),
    ("Electricity and Streetlights", "Exposed electrical wiring or public hazard", "electrical", 90, "exposed wiring electric shock"),
    ("Electricity and Streetlights", "Damaged public lighting", "electrical", 55, "public lighting"),
    ("Electricity and Streetlights", "Electrical hazard in a public facility", "electrical", 85, "electrical hazard"),
    ("Public Health", "Mosquito breeding", "health", 65, "mosquito breeding"),
    ("Public Health", "Pest infestation", "health", 60, "pest infestation"),
    ("Public Health", "Public sanitation hazard", "health", 65, "sanitation hazard"),
    ("Public Health", "Condition that may contribute to disease transmission", "health", 70, "disease health"),
    ("Encroachment and Building-Related Complaints", "Obstructed footpath or public access", "encroachment", 60, "obstructed footpath access"),
    ("Encroachment and Building-Related Complaints", "Encroachment on public space (unverified)", "encroachment", 55, "encroachment public space"),
    ("Encroachment and Building-Related Complaints", "Suspected unauthorized construction (unverified)", "encroachment", 60, "unauthorized construction"),
    ("Encroachment and Building-Related Complaints", "Construction debris obstructing road", "roads", 60, "construction debris road"),
    ("Fire Safety and Disaster Management", "Blocked emergency access", "fire", 90, "blocked emergency access"),
    ("Fire Safety and Disaster Management", "Storm-related public hazard", "fire", 75, "storm hazard"),
    ("Fire Safety and Disaster Management", "Flooding or fallen tree obstructing access", "fire", 85, "flood fallen tree access"),
    ("Fire Safety and Disaster Management", "Damaged public safety infrastructure", "fire", 80, "public safety infrastructure"),
    ("Public Facilities and Municipal Services", "Damaged public building", "facilities", 55, "public building"),
    ("Public Facilities and Municipal Services", "Municipal school maintenance", "facilities", 55, "school maintenance"),
    ("Public Facilities and Municipal Services", "Accessibility problem", "facilities", 60, "accessibility"),
    ("Public Facilities and Municipal Services", "Damaged community centre or public amenity", "facilities", 50, "community centre public amenity"),
    ("Public Facilities and Municipal Services", "Other municipal service issue", "general", 40, "municipal service"),
]
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
        # Additive migrations preserve existing report IDs and workflow history.
        columns = {row["name"] for row in db.execute("PRAGMA table_info(reports)")}
        for name, definition in (
            ("subcategory", "TEXT NOT NULL DEFAULT ''"),
            ("suggested_department", "TEXT"),
            ("synthetic", "INTEGER NOT NULL DEFAULT 0"),
        ):
            if name not in columns:
                db.execute(f"ALTER TABLE reports ADD COLUMN {name} {definition}")
        db.execute('''CREATE TABLE IF NOT EXISTS departments (
          id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, active INTEGER NOT NULL DEFAULT 1
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS issue_categories (
          id TEXT PRIMARY KEY, category TEXT NOT NULL, subcategory TEXT NOT NULL,
          department_id TEXT NOT NULL REFERENCES departments(id),
          default_priority INTEGER NOT NULL DEFAULT 40, keywords TEXT NOT NULL DEFAULT '',
          active INTEGER NOT NULL DEFAULT 1, UNIQUE(category, subcategory)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS routing_rules (
          id TEXT PRIMARY KEY, category_id TEXT NOT NULL REFERENCES issue_categories(id),
          department_id TEXT NOT NULL REFERENCES departments(id), priority INTEGER NOT NULL DEFAULT 100,
          active INTEGER NOT NULL DEFAULT 1
        )''')
        seed_catalog(db)
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_category_subcategory ON reports(category, subcategory)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_department ON reports(department)')
        # Backfill new fields without changing original report text or IDs.
        for row in db.execute("SELECT id, category, subcategory, suggested_department FROM reports").fetchall():
            group = canonical_category(row["category"])
            detail = row["subcategory"] or legacy_subcategory(row["category"])
            suggested = row["suggested_department"] or suggested_department(group, detail)
            db.execute("UPDATE reports SET subcategory=?, suggested_department=? WHERE id=?",
                       (detail, suggested, row["id"]))
        if db.execute('SELECT COUNT(*) FROM reports').fetchone()[0] == 0:
            seed_demo(db)


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def seed_catalog(db):
    for did, name in DEFAULT_DEPARTMENTS:
        db.execute("INSERT OR IGNORE INTO departments(id,name) VALUES (?,?)", (did, name))
    for category, subcategory, department_id, priority, keywords in DEFAULT_CATEGORIES:
        cid = slug(category + "-" + subcategory)
        db.execute("""INSERT OR IGNORE INTO issue_categories
          (id,category,subcategory,department_id,default_priority,keywords)
          VALUES (?,?,?,?,?,?)""", (cid, category, subcategory, department_id, priority, keywords))
    # Preserve five historic labels as accepted aliases for existing clients.
    for legacy, group in LEGACY_CATEGORY_GROUPS.items():
        db.execute("""INSERT OR IGNORE INTO issue_categories
          (id,category,subcategory,department_id,default_priority,keywords)
          VALUES (?,?,?,?,?,?)""",
          (slug(legacy + "-legacy"), group, legacy_subcategory(legacy),
           department_for(group, legacy_subcategory(legacy)), 45, legacy.lower()))
    for category_row in db.execute("SELECT id, department_id FROM issue_categories").fetchall():
        db.execute("""INSERT OR IGNORE INTO routing_rules(id,category_id,department_id,priority)
          VALUES (?,?,?,100)""",
          ("route-" + category_row["id"], category_row["id"], category_row["department_id"]))


def canonical_category(category):
    return LEGACY_CATEGORY_GROUPS.get(category, category)


def legacy_subcategory(category):
    return {
        "Road damage": "Potholes and damaged roads",
        "Water & drainage": "Blocked drain",
        "Streetlight": "Non-functional streetlight",
        "Waste": "Garbage accumulation",
        "Other": "Other municipal service issue",
    }.get(category, "")


def department_for(category, subcategory=""):
    normalized = canonical_category(category)
    for group, detail, department_id, _priority, _keywords in DEFAULT_CATEGORIES:
        if group == normalized and (not subcategory or detail == subcategory):
            return dict(DEFAULT_DEPARTMENTS).get(department_id, "General Municipal Services")
    mapping = {
        "Roads and Public Infrastructure": "roads",
        "Heritage and Historical Sites": "heritage",
        "Water Supply and Drainage": "water",
        "Solid Waste Management and Sanitation": "waste",
        "Gardens and Environment": "environment",
        "Electricity and Streetlights": "electrical",
        "Public Health": "health",
        "Encroachment and Building-Related Complaints": "encroachment",
        "Fire Safety and Disaster Management": "fire",
        "Public Facilities and Municipal Services": "facilities",
    }
    did = mapping.get(normalized, "general")
    return dict(DEFAULT_DEPARTMENTS).get(did, "General Municipal Services")


def department_from_db(db, category, subcategory=""):
    row = db.execute("""SELECT d.name FROM issue_categories c
      JOIN routing_rules r ON r.category_id=c.id AND r.active=1
      JOIN departments d ON d.id=r.department_id AND d.active=1
      WHERE c.category=? AND c.subcategory=? AND c.active=1
      ORDER BY r.priority DESC,c.id LIMIT 1""",
      (canonical_category(category), subcategory)).fetchone()
    if row:
        return row["name"]
    return department_for(category, subcategory)


def normalize_department(db, value):
    aliases = {
        "roads": "Roads and Engineering",
        "electrical": "Electrical / Street Lighting",
        "water & sanitation": "Water Supply",
        "water and sanitation": "Water Supply",
        "waste": "Solid Waste Management",
        "public health": "Public Health",
    }
    name = aliases.get((value or "").strip().casefold(), (value or "").strip())
    row = db.execute("SELECT name FROM departments WHERE name=? AND active=1", (name,)).fetchone()
    return row["name"] if row else None


def suggested_department(category, subcategory=""):
    return department_for(category, subcategory)


def catalog_payload():
    with db_session() as db:
        departments = [dict(row) for row in db.execute(
            "SELECT id,name FROM departments WHERE active=1 ORDER BY name")]
        rows = db.execute("""SELECT c.category,c.subcategory,c.department_id,d.name AS department,
          c.default_priority,c.keywords
          FROM issue_categories c JOIN departments d ON d.id=c.department_id
          WHERE c.active=1 ORDER BY c.category,c.subcategory""").fetchall()
        categories = {}
        for row in rows:
            group = row["category"]
            item = categories.setdefault(group, {"name": group, "subcategories": []})
            item["subcategories"].append({
                "name": row["subcategory"], "department": row["department"],
                "default_priority": row["default_priority"], "keywords": row["keywords"],
            })
        return {"departments": departments, "categories": list(categories.values()),
                "notice": "Routing and priority are demo recommendations; confirm with the competent authority."}


def classify_description(db, text):
    tokens = tokenize(text)
    best = None
    for row in db.execute("""SELECT c.category,c.subcategory,c.keywords,d.name AS department
      FROM issue_categories c JOIN routing_rules r ON r.category_id=c.id AND r.active=1
      JOIN departments d ON d.id=r.department_id AND d.active=1
      WHERE c.active=1 ORDER BY r.priority DESC"""):
        keywords = tokenize(row["keywords"])
        overlap = len(tokens & keywords)
        if overlap and (best is None or overlap > best["matched_terms"]):
            best = {"category": row["category"], "subcategory": row["subcategory"],
                    "department": row["department"], "matched_terms": overlap}
    if best:
        best["method"] = "rule-based"
        best["explanation"] = "Suggested because the description overlaps configured category keywords. Human review is required."
    else:
        best = {"category": None, "subcategory": None, "department": None,
                "method": "rule-based", "explanation": "No configured keyword match; select a category manually."}
    return best


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


def priority_for(report, corroborating_count=1, configured_priority=None):
    category_points = configured_priority or {
        "Roads and Public Infrastructure": 24, "Heritage and Historical Sites": 20,
        "Water Supply and Drainage": 22, "Solid Waste Management and Sanitation": 15,
        "Gardens and Environment": 16, "Electricity and Streetlights": 20,
        "Public Health": 21, "Encroachment and Building-Related Complaints": 16,
        "Fire Safety and Disaster Management": 25, "Public Facilities and Municipal Services": 14,
    }.get(canonical_category(report["category"]), 12)
    safety_terms = ("school", "traffic", "accident", "danger", "open manhole", "injury",
                    "electric shock", "exposed wiring", "fire", "flood", "sewage", "blocked emergency")
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
    item["category_group"] = canonical_category(item.get("category", ""))
    if not item.get("subcategory"):
        item["subcategory"] = legacy_subcategory(item.get("category", ""))
    if not item.get("suggested_department"):
        item["suggested_department"] = suggested_department(
            item.get("category", ""), item.get("subcategory", ""))
    return item


def all_reports(db):
    rows = db.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    return [pack(row) for row in rows]


def find_duplicate(db, report):
    candidates = db.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    target_tokens = tokenize(report["title"] + " " + report["description"])
    for row in candidates:
        old = dict(row)
        if canonical_category(old["category"]) != canonical_category(report["category"]):
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
    subcategory = data.get("subcategory") or legacy_subcategory(data.get("category", ""))
    route = data.get("suggested_department") or department_from_db(db, data.get("category", ""), subcategory)
    configured_priority = db.execute("""SELECT c.default_priority FROM issue_categories c
      WHERE c.category=? AND c.subcategory=? AND c.active=1""",
      (canonical_category(data.get("category", "")), subcategory)).fetchone()
    configured_priority = configured_priority["default_priority"] if configured_priority else None
    completeness, cf = score_completeness(data)
    master_id, reason = find_duplicate(db, data)
    provisional_count = 1
    if master_id:
        provisional_count = 1 + db.execute("SELECT COUNT(*) FROM reports WHERE master_id=? OR id=?", (master_id, master_id)).fetchone()[0]
    priority, pf = priority_for(data, provisional_count, configured_priority)
    created = created_at or now()
    ev = events or [event("Citizen", "Report submitted", "Synthetic demo record" if data.get("synthetic") else "")]
    if master_id:
        ev.append(event("System", "Linked to master issue", reason or "Possible duplicate"))
    db.execute('''INSERT INTO reports (id,title,category,description,area,address,before_photo,after_photo,status,
      completeness,completeness_factors,priority,priority_factors,master_id,duplicate_reason,department,crew,repair_note,
      verification,events,created_at,updated_at,subcategory,suggested_department,synthetic)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (rid,data["title"],data["category"],data["description"],data["area"],data["address"],data["before_photo"],after_photo,status,
       completeness,json.dumps(cf),priority,json.dumps(pf),master_id,reason,department,crew,repair_note,
       json.dumps(verification) if verification is not None else None,json.dumps(ev),created,now(),
       subcategory,route,1 if data.get("synthetic") else 0))
    # Recompute the master score after preserving each linked source report.
    root = master_id or rid
    group = db.execute("SELECT * FROM reports WHERE id=? OR master_id=?", (root, root)).fetchall()
    count = len(group)
    for member in group:
        priority_row = db.execute("""SELECT default_priority FROM issue_categories
          WHERE category=? AND subcategory=? AND active=1""",
          (canonical_category(member["category"]), member["subcategory"])).fetchone()
        base = priority_row["default_priority"] if priority_row else None
        p, factors = priority_for(dict(member), count, base)
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
            insert_report(db,item,status="assigned",department="Electrical / Street Lighting",crew="Crew B",events=[event("Citizen","Report submitted","Synthetic demo record"),event("Municipal","Work order assigned","Electrical / Street Lighting • Crew B")])
        elif item["id"] == "NG-DEMO-104":
            insert_report(db,item,status="repair_submitted",department="Drainage",crew="Crew A",after_photo=sample_photo("Drain • after", "#e6f1e6", "#188a66"),repair_note="Removed debris from the drain; ready for inspection.",events=[event("Citizen","Report submitted","Synthetic demo record"),event("Municipal","Work order assigned","Drainage • Crew A"),event("Field Crew","Repair submitted","Synthetic after-evidence; inspect before closure")])
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
            return json_response(self, {"ok":True,"service":"Nagrivanta demo API",
                "demo_reset_enabled":os.environ.get("NAGRIVANTA_DEMO_RESET","0")=="1"})
        if path == "/api/catalog":
            return json_response(self, catalog_payload())
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
            if not isinstance(data, dict):
                raise ValueError("Request body must be a JSON object.")
            if path == "/api/triage":
                description = data.get("description", "")
                if not isinstance(description, str) or len(description) > 2000:
                    raise ValueError("Provide a description under 2,000 characters.")
                with db_session() as db:
                    return json_response(self, {"recommendation": classify_description(db, description)})
            if path == "/api/reports":
                return self.create_report(data)
            if path == "/api/demo/reset":
                if os.environ.get("NAGRIVANTA_DEMO_RESET","0") != "1":
                    return json_response(self,{"error":"Demo reset is disabled. Enable it only for a disposable synthetic-data demo."},403)
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
        if not isinstance(data.get("category"), str) or not isinstance(data.get("subcategory", ""), str):
            raise ValueError("Choose a valid category and subcategory.")
        category = data["category"].strip()
        subcategory = data.get("subcategory", "").strip()
        if category in LEGACY_CATEGORY_GROUPS and not subcategory:
            subcategory = legacy_subcategory(category)
        group = canonical_category(category)
        if len(data["title"]) > 100 or len(data["description"]) > 1200:
            raise ValueError("Title or description is too long.")
        self.validate_photo(data["before_photo"],"Initial photo")
        with db_session() as db:
            selected = db.execute("""SELECT c.subcategory FROM issue_categories c
              WHERE c.category=? AND c.subcategory=? AND c.active=1""", (group, subcategory)).fetchone()
            if not selected:
                raise ValueError("Choose a valid category and subcategory.")
            route = department_from_db(db, group, subcategory)
            data = {k:data[k].strip() for k in ("title","description","area","address","before_photo")}
            data.update({"category":group,"subcategory":subcategory,"suggested_department":route})
            rid, master, reason = insert_report(db,data)
            row = db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
            return json_response(self,{"report":pack(row),"duplicate":({"master_id":master,"reason":reason} if master else None),
                "recommendation":{"department":route,"explanation":"Suggested from the configured category/subcategory route; an authorized municipal team must confirm."}},201)

    @staticmethod
    def validate_photo(value, label):
        match = re.fullmatch(r"data:(image/(?:jpeg|png|webp|svg\+xml));base64,([A-Za-z0-9+/]*={0,2})",
                             value or "") if isinstance(value, str) else None
        if not match or len(value) > 1_500_000:
            raise ValueError(f"{label} must be an image under about 1 MB.")
        try:
            payload = base64.b64decode(match.group(2), validate=True)
        except ValueError as exc:
            raise ValueError(f"{label} is not valid base64 image data.") from exc
        if not payload:
            raise ValueError(f"{label} is empty.")
        if match.group(1) == "image/svg+xml":
            svg = payload.decode("utf-8", "ignore").lower()
            if any(token in svg for token in ("<script", "onload=", "onerror=", "<foreignobject",
                                               "javascript:", "href=", "<!doctype", "<!entity",
                                               "<style", "url(", "xlink:")):
                raise ValueError(f"{label} contains unsupported SVG content.")
        else:
            valid_signature = (
                (match.group(1) == "image/png" and payload.startswith(b"\x89PNG\r\n\x1a\n")) or
                (match.group(1) == "image/jpeg" and payload.startswith(b"\xff\xd8\xff")) or
                (match.group(1) == "image/webp" and payload.startswith(b"RIFF") and payload[8:12] == b"WEBP")
            )
            if not valid_signature:
                raise ValueError(f"{label} does not match its declared image type.")

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
                requested_department=(data.get("department") or "").strip()
                department=normalize_department(db, requested_department)
                crew=(data.get("crew") or "").strip()
                if not department or not crew: raise ValueError("Select a configured department and crew.")
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
