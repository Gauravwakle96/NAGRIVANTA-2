#!/usr/bin/env python3
"""Nagrivanta demo API: Python stdlib + SQLite, no third-party runtime dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http.cookies import SimpleCookie
import base64, hashlib, hmac, json, math, os, re, secrets, sqlite3, struct, uuid, zlib
import getpass, sys
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(ROOT / "nagrivanta.sqlite3")))
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", str(ROOT / "private_uploads"))).resolve()
PORT = int(os.environ.get("PORT", "8000"))
SESSION_COOKIE = "nagrivanta_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
PASSWORD_ITERATIONS = 310_000
ROLES = {"citizen", "municipal_admin", "field_worker", "inspector", "system_admin"}
ADMIN_ROLES = {"municipal_admin", "system_admin"}
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
    # A small raster illustration for tests and explicitly synthetic demo records.
    def rgb(color):
        color = color.lstrip("#")
        return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

    width, height = 360, 208
    background, foreground = rgb(bg), rgb(accent)
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            if y >= 122:
                pixel = (72, 86, 96)
                if 157 <= y <= 160 and (x // 25) % 2 == 0:
                    pixel = (245, 210, 104)
            elif 42 <= x <= 117 and 45 <= y <= 119:
                pixel = (248, 250, 249)
                if x > 92 and y < 75:
                    pixel = foreground
            elif 230 <= x <= 326 and 34 <= y <= 92:
                pixel = (250, 251, 249)
            else:
                pixel = background
            row.extend(pixel)
        rows.append(b"\x00" + bytes(row))

    def chunk(name, payload):
        return (struct.pack(">I", len(payload)) + name + payload +
                struct.pack(">I", zlib.crc32(name + payload) & 0xffffffff))

    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
           chunk(b"IDAT", zlib.compress(b"".join(rows), 6)) +
           chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


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
        db.execute('''CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
          display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('citizen','municipal_admin','field_worker','inspector','system_admin')),
          active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )''')
        # Additive migrations preserve existing report IDs and workflow history.
        columns = {row["name"] for row in db.execute("PRAGMA table_info(reports)")}
        legacy_columns = (
            ("title", "TEXT NOT NULL DEFAULT ''"),
            ("category", "TEXT NOT NULL DEFAULT ''"),
            ("description", "TEXT NOT NULL DEFAULT ''"),
            ("area", "TEXT NOT NULL DEFAULT ''"),
            ("address", "TEXT NOT NULL DEFAULT ''"),
            ("before_photo", "TEXT NOT NULL DEFAULT ''"),
            ("after_photo", "TEXT"),
            ("status", "TEXT NOT NULL DEFAULT 'submitted'"),
            ("completeness", "INTEGER NOT NULL DEFAULT 0"),
            ("completeness_factors", "TEXT NOT NULL DEFAULT '[]'"),
            ("priority", "INTEGER NOT NULL DEFAULT 0"),
            ("priority_factors", "TEXT NOT NULL DEFAULT '[]'"),
            ("master_id", "TEXT"),
            ("duplicate_reason", "TEXT"),
            ("department", "TEXT"),
            ("crew", "TEXT"),
            ("repair_note", "TEXT"),
            ("verification", "TEXT"),
            ("events", "TEXT NOT NULL DEFAULT '[]'"),
            ("created_at", "TEXT NOT NULL DEFAULT ''"),
            ("updated_at", "TEXT NOT NULL DEFAULT ''"),
        )
        for name,definition in legacy_columns:
            if name not in columns:
                db.execute(f"ALTER TABLE reports ADD COLUMN {name} {definition}")
                columns.add(name)
        for name, definition in (
            ("subcategory", "TEXT NOT NULL DEFAULT ''"),
            ("suggested_department", "TEXT"),
            ("synthetic", "INTEGER NOT NULL DEFAULT 0"),
            ("owner_id", "TEXT REFERENCES users(id)"),
            ("assigned_to", "TEXT REFERENCES users(id)"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),
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
          escalation_hours INTEGER NOT NULL DEFAULT 168,
          active INTEGER NOT NULL DEFAULT 1, UNIQUE(category, subcategory)
        )''')
        category_columns = {row["name"] for row in db.execute("PRAGMA table_info(issue_categories)")}
        if "escalation_hours" not in category_columns:
            db.execute("ALTER TABLE issue_categories ADD COLUMN escalation_hours INTEGER NOT NULL DEFAULT 168")
        db.execute('''CREATE TABLE IF NOT EXISTS routing_rules (
          id TEXT PRIMARY KEY, category_id TEXT NOT NULL REFERENCES issue_categories(id),
          department_id TEXT NOT NULL REFERENCES departments(id), priority INTEGER NOT NULL DEFAULT 100,
          active INTEGER NOT NULL DEFAULT 1
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          csrf_token TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS login_throttles (
          email TEXT PRIMARY KEY, attempts INTEGER NOT NULL DEFAULT 0,
          window_started_at TEXT NOT NULL, locked_until TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS evidence_files (
          id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
          kind TEXT NOT NULL CHECK(kind IN ('before','after')),
          uploaded_by TEXT REFERENCES users(id), storage_name TEXT NOT NULL UNIQUE,
          media_type TEXT NOT NULL, byte_size INTEGER NOT NULL, sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS repair_submissions (
          id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
          worker_id TEXT NOT NULL REFERENCES users(id), repair_note TEXT NOT NULL,
          evidence_id TEXT NOT NULL REFERENCES evidence_files(id), created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS inspections (
          id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
          inspector_id TEXT NOT NULL REFERENCES users(id), approved INTEGER NOT NULL,
          checks TEXT NOT NULL, notes TEXT NOT NULL, created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS notifications (
          id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          report_id TEXT REFERENCES reports(id) ON DELETE CASCADE,
          kind TEXT NOT NULL, title TEXT NOT NULL, message TEXT NOT NULL,
          created_at TEXT NOT NULL, read_at TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS audit_events (
          id TEXT PRIMARY KEY, actor_id TEXT REFERENCES users(id),
          action TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT,
          details TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS schema_migrations (
          version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL
        )''')
        seed_catalog(db)
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_category_subcategory ON reports(category, subcategory)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_department ON reports(department)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_owner ON reports(owner_id, created_at)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reports_assignee ON reports(assigned_to, status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_evidence_report ON evidence_files(report_id, kind)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read_at, created_at)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_inspections_report ON inspections(report_id, created_at)')
        # Backfill new fields without changing original report text or IDs.
        for row in db.execute("SELECT id, category, subcategory, suggested_department FROM reports").fetchall():
            group = canonical_category(row["category"])
            detail = row["subcategory"] or legacy_subcategory(row["category"])
            suggested = row["suggested_department"] or suggested_department(group, detail)
            db.execute("UPDATE reports SET subcategory=?, suggested_department=? WHERE id=?",
                       (detail, suggested, row["id"]))
        if db.execute('SELECT COUNT(*) FROM reports').fetchone()[0] == 0:
            seed_demo(db)
        db.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES (?,?)",(2,now()))
    # Older builds kept data URLs inside the reports table. Move those bytes
    # into private files without changing report IDs, status, or event history.
    migrate_legacy_evidence()
    bootstrap_admin()


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
            try:
                item[key] = json.loads(item[key])
            except (TypeError, json.JSONDecodeError):
                item[key] = None
    for field, output in (("before_photo", "before_evidence_id"), ("after_photo", "after_evidence_id")):
        reference = item.pop(field, None)
        item[output] = reference.split(":", 1)[1] if isinstance(reference, str) and reference.startswith("evidence:") else None
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
    rid = data.get("id") or "NG-" + uuid.uuid4().hex[:12].upper()
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
      verification,events,created_at,updated_at,subcategory,suggested_department,synthetic,owner_id,assigned_to,latitude,longitude)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (rid,data["title"],data["category"],data["description"],data["area"],data["address"],data["before_photo"],after_photo,status,
       completeness,json.dumps(cf),priority,json.dumps(pf),master_id,reason,department,crew,repair_note,
       json.dumps(verification) if verification is not None else None,json.dumps(ev),created,now(),
       subcategory,route,1 if data.get("synthetic") else 0,data.get("owner_id"),data.get("assigned_to"),
       data.get("latitude"),data.get("longitude")))
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


def json_response(handler, data, status=200, headers=None):
    body = json.dumps(data, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.security_headers()
    for name, value in (headers or {}).items():
        handler.send_header(name, value)
    handler.end_headers()
    handler.wfile.write(body)


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(rounds))
        return hmac.compare_digest(digest, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


def validate_password(value):
    if not isinstance(value, str) or len(value) < 12 or len(value) > 256:
        raise ValueError("Password must be between 12 and 256 characters.")
    return value


def normalize_email(value):
    if not isinstance(value, str):
        raise ValueError("Enter a valid email address.")
    email = value.strip().casefold()
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Enter a valid email address.")
    return email


def create_user(db, email, display_name, password, role="citizen"):
    email = normalize_email(email)
    password = validate_password(password)
    if role not in ROLES:
        raise ValueError("Choose a supported account role.")
    if not isinstance(display_name, str) or not 2 <= len(display_name.strip()) <= 80:
        raise ValueError("Name must be between 2 and 80 characters.")
    user_id = uuid.uuid4().hex
    timestamp = now()
    try:
        db.execute("""INSERT INTO users(id,email,display_name,password_hash,role,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?)""",
          (user_id,email,display_name.strip(),hash_password(password),role,timestamp,timestamp))
    except sqlite3.IntegrityError as exc:
        if "email" in str(exc).lower():
            raise ValueError("An account with that email already exists.") from exc
        raise
    return db.execute("SELECT id,email,display_name,role,active,created_at FROM users WHERE id=?",
                      (user_id,)).fetchone()


def make_session(db, user_id):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    timestamp = now()
    expires = (datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)).isoformat(timespec="seconds")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.execute("DELETE FROM sessions WHERE expires_at < ?", (timestamp,))
    db.execute("INSERT INTO sessions(token_hash,user_id,csrf_token,created_at,expires_at) VALUES (?,?,?,?,?)",
               (token_hash,user_id,csrf,timestamp,expires))
    return token, csrf, expires


def user_payload(row):
    return {"id": row["id"], "email": row["email"], "display_name": row["display_name"],
            "role": row["role"], "active": bool(row["active"]), "created_at": row["created_at"]}


def record_audit(db, actor_id, action, entity_type, entity_id=None, details=None):
    db.execute("""INSERT INTO audit_events(id,actor_id,action,entity_type,entity_id,details,created_at)
      VALUES (?,?,?,?,?,?,?)""",
      (uuid.uuid4().hex,actor_id,action,entity_type,entity_id,
       json.dumps(details or {}, ensure_ascii=False),now()))


def notify_user(db, user_id, report_id, kind, title, message):
    if user_id:
        db.execute("""INSERT INTO notifications(id,user_id,report_id,kind,title,message,created_at)
          VALUES (?,?,?,?,?,?,?)""",
          (uuid.uuid4().hex,user_id,report_id,kind,title[:120],message[:500],now()))


def notify_roles(db, roles, report_id, kind, title, message):
    placeholders = ",".join("?" for _ in roles)
    if not placeholders:
        return
    rows = db.execute(f"SELECT id FROM users WHERE active=1 AND role IN ({placeholders})", tuple(roles)).fetchall()
    for row in rows:
        notify_user(db,row["id"],report_id,kind,title,message)


def save_evidence_bytes(db, report_id, kind, uploaded_by, payload, media_type, *, legacy=False):
    if kind not in {"before","after"} or not payload:
        raise ValueError("Evidence is empty or has an unsupported purpose.")
    if len(payload) > (1_200_000 if legacy else 1_000_000):
        raise ValueError("Evidence image must be 1 MB or smaller.")
    extensions = {"image/png":"png","image/jpeg":"jpg","image/webp":"webp"}
    if media_type not in extensions:
        media_type = "application/octet-stream"
        extension = "bin"
    else:
        extension = extensions[media_type]
    if PUBLIC.resolve() == UPLOADS_DIR or PUBLIC.resolve() in UPLOADS_DIR.parents:
        raise RuntimeError("Evidence storage must not be inside the public static directory.")
    UPLOADS_DIR.mkdir(parents=True,exist_ok=True)
    file_id = uuid.uuid4().hex
    storage_name = f"{uuid.uuid4().hex}.{extension}"
    destination = UPLOADS_DIR / storage_name
    with destination.open("xb") as file:
        file.write(payload)
        file.flush()
        os.fsync(file.fileno())
    db.execute("""INSERT INTO evidence_files
      (id,report_id,kind,uploaded_by,storage_name,media_type,byte_size,sha256,created_at)
      VALUES (?,?,?,?,?,?,?,?,?)""",
      (file_id,report_id,kind,uploaded_by,storage_name,media_type,len(payload),
       hashlib.sha256(payload).hexdigest(),now()))
    return file_id


def parse_image_data_url(value, label):
    if not isinstance(value, str) or len(value) > 1_500_000:
        raise ValueError(f"{label} must be a PNG, JPEG or WebP image no larger than 1 MB.")
    match = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/]*={0,2})",value)
    if not match:
        if isinstance(value,str) and value.startswith("data:image/svg+xml"):
            raise ValueError(f"{label} uses unsupported SVG; upload a PNG, JPEG or WebP image.")
        raise ValueError(f"{label} must be a PNG, JPEG or WebP image no larger than 1 MB.")
    try:
        payload = base64.b64decode(match.group(2),validate=True)
    except (ValueError,base64.binascii.Error) as exc:
        raise ValueError(f"{label} is not valid base64 image data.") from exc
    media_type = match.group(1)
    signatures = {
        "image/png": payload.startswith(b"\x89PNG\r\n\x1a\n") and payload[12:16] == b"IHDR",
        "image/jpeg": payload.startswith(b"\xff\xd8\xff"),
        "image/webp": payload.startswith(b"RIFF") and payload[8:12] == b"WEBP",
    }
    if not payload or len(payload) > 1_000_000 or not signatures[media_type]:
        raise ValueError(f"{label} does not match a supported image file or exceeds 1 MB.")
    return payload,media_type


def store_image_data_url(db, report_id, kind, uploaded_by, value, label):
    payload,media_type = parse_image_data_url(value,label)
    return save_evidence_bytes(db,report_id,kind,uploaded_by,payload,media_type)


def migrate_legacy_evidence():
    with db_session() as db:
        rows = db.execute("SELECT id,before_photo,after_photo FROM reports").fetchall()
        for row in rows:
            for kind,column in (("before","before_photo"),("after","after_photo")):
                value = row[column]
                if not isinstance(value,str) or not value.startswith("data:"):
                    continue
                exists = db.execute("SELECT 1 FROM evidence_files WHERE report_id=? AND kind=? LIMIT 1",
                                    (row["id"],kind)).fetchone()
                if exists:
                    continue
                match = re.fullmatch(r"data:[^;,]+;base64,([A-Za-z0-9+/]*={0,2})",value)
                if not match:
                    continue
                try:
                    payload = base64.b64decode(match.group(1),validate=True)
                except (ValueError,base64.binascii.Error):
                    continue
                if not payload or len(payload)>1_200_000:
                    continue
                media_type = "application/octet-stream"
                if payload.startswith(b"\x89PNG\r\n\x1a\n") and payload[12:16]==b"IHDR":
                    media_type="image/png"
                elif payload.startswith(b"\xff\xd8\xff"):
                    media_type="image/jpeg"
                elif payload.startswith(b"RIFF") and payload[8:12]==b"WEBP":
                    media_type="image/webp"
                file_id = save_evidence_bytes(db,row["id"],kind,None,payload,media_type,legacy=True)
                db.execute(f"UPDATE reports SET {column}=? WHERE id=?",
                           (f"evidence:{file_id}",row["id"]))


def can_view_report(db,user,row):
    if user["role"] in ADMIN_ROLES:
        return True
    if user["role"] == "citizen":
        return row["owner_id"] == user["id"]
    if user["role"] == "field_worker":
        return row["assigned_to"] == user["id"]
    if user["role"] == "inspector":
        return row["status"] == "repair_submitted" or db.execute(
            "SELECT 1 FROM inspections WHERE report_id=? AND inspector_id=? LIMIT 1",
            (row["id"],user["id"])).fetchone() is not None
    return False


def report_for_user(row,user):
    item = pack(row)
    if user["role"] == "citizen":
        for key in ("completeness_factors","priority_factors","master_id","duplicate_reason","assigned_to"):
            item.pop(key,None)
    else:
        item.pop("owner_id",None)
    if user["role"] not in ADMIN_ROLES:
        item.pop("assigned_to",None)
    return item


def report_history(db,report_id):
    repairs = [dict(row) for row in db.execute("""SELECT s.id,s.repair_note,s.evidence_id,s.created_at,
      u.display_name AS worker FROM repair_submissions s JOIN users u ON u.id=s.worker_id
      WHERE s.report_id=? ORDER BY s.created_at""",(report_id,))]
    inspections = []
    for row in db.execute("""SELECT i.id,i.approved,i.checks,i.notes,i.created_at,u.display_name AS inspector
      FROM inspections i JOIN users u ON u.id=i.inspector_id
      WHERE i.report_id=? ORDER BY i.created_at""",(report_id,)):
        item = dict(row)
        item["approved"] = bool(item["approved"])
        item["checks"] = json.loads(item["checks"])
        inspections.append(item)
    return {"repair_history":repairs,"inspection_history":inspections}


def cookie_is_secure(handler):
    return bool(os.environ.get("RENDER")) or os.environ.get("NAGRIVANTA_COOKIE_SECURE") == "1" or \
           handler.headers.get("X-Forwarded-Proto","").split(",")[0].strip().lower() == "https"


def parse_query(path):
    return {key:values[0] for key,values in parse_qs(urlparse(path).query,keep_blank_values=False).items() if values}


def validate_coordinates(latitude,longitude):
    if latitude in (None,"") and longitude in (None,""):
        return None,None
    try:
        lat,lng = float(latitude),float(longitude)
    except (TypeError,ValueError) as exc:
        raise ValueError("Latitude and longitude must both be valid numbers.") from exc
    if not math.isfinite(lat) or not math.isfinite(lng) or not -90<=lat<=90 or not -180<=lng<=180:
        raise ValueError("Coordinates are outside valid latitude and longitude ranges.")
    return lat,lng


def analytics_payload(db):
    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    counts = {row["status"]:row["n"] for row in db.execute(
      "SELECT status,COUNT(*) AS n FROM reports GROUP BY status")}
    resolved = counts.get("verified",0)
    durations = []
    for row in db.execute("SELECT created_at,updated_at FROM reports WHERE status='verified'"):
        try:
            start = datetime.fromisoformat(row["created_at"])
            end = datetime.fromisoformat(row["updated_at"])
            durations.append(max(0,(end-start).total_seconds()/3600))
        except (ValueError,TypeError):
            continue
    total_inspections = db.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]
    rejected = db.execute("SELECT COUNT(*) FROM inspections WHERE approved=0").fetchone()[0]
    departments = [dict(row) for row in db.execute("""SELECT
      COALESCE(NULLIF(department,''),NULLIF(suggested_department,''),'Unassigned') AS department,
      COUNT(*) AS complaint_count FROM reports WHERE status!='verified'
      GROUP BY department ORDER BY complaint_count DESC,department""")]
    overdue = 0
    current = datetime.now(timezone.utc)
    for row in db.execute("""SELECT r.created_at,c.escalation_hours FROM reports r
      LEFT JOIN issue_categories c ON c.category=r.category AND c.subcategory=r.subcategory
      WHERE r.status!='verified'"""):
        try:
            created = datetime.fromisoformat(row["created_at"])
            if (current-created).total_seconds() > (row["escalation_hours"] or 168)*3600:
                overdue += 1
        except (ValueError,TypeError):
            pass
    return {
      "total":total,"pending":total-resolved,"awaiting_assignment":counts.get("submitted",0),
      "awaiting_inspection":counts.get("repair_submitted",0),
      "high_priority":db.execute("SELECT COUNT(*) FROM reports WHERE priority>=70 AND status!='verified'").fetchone()[0],
      "verified_resolutions":resolved,"resolution_rate":round(resolved*100/total,1) if total else None,
      "average_resolution_hours":round(sum(durations)/len(durations),1) if durations else None,
      "department_workload":departments,"overdue":overdue,
      "inspection_count":total_inspections,
      "inspection_approval_rate":round((total_inspections-rejected)*100/total_inspections,1) if total_inspections else None,
      "rework_rate":round(rejected*100/total_inspections,1) if total_inspections else None,
      "definitions":{"resolution_rate":"verified reports divided by all reports",
        "average_resolution_hours":"mean created-to-verified elapsed time for verified reports",
        "overdue":"open reports older than their category's configured escalation threshold (default 168 hours)",
        "priority":"illustrative rule-based score of 70 or higher; not an official service level"}
    }


def bootstrap_admin():
    with db_session() as db:
        # Bootstrap is a one-time recovery path, not a way to mint additional
        # system administrators or rotate credentials on each Render restart.
        if db.execute("SELECT 1 FROM users WHERE role='system_admin' LIMIT 1").fetchone():
            return

        email = os.environ.get("NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL","").strip()
        password = os.environ.get("NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD")
        if not email:
            return
        if not password:
            raise RuntimeError("NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD is required when bootstrap email is set.")

        try:
            normalized = normalize_email(email)
            if db.execute("SELECT 1 FROM users WHERE email=? COLLATE NOCASE",(normalized,)).fetchone():
                raise RuntimeError(
                    "The bootstrap email already belongs to an account. Choose a new unused email; "
                    "bootstrap never promotes existing accounts."
                )
            name = os.environ.get("NAGRIVANTA_BOOTSTRAP_ADMIN_NAME","System Administrator")
            create_user(db,normalized,name,password,"system_admin")
        except ValueError as exc:
            raise RuntimeError(f"System administrator bootstrap failed: {exc}") from exc

        row = db.execute("SELECT id FROM users WHERE email=?",(normalized,)).fetchone()
        record_audit(db,row["id"],"bootstrap_admin_created","user",row["id"])


class Handler(BaseHTTPRequestHandler):
    server_version = "Nagrivanta/2.0"
    sys_version = ""

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def security_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Referrer-Policy","strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy","camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy",
          "default-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
          "style-src 'self' 'unsafe-inline' https://unpkg.com; script-src 'self' https://unpkg.com; "
          "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

    def body(self):
        try:
            length = int(self.headers.get("Content-Length","0"))
        except ValueError as exc:
            raise ValueError("Invalid request length.") from exc
        if length < 0 or length > MAX_BODY:
            raise ValueError("Request is too large (3 MB limit). Resize the image and try again.")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw)
        except (json.JSONDecodeError,UnicodeDecodeError) as exc:
            raise ValueError("Request body must be valid JSON.") from exc

    def origin_allowed(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed = urlparse(origin)
        host = self.headers.get("Host","").lower()
        return parsed.scheme in {"http","https"} and parsed.netloc.lower() == host

    def cookie_headers(self, token=None, clear=False):
        secure = "; Secure" if cookie_is_secure(self) else ""
        if clear:
            value = f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax{secure}"
        else:
            value = f"{SESSION_COOKIE}={token}; Path=/; Max-Age={SESSION_TTL_SECONDS}; HttpOnly; SameSite=Lax{secure}"
        return {"Set-Cookie":value}

    def current_user(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie",""))
        except Exception:
            return None
        morsel = cookie.get(SESSION_COOKIE)
        if not morsel or not morsel.value:
            return None
        token_hash = hashlib.sha256(morsel.value.encode()).hexdigest()
        with db_session() as db:
            row = db.execute("""SELECT s.token_hash,s.csrf_token,s.expires_at,
              u.id,u.email,u.display_name,u.role,u.active,u.created_at
              FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?""",(token_hash,)).fetchone()
            if not row or not row["active"] or row["expires_at"] <= now():
                db.execute("DELETE FROM sessions WHERE token_hash=?",(token_hash,))
                return None
            return dict(row)

    def require_user(self, roles=None):
        user = self.current_user()
        if not user:
            json_response(self,{"error":"Sign in to continue."},401)
            return None
        if roles and user["role"] not in roles:
            json_response(self,{"error":"You do not have permission to perform this action."},403)
            return None
        return user

    def require_csrf(self,user):
        if not user or not self.origin_allowed():
            json_response(self,{"error":"Request origin was not accepted."},403)
            return False
        supplied = self.headers.get("X-CSRF-Token","")
        if not supplied or not secrets.compare_digest(supplied,user["csrf_token"]):
            json_response(self,{"error":"Session security check failed. Refresh and try again."},403)
            return False
        return True

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return json_response(self,{"ok":True,"service":"Nagrivanta","storage":"SQLite + private filesystem"})
        if path == "/api/catalog":
            return json_response(self,catalog_payload())
        if path == "/api/auth/me":
            user = self.current_user()
            if not user:
                return json_response(self,{"authenticated":False})
            return json_response(self,{"authenticated":True,"user":user_payload(user),
                                       "csrf_token":user["csrf_token"],"expires_at":user["expires_at"]})
        if path == "/api/reports":
            user = self.require_user()
            if not user:
                return
            return self.list_reports(user)
        if path.startswith("/api/reports/"):
            user = self.require_user()
            if not user:
                return
            rid = path.rsplit("/",1)[-1]
            with db_session() as db:
                row = db.execute("SELECT * FROM reports WHERE id=?",(rid,)).fetchone()
                if not row or not can_view_report(db,user,row):
                    return json_response(self,{"error":"Issue not found."},404)
                report = report_for_user(row,user)
                report.update(report_history(db,rid))
                return json_response(self,{"report":report})
        if path.startswith("/api/evidence/"):
            user = self.require_user()
            if not user:
                return
            return self.serve_evidence(user,path.rsplit("/",1)[-1])
        if path == "/api/notifications":
            user = self.require_user()
            if not user:
                return
            with db_session() as db:
                rows = db.execute("""SELECT id,report_id,kind,title,message,created_at,read_at
                  FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 100""",(user["id"],)).fetchall()
                unread = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND read_at IS NULL",
                                    (user["id"],)).fetchone()[0]
                return json_response(self,{"unread_count":unread,"notifications":[dict(row) for row in rows]})
        if path == "/api/workers":
            user = self.require_user(ADMIN_ROLES)
            if not user:
                return
            with db_session() as db:
                rows = db.execute("""SELECT id,display_name,email FROM users
                  WHERE role='field_worker' AND active=1 ORDER BY display_name""").fetchall()
                return json_response(self,{"workers":[dict(row) for row in rows]})
        if path == "/api/analytics":
            user = self.require_user(ADMIN_ROLES)
            if not user:
                return
            with db_session() as db:
                return json_response(self,{"analytics":analytics_payload(db)})
        if path == "/api/admin/users":
            user = self.require_user({"system_admin"})
            if not user:
                return
            with db_session() as db:
                rows = db.execute("""SELECT id,email,display_name,role,active,created_at
                  FROM users ORDER BY created_at DESC LIMIT 500""").fetchall()
                return json_response(self,{"users":[user_payload(row) for row in rows]})
        if path == "/api/admin/config":
            user = self.require_user({"system_admin"})
            if not user:
                return
            with db_session() as db:
                departments = [dict(row) for row in db.execute(
                  "SELECT id,name,active FROM departments ORDER BY name")]
                categories = [dict(row) for row in db.execute("""SELECT c.id,c.category,c.subcategory,
                  c.department_id,d.name AS department,c.default_priority,c.keywords,c.escalation_hours,c.active
                  FROM issue_categories c JOIN departments d ON d.id=c.department_id
                  ORDER BY c.category,c.subcategory""")]
                return json_response(self,{"departments":departments,"categories":categories})
        if path == "/api/admin/audit":
            user = self.require_user({"system_admin"})
            if not user:
                return
            with db_session() as db:
                rows = db.execute("""SELECT a.id,a.action,a.entity_type,a.entity_id,a.details,a.created_at,
                  u.display_name AS actor FROM audit_events a LEFT JOIN users u ON u.id=a.actor_id
                  ORDER BY a.created_at DESC LIMIT 200""").fetchall()
                result = []
                for row in rows:
                    item = dict(row)
                    item["details"] = json.loads(item["details"] or "{}")
                    result.append(item)
                return json_response(self,{"events":result})
        if path == "/api/admin/notifications":
            user = self.require_user({"system_admin"})
            if not user:
                return
            with db_session() as db:
                rows = db.execute("""SELECT kind,COUNT(*) AS total,
                  SUM(CASE WHEN read_at IS NULL THEN 1 ELSE 0 END) AS unread,
                  MAX(created_at) AS latest FROM notifications GROUP BY kind ORDER BY total DESC""").fetchall()
                return json_response(self,{"notification_metrics":[dict(row) for row in rows]})
        return self.static_file(path)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path in {"/api/auth/register","/api/auth/login"}:
                if not self.origin_allowed():
                    return json_response(self,{"error":"Request origin was not accepted."},403)
                data = self.body()
                if not isinstance(data,dict):
                    raise ValueError("Request body must be a JSON object.")
                return self.auth_request(path,data)
            if path == "/api/triage":
                data = self.body()
                if not isinstance(data,dict):
                    raise ValueError("Request body must be a JSON object.")
                description = data.get("description","")
                if not isinstance(description,str) or len(description)>2000:
                    raise ValueError("Provide a description under 2,000 characters.")
                with db_session() as db:
                    return json_response(self,{"recommendation":classify_description(db,description)})

            user = self.require_user()
            if not user:
                return
            if not self.require_csrf(user):
                return
            data = self.body()
            if not isinstance(data,dict):
                raise ValueError("Request body must be a JSON object.")
            if path == "/api/auth/password":
                current = data.get("current_password")
                new = validate_password(data.get("new_password"))
                with db_session() as db:
                    account = db.execute("SELECT password_hash FROM users WHERE id=? AND active=1",
                                         (user["id"],)).fetchone()
                    if not account or not isinstance(current,str) or not verify_password(current,account["password_hash"]):
                        return json_response(self,{"error":"Current password is incorrect."},400)
                    db.execute("UPDATE users SET password_hash=?,updated_at=? WHERE id=?",
                               (hash_password(new),now(),user["id"]))
                    db.execute("DELETE FROM sessions WHERE user_id=?",(user["id"],))
                    token,csrf,expires = make_session(db,user["id"])
                    record_audit(db,user["id"],"password_changed","user",user["id"])
                    updated = db.execute("SELECT id,email,display_name,role,active,created_at FROM users WHERE id=?",
                                          (user["id"],)).fetchone()
                return json_response(self,{"user":user_payload(updated),"csrf_token":csrf,"expires_at":expires},
                                     headers=self.cookie_headers(token))
            if path == "/api/auth/logout":
                cookie = SimpleCookie(self.headers.get("Cookie",""))
                morsel = cookie.get(SESSION_COOKIE)
                if morsel:
                    token_hash = hashlib.sha256(morsel.value.encode()).hexdigest()
                    with db_session() as db:
                        db.execute("DELETE FROM sessions WHERE token_hash=?",(token_hash,))
                return json_response(self,{"ok":True},headers=self.cookie_headers(clear=True))
            if path == "/api/reports":
                if user["role"] != "citizen":
                    return json_response(self,{"error":"Only citizen accounts can submit public complaints."},403)
                return self.create_report(user,data)
            if path.startswith("/api/reports/"):
                rid = path.split("/")[3]
                return self.transition(user,rid,data)
            if path == "/api/demo/reset":
                if user["role"] != "system_admin":
                    return json_response(self,{"error":"System administrator access is required."},403)
                if os.environ.get("NAGRIVANTA_DEMO_RESET","0") != "1":
                    return json_response(self,{"error":"Demo reset is disabled. Enable only for disposable synthetic data."},403)
                evidence_paths = []
                with db_session() as db:
                    real_records = db.execute("SELECT COUNT(*) FROM reports WHERE synthetic=0").fetchone()[0]
                    if real_records:
                        return json_response(self,{"error":"Reset refused because non-synthetic complaints exist."},403)
                    evidence_paths = [UPLOADS_DIR / row["storage_name"] for row in
                                      db.execute("SELECT storage_name FROM evidence_files").fetchall()]
                    db.execute("UPDATE reports SET master_id=NULL")
                    db.execute("DELETE FROM reports")
                    seed_demo(db)
                    record_audit(db,user["id"],"demo_reset","system")
                for evidence_path in evidence_paths:
                    try:
                        evidence_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                migrate_legacy_evidence()
                with db_session() as db:
                    return json_response(self,{"ok":True,"reports":all_reports(db)})
            if path.startswith("/api/notifications/"):
                notification_id = path.rsplit("/",1)[-1]
                with db_session() as db:
                    result = db.execute("""UPDATE notifications SET read_at=?
                      WHERE id=? AND user_id=?""",(now(),notification_id,user["id"]))
                    if result.rowcount == 0:
                        return json_response(self,{"error":"Notification not found."},404)
                    return json_response(self,{"ok":True})
            if path == "/api/admin/users":
                if user["role"] != "system_admin":
                    return json_response(self,{"error":"System administrator access is required."},403)
                return self.admin_create_user(user,data)
            if path.startswith("/api/admin/users/"):
                if user["role"] != "system_admin":
                    return json_response(self,{"error":"System administrator access is required."},403)
                return self.admin_update_user(user,path.rsplit("/",1)[-1],data)
            if path == "/api/admin/config/categories":
                if user["role"] != "system_admin":
                    return json_response(self,{"error":"System administrator access is required."},403)
                return self.admin_save_category(user,data)
            if path == "/api/admin/config/departments":
                if user["role"] != "system_admin":
                    return json_response(self,{"error":"System administrator access is required."},403)
                return self.admin_save_department(user,data)
            return json_response(self,{"error":"Endpoint not found."},404)
        except ValueError as exc:
            return json_response(self,{"error":str(exc)},400)
        except Exception:
            print("Request error: unexpected application exception")
            return json_response(self,{"error":"The request could not be completed. Please retry."},500)

    def auth_request(self,path,data):
        if path.endswith("/register"):
            if data.get("role") not in (None,"citizen"):
                raise ValueError("Public registration can create citizen accounts only.")
            with db_session() as db:
                user = create_user(db,data.get("email"),data.get("display_name"),data.get("password"),"citizen")
                token,csrf,expires = make_session(db,user["id"])
                record_audit(db,user["id"],"account_registered","user",user["id"])
            return json_response(self,{"user":user_payload(user),"csrf_token":csrf,"expires_at":expires},
                                 201,self.cookie_headers(token))
        email = normalize_email(data.get("email"))
        password = data.get("password")
        if not isinstance(password,str) or len(password)>256:
            password = ""
        with db_session() as db:
            throttle = db.execute("SELECT attempts,window_started_at,locked_until FROM login_throttles WHERE email=?",
                                  (email,)).fetchone()
            stamp = now()
            if throttle and throttle["locked_until"] and throttle["locked_until"] > stamp:
                return json_response(self,{"error":"Too many sign-in attempts. Please wait and try again."},429)
            if throttle and throttle["window_started_at"] < (datetime.now(timezone.utc)-timedelta(minutes=15)).isoformat(timespec="seconds"):
                db.execute("DELETE FROM login_throttles WHERE email=?",(email,))
                throttle = None
            row = db.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE",(email,)).fetchone()
            # The dummy hash prevents user enumeration through a noticeably cheaper failed login.
            valid = verify_password(password,row["password_hash"]) if row else verify_password(
                password,"pbkdf2_sha256$310000$MDEyMzQ1Njc4OWFiY2RlZg==$AAAAAAAAAAAAAAAAAAAAAAAAAAA=")
            if not row or not row["active"] or not valid:
                attempts = (throttle["attempts"] if throttle else 0) + 1
                locked_until = (datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat(timespec="seconds") if attempts >= 10 else None
                start = throttle["window_started_at"] if throttle else stamp
                db.execute("""INSERT INTO login_throttles(email,attempts,window_started_at,locked_until)
                  VALUES (?,?,?,?) ON CONFLICT(email) DO UPDATE SET attempts=excluded.attempts,
                  window_started_at=excluded.window_started_at,locked_until=excluded.locked_until""",
                  (email,attempts,start,locked_until))
                if attempts>=10:
                    return json_response(self,{"error":"Too many sign-in attempts. Please wait and try again."},429)
                return json_response(self,{"error":"Email or password is incorrect."},401)
            db.execute("DELETE FROM login_throttles WHERE email=?",(email,))
            token,csrf,expires = make_session(db,row["id"])
            record_audit(db,row["id"],"login","session")
            user = user_payload(row)
        return json_response(self,{"user":user,"csrf_token":csrf,"expires_at":expires},
                             headers=self.cookie_headers(token))

    def list_reports(self,user):
        params = []
        clauses = []
        role = user["role"]
        if role == "citizen":
            clauses.append("owner_id=?")
            params.append(user["id"])
        elif role == "field_worker":
            clauses.append("assigned_to=?")
            params.append(user["id"])
        elif role == "inspector":
            clauses.append("""(status='repair_submitted' OR EXISTS
              (SELECT 1 FROM inspections i WHERE i.report_id=reports.id AND i.inspector_id=?))""")
            params.append(user["id"])
        query = parse_query(self.path)
        if query.get("status"):
            clauses.append("status=?")
            params.append(query["status"][:40])
        if query.get("category"):
            clauses.append("category=?")
            params.append(query["category"][:120])
        if query.get("q"):
            clauses.append("(title LIKE ? OR description LIKE ? OR area LIKE ? OR address LIKE ?)")
            needle = "%" + query["q"][:100] + "%"
            params.extend([needle]*4)
        if query.get("heritage") == "1":
            clauses.append("category='Heritage and Historical Sites'")
        limit = 50
        try:
            limit = min(100,max(1,int(query.get("limit","50"))))
        except ValueError:
            pass
        sql = "SELECT * FROM reports"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with db_session() as db:
            rows = db.execute(sql,params).fetchall()
            reports = []
            for row in rows:
                item = report_for_user(row,user)
                item.update(report_history(db,row["id"]))
                reports.append(item)
            return json_response(self,{"reports":reports})

    def serve_evidence(self,user,evidence_id):
        with db_session() as db:
            evidence = db.execute("SELECT * FROM evidence_files WHERE id=?",(evidence_id,)).fetchone()
            if not evidence:
                return json_response(self,{"error":"Evidence not found."},404)
            report = db.execute("SELECT * FROM reports WHERE id=?",(evidence["report_id"],)).fetchone()
            if not report or not can_view_report(db,user,report):
                return json_response(self,{"error":"Evidence not found."},404)
            path = (UPLOADS_DIR / evidence["storage_name"]).resolve()
            if UPLOADS_DIR not in path.parents or not path.is_file():
                return json_response(self,{"error":"Evidence is unavailable."},404)
            content_type = evidence["media_type"]
            disposition = "inline" if content_type.startswith("image/") else "attachment"
            body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","private, no-store")
        self.send_header("Content-Disposition",f'{disposition}; filename="nagrivanta-evidence-{evidence_id[:8]}"')
        self.security_headers()
        self.end_headers()
        self.wfile.write(body)

    def create_report(self,user,data):
        string_limits = {"title":100,"description":1200,"area":100,"address":240}
        cleaned = {}
        for key,maximum in string_limits.items():
            value = data.get(key)
            if not isinstance(value,str) or not value.strip() or len(value.strip())>maximum:
                raise ValueError(f"{key.replace('_',' ').capitalize()} is required and must be under {maximum} characters.")
            cleaned[key] = value.strip()
        if not isinstance(data.get("category"),str) or not isinstance(data.get("subcategory",""),str):
            raise ValueError("Choose a valid category and subcategory.")
        category = data["category"].strip()
        subcategory = data.get("subcategory","").strip()
        group = canonical_category(category)
        latitude,longitude = validate_coordinates(data.get("latitude"),data.get("longitude"))
        photo = data.get("before_photo")
        payload,media_type = parse_image_data_url(photo,"Initial photo")
        with db_session() as db:
            selected = db.execute("""SELECT id FROM issue_categories
              WHERE category=? AND subcategory=? AND active=1""",(group,subcategory)).fetchone()
            if not selected:
                raise ValueError("Choose a valid category and subcategory.")
            route = department_from_db(db,group,subcategory)
            rid = "NG-" + uuid.uuid4().hex[:12].upper()
            cleaned.update({"id":rid,"category":group,"subcategory":subcategory,
                            "suggested_department":route,"before_photo":"pending",
                            "owner_id":user["id"],"latitude":latitude,"longitude":longitude})
            events = [event(user["display_name"],"Report submitted","Citizen-submitted report")]
            rid,master,reason = insert_report(db,cleaned,events=events)
            evidence_id = save_evidence_bytes(db,rid,"before",user["id"],payload,media_type)
            db.execute("UPDATE reports SET before_photo=? WHERE id=?",(f"evidence:{evidence_id}",rid))
            notify_roles(db,ADMIN_ROLES,rid,"report_submitted","New civic complaint",
                         f"{rid} is awaiting municipal review.")
            record_audit(db,user["id"],"report_submitted","report",rid,{"category":group})
            row = db.execute("SELECT * FROM reports WHERE id=?",(rid,)).fetchone()
            response = {"report":report_for_user(row,user),
              "recommendation":{"department":route,
                "explanation":"Suggested from the configured category route. Human review is required."},
              "duplicate":{"master_id":master,"reason":reason} if master else None}
        return json_response(self,response,201)

    def transition(self,user,rid,data):
        action = data.get("action")
        with db_session() as db:
            row = db.execute("SELECT * FROM reports WHERE id=?",(rid,)).fetchone()
            if not row or not can_view_report(db,user,row):
                return json_response(self,{"error":"Issue not found."},404)
            r = pack(row)
            events = r["events"] or []
            stamp = now()
            if action == "assign":
                if user["role"] not in ADMIN_ROLES:
                    return json_response(self,{"error":"Municipal assignment permission is required."},403)
                if r["status"] not in {"submitted","needs_rework"}:
                    raise ValueError("Only submitted or returned issues can be assigned.")
                department = normalize_department(db,data.get("department","") if isinstance(data.get("department"),str) else "")
                worker_id = data.get("worker_id")
                worker = db.execute("""SELECT id,display_name FROM users
                  WHERE id=? AND role='field_worker' AND active=1""",(worker_id,)).fetchone() if isinstance(worker_id,str) else None
                if not department or not worker:
                    raise ValueError("Select an active department and field worker.")
                crew = worker["display_name"]
                events.append(event(user["display_name"],"Work order assigned",f"{department} • {crew}"))
                db.execute("""UPDATE reports SET department=?,crew=?,assigned_to=?,status='assigned',
                  events=?,updated_at=? WHERE id=?""",(department,crew,worker["id"],json.dumps(events),stamp,rid))
                notify_user(db,r["owner_id"],rid,"assigned","Complaint assigned",f"{rid} was assigned to {department}.")
                notify_user(db,worker["id"],rid,"assigned","New work assigned",f"{rid} is assigned to you.")
                record_audit(db,user["id"],"report_assigned","report",rid,{"department":department,"worker_id":worker["id"]})
            elif action == "work_start":
                if user["role"] != "field_worker":
                    return json_response(self,{"error":"Field worker permission is required."},403)
                if r["assigned_to"] != user["id"]:
                    return json_response(self,{"error":"This work order is not assigned to your account."},403)
                if r["status"] not in {"assigned","needs_rework"}:
                    raise ValueError("Work can start only on an assigned or returned issue.")
                events.append(event(user["display_name"],"Work started"))
                db.execute("UPDATE reports SET status='in_progress',events=?,updated_at=? WHERE id=?",
                           (json.dumps(events),stamp,rid))
                notify_user(db,r["owner_id"],rid,"work_started","Work started",f"Field work has started on {rid}.")
                record_audit(db,user["id"],"work_started","report",rid)
            elif action == "repair":
                if user["role"] != "field_worker":
                    return json_response(self,{"error":"Field worker permission is required."},403)
                if r["assigned_to"] != user["id"]:
                    return json_response(self,{"error":"This work order is not assigned to your account."},403)
                if r["status"] != "in_progress":
                    raise ValueError("Start assigned work before submitting repair evidence.")
                note = data.get("repair_note")
                if not isinstance(note,str) or not note.strip() or len(note.strip())>1000:
                    raise ValueError("Add a repair note under 1,000 characters.")
                photo_payload,media_type = parse_image_data_url(data.get("after_photo"),"After photo")
                evidence_id = save_evidence_bytes(db,rid,"after",user["id"],photo_payload,media_type)
                note = note.strip()
                events.append(event(user["display_name"],"Repair submitted","Completion evidence sent for inspection"))
                db.execute("""UPDATE reports SET after_photo=?,repair_note=?,status='repair_submitted',
                  verification=NULL,events=?,updated_at=? WHERE id=?""",
                  (f"evidence:{evidence_id}",note,json.dumps(events),stamp,rid))
                db.execute("""INSERT INTO repair_submissions(id,report_id,worker_id,repair_note,evidence_id,created_at)
                  VALUES (?,?,?,?,?,?)""",(uuid.uuid4().hex,rid,user["id"],note,evidence_id,stamp))
                notify_user(db,r["owner_id"],rid,"repair_submitted","Repair ready for inspection",f"Repair evidence for {rid} is awaiting review.")
                notify_roles(db,{"inspector"},rid,"inspection_needed","Inspection needed",f"{rid} is ready for inspection.")
                notify_roles(db,{"municipal_admin"},rid,"repair_submitted","Repair evidence submitted",f"{rid} is awaiting inspection.")
                record_audit(db,user["id"],"repair_submitted","report",rid)
            elif action == "verify":
                if user["role"] != "inspector":
                    return json_response(self,{"error":"Inspector permission is required."},403)
                if r["status"] != "repair_submitted":
                    raise ValueError("Only submitted repairs can be inspected.")
                checks = data.get("checks")
                if not isinstance(checks,dict) or set(checks) != {"1","2","3","4","5"} or any(type(v) is not bool for v in checks.values()):
                    raise ValueError("Record a pass or fail for each of the five inspection checks.")
                approved = data.get("approved")
                if type(approved) is not bool:
                    raise ValueError("Select approve or return for rework.")
                if approved and not all(checks.values()):
                    raise ValueError("All five checks must pass before verified closure.")
                if not approved and all(checks.values()):
                    raise ValueError("A rejected repair must identify at least one failed check.")
                notes = data.get("notes")
                if not isinstance(notes,str) or not notes.strip() or len(notes.strip())>1000:
                    raise ValueError("Add inspection notes under 1,000 characters.")
                notes = notes.strip()
                verification = {"checks":checks,"approved":approved,"notes":notes,
                                "inspector":user["display_name"],"inspected_at":stamp}
                status = "verified" if approved else "needs_rework"
                action_name = "Repair verified" if approved else "Returned for rework"
                events.append(event(user["display_name"],action_name,notes))
                db.execute("""INSERT INTO inspections(id,report_id,inspector_id,approved,checks,notes,created_at)
                  VALUES (?,?,?,?,?,?,?)""",
                  (uuid.uuid4().hex,rid,user["id"],1 if approved else 0,json.dumps(checks),notes,stamp))
                db.execute("UPDATE reports SET verification=?,status=?,events=?,updated_at=? WHERE id=?",
                           (json.dumps(verification),status,json.dumps(events),stamp,rid))
                notify_user(db,r["owner_id"],rid,"resolved" if approved else "rework",
                            "Complaint resolved" if approved else "Rework requested",
                            f"{rid} was " + ("approved after inspection." if approved else "returned for additional work."))
                notify_user(db,r["assigned_to"],rid,"inspection_result","Inspection completed",
                            f"Inspection of {rid} was " + ("approved." if approved else "returned for rework."))
                record_audit(db,user["id"],"inspection_approved" if approved else "inspection_rejected",
                             "report",rid,{"checks":checks})
            else:
                raise ValueError("Choose a supported workflow action.")
            updated = db.execute("SELECT * FROM reports WHERE id=?",(rid,)).fetchone()
            return json_response(self,{"report":report_for_user(updated,user)})

    def admin_create_user(self,user,data):
        role = data.get("role")
        if role not in ROLES:
            raise ValueError("Choose one of the configured account roles.")
        with db_session() as db:
            created = create_user(db,data.get("email"),data.get("display_name"),data.get("password"),role)
            record_audit(db,user["id"],"user_created","user",created["id"],{"role":role})
            notify_user(db,created["id"],None,"account_created","Staff account created",
                        "Your account is ready. Your system administrator will provide sign-in details.")
            return json_response(self,{"user":user_payload(created)},201)

    def admin_update_user(self,user,user_id,data):
        with db_session() as db:
            target = db.execute("SELECT * FROM users WHERE id=?",(user_id,)).fetchone()
            if not target:
                return json_response(self,{"error":"User not found."},404)
            role = data.get("role",target["role"])
            active = data.get("active",bool(target["active"]))
            if role not in ROLES or type(active) is not bool:
                raise ValueError("Use a supported role and boolean account status.")
            if target["id"] == user["id"] and not active:
                raise ValueError("You cannot deactivate the account currently in use.")
            if target["role"] == "system_admin" and (role != "system_admin" or not active):
                admins = db.execute("SELECT COUNT(*) FROM users WHERE role='system_admin' AND active=1").fetchone()[0]
                if admins <= 1:
                    raise ValueError("The last active system administrator cannot be removed.")
            if target["role"] == "field_worker" and not active:
                assigned = db.execute("""SELECT COUNT(*) FROM reports
                  WHERE assigned_to=? AND status NOT IN ('verified')""",(user_id,)).fetchone()[0]
                if assigned:
                    raise ValueError("Reassign this worker's open work before deactivating the account.")
            db.execute("UPDATE users SET role=?,active=?,updated_at=? WHERE id=?",
                       (role,1 if active else 0,now(),user_id))
            record_audit(db,user["id"],"user_updated","user",user_id,{"role":role,"active":active})
            notify_user(db,user_id,None,"account_updated","Account access updated",
                        "Your account role or access status was updated by a system administrator.")
            row = db.execute("SELECT id,email,display_name,role,active,created_at FROM users WHERE id=?",(user_id,)).fetchone()
            return json_response(self,{"user":user_payload(row)})

    def admin_save_category(self,user,data):
        category = data.get("category")
        subcategory = data.get("subcategory")
        department = data.get("department_id")
        keywords = data.get("keywords","")
        priority = data.get("default_priority",40)
        escalation = data.get("escalation_hours",168)
        active = data.get("active",True)
        if not isinstance(category,str) or not 2<=len(category.strip())<=120:
            raise ValueError("Category must be between 2 and 120 characters.")
        if not isinstance(subcategory,str) or not 2<=len(subcategory.strip())<=160:
            raise ValueError("Subcategory must be between 2 and 160 characters.")
        if not isinstance(keywords,str) or len(keywords)>500:
            raise ValueError("Routing keywords must be under 500 characters.")
        if type(priority) is not int or not 0<=priority<=100:
            raise ValueError("Default priority must be an integer from 0 to 100.")
        if type(escalation) is not int or not 1<=escalation<=8760:
            raise ValueError("Escalation threshold must be 1 to 8,760 hours.")
        if type(active) is not bool:
            raise ValueError("Category status must be enabled or disabled.")
        with db_session() as db:
            dept = db.execute("SELECT id FROM departments WHERE id=? AND active=1",(department,)).fetchone()
            if not dept:
                raise ValueError("Choose an active department.")
            category,subcategory = category.strip(),subcategory.strip()
            cid = slug(category+"-"+subcategory)
            db.execute("""INSERT INTO issue_categories
              (id,category,subcategory,department_id,default_priority,keywords,escalation_hours,active)
              VALUES (?,?,?,?,?,?,?,?)
              ON CONFLICT(category,subcategory) DO UPDATE SET department_id=excluded.department_id,
              default_priority=excluded.default_priority,keywords=excluded.keywords,
              escalation_hours=excluded.escalation_hours,active=excluded.active""",
              (cid,category,subcategory,department,priority,keywords.strip(),escalation,1 if active else 0))
            row = db.execute("SELECT id FROM issue_categories WHERE category=? AND subcategory=?",
                             (category,subcategory)).fetchone()
            db.execute("""INSERT INTO routing_rules(id,category_id,department_id,priority,active)
              VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET department_id=excluded.department_id,
              priority=excluded.priority,active=excluded.active""",
              ("route-"+row["id"],row["id"],department,100,1 if active else 0))
            record_audit(db,user["id"],"category_configured","category",row["id"],
                         {"category":category,"subcategory":subcategory,"department_id":department})
            notify_roles(db,ADMIN_ROLES,None,"configuration_updated","Routing configuration updated",
                         f"Routing for {category} / {subcategory} was updated.")
            return json_response(self,{"ok":True,"id":row["id"]})

    def admin_save_department(self,user,data):
        name = data.get("name")
        active = data.get("active",True)
        if not isinstance(name,str) or not 2<=len(name.strip())<=100 or type(active) is not bool:
            raise ValueError("Enter a department name and valid enabled status.")
        department_id = data.get("id") or slug(name)
        if not isinstance(department_id,str) or not re.fullmatch(r"[a-z0-9-]{2,80}",department_id):
            raise ValueError("Department ID must contain lowercase letters, numbers or hyphens.")
        with db_session() as db:
            existing = db.execute("SELECT id FROM departments WHERE id=?",(department_id,)).fetchone()
            if not active:
                in_use = db.execute("""SELECT COUNT(*) FROM issue_categories
                  WHERE department_id=? AND active=1""",(department_id,)).fetchone()[0]
                if in_use:
                    raise ValueError("Move or deactivate active categories before disabling this department.")
            if existing:
                try:
                    db.execute("UPDATE departments SET name=?,active=? WHERE id=?",
                               (name.strip(),1 if active else 0,department_id))
                except sqlite3.IntegrityError as exc:
                    raise ValueError("A department with that name already exists.") from exc
            else:
                try:
                    db.execute("INSERT INTO departments(id,name,active) VALUES (?,?,?)",
                               (department_id,name.strip(),1 if active else 0))
                except sqlite3.IntegrityError as exc:
                    raise ValueError("A department with that name or ID already exists.") from exc
            record_audit(db,user["id"],"department_configured","department",department_id,
                         {"name":name.strip(),"active":active})
            notify_roles(db,ADMIN_ROLES,None,"configuration_updated","Department configuration updated",
                         f"Department configuration for {name.strip()} changed.")
            return json_response(self,{"ok":True,"id":department_id})

    def static_file(self,path):
        rel = "index.html" if path in {"","/"} else path.lstrip("/")
        target = (PUBLIC / rel).resolve()
        if PUBLIC.resolve() not in target.parents or not target.is_file():
            return json_response(self,{"error":"Not found."},404)
        types = {".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",
                 ".js":"text/javascript; charset=utf-8",".svg":"image/svg+xml"}
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",types.get(target.suffix,"application/octet-stream"))
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-cache")
        self.security_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        return json_response(self,{"error":"Cross-origin requests are not supported."},405)


if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1]=="create-admin":
        init_db()
        email = sys.argv[2] if len(sys.argv)>2 else input("Admin email: ")
        password = getpass.getpass("New admin password (12+ characters): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            raise SystemExit("Passwords do not match.")
        with db_session() as db:
            row = create_user(db,email,"System Administrator",password,"system_admin")
            record_audit(db,row["id"],"admin_created_cli","user",row["id"])
        print("System administrator created.")
    else:
        init_db()
        print(f"Nagrivanta running on port {PORT}")
        ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
