"""
Database layer for Nitya VFX Studio — SQLite.
v5.1 — Global Artist Roster + Time Tracking + Portfolio + Workload Dashboard
"""
import sqlite3
import os
import re
import datetime


def _get_db_path(db_path: str) -> str:
    abs_path = os.path.abspath(db_path)
    parent = os.path.dirname(abs_path)
    if os.access(parent, os.W_OK):
        return abs_path
    return os.path.join("/tmp", os.path.basename(db_path))


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    project_type TEXT DEFAULT '',
    client       TEXT DEFAULT '',
    description  TEXT DEFAULT '',
    created      TEXT NOT NULL,
    status       TEXT DEFAULT 'Active'
);
CREATE TABLE IF NOT EXISTS global_artists (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    role            TEXT DEFAULT '',
    email           TEXT DEFAULT '',
    phone           TEXT DEFAULT '',
    color           TEXT DEFAULT '#f5a623',
    skills          TEXT DEFAULT '',
    seniority       TEXT DEFAULT 'Mid',
    availability    TEXT DEFAULT 'Available',
    notes           TEXT DEFAULT '',
    joined_date     TEXT DEFAULT '',
    created         TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artists (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    role       TEXT DEFAULT '',
    email      TEXT DEFAULT '',
    color      TEXT DEFAULT '#f5a623'
);
CREATE TABLE IF NOT EXISTS shots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sequence    TEXT DEFAULT '',
    shot_name   TEXT NOT NULL,
    artist      TEXT DEFAULT '',
    frame_count INTEGER DEFAULT 0,
    start_frame INTEGER DEFAULT 1001,
    end_frame   INTEGER DEFAULT 1001,
    eta         TEXT DEFAULT '',
    status      TEXT DEFAULT 'Pending',
    priority    TEXT DEFAULT 'Normal',
    notes       TEXT DEFAULT '',
    roto        TEXT DEFAULT 'Pending',
    paint       TEXT DEFAULT 'Pending',
    tracking    TEXT DEFAULT 'Pending',
    cg          TEXT DEFAULT 'N/A',
    comp        TEXT DEFAULT 'Pending',
    folder_link TEXT DEFAULT '',
    shot_link   TEXT DEFAULT '',
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shot_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    shot_id   INTEGER NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
    action    TEXT NOT NULL,
    date      TEXT NOT NULL,
    by_artist TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS versions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    shot_id         INTEGER NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
    version         TEXT NOT NULL,
    date_sent       TEXT DEFAULT '',
    artist          TEXT DEFAULT '',
    delivery_notes  TEXT DEFAULT '',
    batch           TEXT DEFAULT '',
    feedback        TEXT DEFAULT 'Pending',
    feedback_date   TEXT DEFAULT '',
    feedback_detail TEXT DEFAULT '',
    feedback_image  TEXT DEFAULT '',
    action          TEXT DEFAULT '',
    status          TEXT DEFAULT 'Pending',
    created         TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS time_sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    shot_id      INTEGER NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
    artist_name  TEXT DEFAULT '',
    dept         TEXT DEFAULT '',
    started_at   TEXT NOT NULL,
    ended_at     TEXT,
    duration_s   INTEGER DEFAULT 0,
    notes        TEXT DEFAULT '',
    created      TEXT DEFAULT CURRENT_DATE,
    FOREIGN KEY(shot_id) REFERENCES shots(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS artist_portfolio (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id   INTEGER NOT NULL REFERENCES global_artists(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    project     TEXT DEFAULT '',
    shot        TEXT DEFAULT '',
    media_url   TEXT DEFAULT '',
    thumbnail   TEXT DEFAULT '',
    category    TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created     TEXT DEFAULT CURRENT_DATE,
    FOREIGN KEY(artist_id) REFERENCES global_artists(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_shots_project  ON shots(project_id);
CREATE INDEX IF NOT EXISTS idx_shots_status   ON shots(status);
CREATE INDEX IF NOT EXISTS idx_shots_artist   ON shots(artist);
CREATE INDEX IF NOT EXISTS idx_shots_seq      ON shots(sequence);
CREATE INDEX IF NOT EXISTS idx_versions_shot  ON versions(shot_id);
CREATE INDEX IF NOT EXISTS idx_history_shot   ON shot_history(shot_id);
CREATE INDEX IF NOT EXISTS idx_time_artist    ON time_sessions(artist_name);
CREATE INDEX IF NOT EXISTS idx_time_shot      ON time_sessions(shot_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_artist ON artist_portfolio(artist_id);
"""

# Migration: add columns that may be missing in older databases
MIGRATIONS = [
    "ALTER TABLE shots ADD COLUMN folder_link TEXT DEFAULT ''",
    "ALTER TABLE shots ADD COLUMN shot_link   TEXT DEFAULT ''",
]


class Database:
    def __init__(self, db_path: str):
        self.db_path = _get_db_path(db_path)
        self._init_schema()
        self._run_migrations()

    def _run(self, sql, params=()):
        con = _connect(self.db_path)
        try:
            cur = con.execute(sql, params)
            con.commit()
            return cur
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _runmany(self, sql, rows):
        con = _connect(self.db_path)
        try:
            cur = con.executemany(sql, rows)
            con.commit()
            return cur
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _fetch(self, sql, params=()):
        con = _connect(self.db_path)
        try:
            return [dict(r) for r in con.execute(sql, params).fetchall()]
        finally:
            con.close()

    def _fetchone(self, sql, params=()):
        con = _connect(self.db_path)
        try:
            row = con.execute(sql, params).fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    def _script(self, sql):
        con = _connect(self.db_path)
        try:
            con.executescript(sql)
            con.commit()
        finally:
            con.close()

    def _init_schema(self):
        self._script(SCHEMA)

    def _run_migrations(self):
        """Safely apply schema additions to existing databases."""
        for sql in MIGRATIONS:
            try:
                self._run(sql)
            except Exception:
                pass  # Column already exists — safe to ignore

    # ── GLOBAL ARTISTS ────────────────────────────────────────────────────────

    def create_global_artist(self, name, role="", email="", phone="", color="#f5a623",
                             skills="", seniority="Mid", availability="Available",
                             notes="", joined_date=""):
        """Add artist to global roster."""
        if not joined_date:
            joined_date = datetime.date.today().strftime("%d-%b-%Y")
        today = datetime.date.today().strftime("%d-%b-%Y")
        try:
            cur = self._run(
                """INSERT INTO global_artists 
                   (name,role,email,phone,color,skills,seniority,availability,notes,joined_date,created)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (name, role, email, phone, color, skills, seniority, availability, notes, joined_date, today)
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def list_global_artists(self):
        """Get all global artists with shot stats."""
        return self._fetch("""
            SELECT ga.*,
                   COUNT(DISTINCT CASE WHEN s.status NOT IN ('Approved','N/A') THEN s.id END) AS active_shots,
                   COUNT(DISTINCT s.id) AS total_shots,
                   COALESCE(SUM(ts.duration_s), 0) AS total_seconds
            FROM global_artists ga
            LEFT JOIN shots s ON s.artist = ga.name
            LEFT JOIN time_sessions ts ON ts.artist_name = ga.name AND ts.ended_at IS NOT NULL
            GROUP BY ga.id
            ORDER BY ga.name
        """)

    def get_global_artist(self, artist_id):
        """Get single global artist by ID."""
        return self._fetchone("SELECT * FROM global_artists WHERE id=?", (artist_id,))

    def get_global_artist_by_name(self, name):
        """Get single global artist by name."""
        return self._fetchone("SELECT * FROM global_artists WHERE name=?", (name,))

    def update_global_artist(self, artist_id, **kwargs):
        """Update global artist."""
        allowed = {"name", "role", "email", "phone", "color", "skills",
                   "seniority", "availability", "notes", "joined_date"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        self._run(f"UPDATE global_artists SET {sets} WHERE id=?", tuple(fields.values()) + (artist_id,))

    def delete_global_artist(self, artist_id):
        """Delete global artist."""
        self._run("DELETE FROM global_artists WHERE id=?", (artist_id,))

    # ── PROJECTS ─────────────────────────────────────────────────────────

    def create_project(self, display_name, project_type="", client="", description=""):
        safe = re.sub(r'[^\w\-]', '_', display_name).lower()
        today = datetime.date.today().strftime("%d-%b-%Y")
        cur = self._run(
            "INSERT INTO projects (name,display_name,project_type,client,description,created) VALUES (?,?,?,?,?,?)",
            (safe, display_name, project_type, client, description, today)
        )
        return cur.lastrowid

    def list_projects(self):
        return self._fetch("""
            SELECT p.*, COUNT(s.id) as shot_count
            FROM projects p LEFT JOIN shots s ON s.project_id=p.id
            GROUP BY p.id ORDER BY p.created DESC
        """)

    def get_project(self, project_id):
        return self._fetchone("SELECT * FROM projects WHERE id=?", (project_id,))

    def update_project(self, project_id, **kwargs):
        allowed = {"display_name", "project_type", "client", "description", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        self._run(f"UPDATE projects SET {sets} WHERE id=?", tuple(fields.values()) + (project_id,))

    def delete_project(self, project_id):
        self._run("DELETE FROM projects WHERE id=?", (project_id,))

    # ── ARTISTS (Project-specific) ────────────────────────────────────────

    def add_artist(self, project_id, name, role="", email="", color="#f5a623"):
        cur = self._run(
            "INSERT INTO artists (project_id,name,role,email,color) VALUES (?,?,?,?,?)",
            (project_id, name, role, email, color)
        )
        return cur.lastrowid

    def list_artists(self, project_id):
        return self._fetch(
            "SELECT a.*, COUNT(s.id) as shot_count FROM artists a "
            "LEFT JOIN shots s ON s.project_id=? AND s.artist=a.name "
            "WHERE a.project_id=? GROUP BY a.id",
            (project_id, project_id)
        )

    def update_artist(self, artist_id, **kwargs):
        allowed = {"name", "role", "email", "color"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        self._run(f"UPDATE artists SET {sets} WHERE id=?", tuple(fields.values()) + (artist_id,))

    def delete_artist(self, artist_id):
        self._run("DELETE FROM artists WHERE id=?", (artist_id,))

    def get_artist_names(self, project_id):
        return [r["name"] for r in self._fetch(
            "SELECT name FROM artists WHERE project_id=? ORDER BY name", (project_id,)
        )]

    # ── SHOTS ──────────────────────────────────────────────────────────

    def add_shot(self, project_id, shot_name, sequence="", artist="",
                 frame_count=0, start_frame=1001, end_frame=1001,
                 eta="", status="Pending", priority="Normal", notes=""):
        today = datetime.date.today().strftime("%d-%b-%Y")
        cur = self._run("""
            INSERT INTO shots
              (project_id,sequence,shot_name,artist,frame_count,start_frame,end_frame,
               eta,status,priority,notes,created,modified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (project_id, sequence, shot_name, artist, frame_count,
              start_frame, end_frame, eta, status, priority, notes, today, today))
        shot_id = cur.lastrowid
        self._run("INSERT INTO shot_history (shot_id,action,date) VALUES (?,?,?)",
                  (shot_id, "Shot created", today))
        return shot_id

    def get_shot(self, shot_id):
        """Return a single shot dict by its primary key."""
        return self._fetchone("SELECT * FROM shots WHERE id=?", (shot_id,))

    def get_shots(self, project_id, filters=None):
        where, params = ["s.project_id=?"], [project_id]
        if filters:
            if filters.get("status"):   where.append("s.status=?");   params.append(filters["status"])
            if filters.get("artist"):   where.append("s.artist=?");   params.append(filters["artist"])
            if filters.get("sequence"): where.append("s.sequence=?"); params.append(filters["sequence"])
            if filters.get("priority"): where.append("s.priority=?"); params.append(filters["priority"])
            if filters.get("search"):
                q = f"%{filters['search']}%"
                where.append("(s.shot_name LIKE ? OR s.notes LIKE ? OR s.artist LIKE ?)")
                params += [q, q, q]
        return self._fetch(
            f"SELECT * FROM shots s WHERE {' AND '.join(where)} ORDER BY s.sequence, s.shot_name",
            params
        )

    def get_shots_for_artist(self, artist_name):
        """Get all shots assigned to an artist."""
        return self._fetch(
            "SELECT * FROM shots WHERE artist=? ORDER BY sequence, shot_name",
            (artist_name,)
        )

    def update_shot(self, shot_id, **kwargs):
        allowed = {"sequence", "shot_name", "artist", "frame_count", "start_frame", "end_frame",
                   "eta", "status", "priority", "notes", "roto", "paint", "tracking", "cg", "comp",
                   "folder_link", "shot_link"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        today = datetime.date.today().strftime("%d-%b-%Y")
        fields["modified"] = today
        sets = ", ".join(f"{k}=?" for k in fields)
        self._run(f"UPDATE shots SET {sets} WHERE id=?", tuple(fields.values()) + (shot_id,))

    def delete_shot(self, shot_id):
        self._run("DELETE FROM shots WHERE id=?", (shot_id,))

    def bulk_insert_shots(self, project_id, shots_list):
        today = datetime.date.today().strftime("%d-%b-%Y")
        def si(v, d):
            try:
                return int(v)
            except Exception:
                return d
        rows = [(
            project_id, s.get("sequence", ""), s.get("shot_name", ""), s.get("artist", ""),
            si(s.get("frame_count"), 0), si(s.get("start_frame"), 1001), si(s.get("end_frame"), 1001),
            s.get("eta", ""), s.get("status", "Pending"), s.get("priority", "Normal"), s.get("notes", ""),
            today, today
        ) for s in shots_list]
        cur = self._runmany("""
            INSERT OR IGNORE INTO shots
              (project_id,sequence,shot_name,artist,frame_count,start_frame,end_frame,
               eta,status,priority,notes,created,modified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)
        return cur.rowcount

    def get_sequences(self, project_id):
        return [r["sequence"] for r in self._fetch(
            "SELECT DISTINCT sequence FROM shots WHERE project_id=? AND sequence!='' ORDER BY sequence",
            (project_id,)
        )]

    def get_project_stats(self, project_id):
        return self._fetchone("""
            SELECT COUNT(*) as total,
              SUM(CASE WHEN status='Approved' THEN 1 ELSE 0 END) as approved,
              SUM(CASE WHEN status='WIP'      THEN 1 ELSE 0 END) as wip,
              SUM(CASE WHEN status='Pending'  THEN 1 ELSE 0 END) as pending,
              SUM(CASE WHEN status='Review'   THEN 1 ELSE 0 END) as review,
              SUM(CASE WHEN status='Hold'     THEN 1 ELSE 0 END) as hold,
              SUM(frame_count) as total_frames
            FROM shots WHERE project_id=?
        """, (project_id,)) or {}

    # ── SHOT HISTORY ──────────────────────────────────────────────────────

    def add_shot_history(self, shot_id, action, by_artist=""):
        today = datetime.date.today().strftime("%d-%b-%Y")
        self._run(
            "INSERT INTO shot_history (shot_id,action,date,by_artist) VALUES (?,?,?,?)",
            (shot_id, action, today, by_artist)
        )

    def get_shot_history(self, shot_id):
        """Return all history entries for a shot, newest first."""
        return self._fetch(
            "SELECT * FROM shot_history WHERE shot_id=? ORDER BY id DESC",
            (shot_id,)
        )

    # ── VERSIONS ──────────────────────────────────────────────────────

    def add_version(self, shot_id, version, date_sent="", artist="",
                    delivery_notes="", batch=""):
        today = datetime.date.today().strftime("%d-%b-%Y")
        if not date_sent:
            date_sent = today
        cur = self._run("""
            INSERT INTO versions
              (shot_id,version,date_sent,artist,delivery_notes,batch,created)
            VALUES (?,?,?,?,?,?,?)
        """, (shot_id, version, date_sent, artist, delivery_notes, batch, today))
        ver_id = cur.lastrowid
        self.add_shot_history(
            shot_id,
            f"Version {version} submitted" + (f" by {artist}" if artist else ""),
            by_artist=artist
        )
        return ver_id

    def get_versions(self, shot_id):
        """Return all versions for a shot, oldest first."""
        return self._fetch(
            "SELECT * FROM versions WHERE shot_id=? ORDER BY id ASC",
            (shot_id,)
        )

    def update_version(self, version_id, **kwargs):
        allowed = {"feedback", "feedback_date", "feedback_detail",
                   "feedback_image", "action", "status", "delivery_notes", "batch"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        self._run(f"UPDATE versions SET {sets} WHERE id=?", tuple(fields.values()) + (version_id,))

    def delete_version(self, version_id):
        self._run("DELETE FROM versions WHERE id=?", (version_id,))

    # ── TIME TRACKING ──────────────────────────────────────────────────

    def start_timer(self, shot_id, artist_name, dept="", notes=""):
        """Start a new timer. Auto-stops any running session for this artist."""
        import datetime as dt
        self.stop_all_running_timers(artist_name)
        now = dt.datetime.utcnow().isoformat()
        cur = self._run(
            "INSERT INTO time_sessions (shot_id,artist_name,dept,started_at,notes) VALUES (?,?,?,?,?)",
            (shot_id, artist_name, dept, now, notes)
        )
        return cur.lastrowid

    def stop_timer(self, session_id):
        """Stop a specific session. Returns duration in seconds."""
        import datetime as dt
        session = self._fetchone("SELECT started_at, ended_at FROM time_sessions WHERE id=?", (session_id,))
        if not session or session["ended_at"]:
            return 0
        now = dt.datetime.utcnow()
        started = dt.datetime.fromisoformat(session["started_at"])
        duration_s = max(1, int((now - started).total_seconds()))
        self._run(
            "UPDATE time_sessions SET ended_at=?, duration_s=? WHERE id=?",
            (now.isoformat(), duration_s, session_id)
        )
        return duration_s

    def stop_all_running_timers(self, artist_name):
        """Stop every open session for this artist."""
        import datetime as dt
        rows = self._fetch(
            "SELECT id, started_at FROM time_sessions WHERE artist_name=? AND ended_at IS NULL",
            (artist_name,)
        )
        now = dt.datetime.utcnow()
        for row in rows:
            started = dt.datetime.fromisoformat(row["started_at"])
            duration_s = max(1, int((now - started).total_seconds()))
            self._run(
                "UPDATE time_sessions SET ended_at=?, duration_s=? WHERE id=?",
                (now.isoformat(), duration_s, row["id"])
            )

    def get_running_timer(self, artist_name):
        """Return running session dict or None."""
        return self._fetchone("""
            SELECT ts.*, s.shot_name, p.display_name AS project_name
            FROM time_sessions ts
            JOIN shots s ON s.id = ts.shot_id
            LEFT JOIN projects p ON p.id = s.project_id
            WHERE ts.artist_name=? AND ts.ended_at IS NULL
            ORDER BY ts.started_at DESC LIMIT 1
        """, (artist_name,))

    def get_time_sessions(self, shot_id=None, artist_name=None, limit=300):
        """Get time sessions."""
        clauses, params = [], []
        if shot_id:
            clauses.append("ts.shot_id=?"); params.append(shot_id)
        if artist_name:
            clauses.append("ts.artist_name=?"); params.append(artist_name)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return self._fetch(f"""
            SELECT ts.*, s.shot_name, p.display_name AS project_name
            FROM time_sessions ts
            JOIN shots s ON s.id = ts.shot_id
            LEFT JOIN projects p ON p.id = s.project_id
            {where}
            ORDER BY ts.started_at DESC LIMIT ?
        """, (*params, limit))

    def get_artist_time_summary(self, artist_name):
        """Get time breakdown by project/shot."""
        return self._fetch("""
            SELECT p.display_name AS project_name,
                   s.shot_name,
                   ts.dept,
                   SUM(ts.duration_s) AS total_s,
                   COUNT(*) AS sessions
            FROM time_sessions ts
            JOIN shots s ON s.id = ts.shot_id
            LEFT JOIN projects p ON p.id = s.project_id
            WHERE ts.artist_name=? AND ts.ended_at IS NOT NULL
            GROUP BY p.id, s.id, ts.dept
            ORDER BY total_s DESC
        """, (artist_name,))

    # ── WORKLOAD ────────────────────────────────────────────────────────

    def get_workload_summary(self):
        """Per-artist shot status breakdown + tracked hours."""
        rows = self._fetch("""
            SELECT
                s.artist AS artist_name,
                SUM(CASE WHEN s.status='WIP'      THEN 1 ELSE 0 END) AS wip,
                SUM(CASE WHEN s.status='Pending'  THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN s.status='Review'   THEN 1 ELSE 0 END) AS review,
                SUM(CASE WHEN s.status='Approved' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN s.status='Retake'   THEN 1 ELSE 0 END) AS retake,
                SUM(CASE WHEN s.status='Hold'     THEN 1 ELSE 0 END) AS hold,
                COUNT(*) AS total_shots,
                COALESCE(SUM(s.frame_count), 0) AS total_frames
            FROM shots s
            WHERE s.artist IS NOT NULL AND s.artist != ''
            GROUP BY s.artist
            ORDER BY wip DESC, total_shots DESC
        """)
        hours_map = {r["artist_name"]: r["total_s"] 
                     for r in self._fetch("""
                        SELECT artist_name, SUM(duration_s) AS total_s
                        FROM time_sessions WHERE ended_at IS NOT NULL
                        GROUP BY artist_name
                     """)}
        for row in rows:
            row["tracked_seconds"] = hours_map.get(row["artist_name"], 0)
        return rows

    # ── PORTFOLIO ────────────────────────────────────────────────────────

    def add_portfolio_entry(self, artist_id, title, project="", shot="",
                            media_url="", thumbnail="", category="", description=""):
        """Add portfolio entry."""
        cur = self._run(
            """INSERT INTO artist_portfolio
               (artist_id,title,project,shot,media_url,thumbnail,category,description)
               VALUES (?,?,?,?,?,?,?,?)""",
            (artist_id, title, project, shot, media_url, thumbnail, category, description)
        )
        return cur.lastrowid

    def get_portfolio(self, artist_id):
        """Get portfolio entries for artist."""
        return self._fetch(
            "SELECT * FROM artist_portfolio WHERE artist_id=? ORDER BY created DESC",
            (artist_id,)
        )

    def delete_portfolio_entry(self, entry_id):
        """Delete portfolio entry."""
        self._run("DELETE FROM artist_portfolio WHERE id=?", (entry_id,))

    # ── ARTIST REPORT ────────────────────────────────────────────────────

    def build_artist_report(self, artist_name):
        """Build comprehensive artist report."""
        shots = self._fetch("""
            SELECT p.display_name AS project, s.sequence, s.shot_name,
                   s.status, s.priority, s.frame_count, s.eta,
                   s.roto, s.paint, s.comp, s.cg, s.tracking
            FROM shots s
            LEFT JOIN projects p ON p.id = s.project_id
            WHERE s.artist = ?
            ORDER BY p.display_name, s.sequence, s.shot_name
        """, (artist_name,))
        time_rows = self.get_artist_time_summary(artist_name)
        total_s = sum(r.get("total_s") or 0 for r in time_rows)
        return {
            "artist":       artist_name,
            "shots":        shots,
            "time_rows":    time_rows,
            "total_hours":  round(total_s / 3600, 2),
            "total_shots":  len(shots),
            "approved":     sum(1 for s in shots if s.get("status") == "Approved"),
            "wip":          sum(1 for s in shots if s.get("status") == "WIP"),
            "retake":       sum(1 for s in shots if s.get("status") == "Retake"),
            "total_frames": sum(s.get("frame_count") or 0 for s in shots),
        }
