"""
Nitya VFX Studio — Streamlit Web App  v4.0
Full-featured VFX shot tracking. Shot detail page, version management,
artist assignment, pipeline workflow — deploys on GitHub Codespaces.
"""
import streamlit as st
import pandas as pd
import datetime
import io
import os
import sys
import base64

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nitya VFX Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from database import Database
from excel_io import export_to_excel, import_from_excel
from page_global_artists import page_global_artists
from page_artist_profile  import page_artist_profile
from page_workload        import page_workload

# ── Constants ─────────────────────────────────────────────────────────────────
STATUSES      = ["Pending", "WIP", "Review", "Approved", "Hold", "Retake", "N/A"]
PRIORITIES    = ["Low", "Normal", "High", "Critical"]
PROJECT_TYPES = ["", "Roto/Paint", "Comp", "CG", "VFX", "Animation", "Motion Graphics", "Other"]
DEPT_STATUSES = ["Pending", "WIP", "Done", "N/A"]
COMP_STATUSES = ["Pending", "WIP", "Approved", "Revision", "Sent", "N/A"]
VER_FEEDBACKS = ["Pending", "Approved", "Changes Req.", "No Feedback"]
VER_STATUSES  = ["Pending", "WIP", "Resolved", "Approved", "Changes Req."]

STATUS_COLORS = {
    "Pending":  "#E67E22",
    "WIP":      "#4A90D9",
    "Review":   "#9B59B6",
    "Approved": "#2ECC71",
    "Hold":     "#E74C3C",
    "Retake":   "#F39C12",
    "N/A":      "#6C7A89",
}
PRIORITY_COLORS = {
    "Low":      "#6C7A89",
    "Normal":   "#4A90D9",
    "High":     "#E67E22",
    "Critical": "#E74C3C",
}
DEPT_COLORS = {
    "Done":      "#2ECC71",
    "Approved":  "#2ECC71",
    "WIP":       "#4A90D9",
    "Pending":   "#E67E22",
    "Revision":  "#E74C3C",
    "Sent":      "#9B59B6",
    "N/A":       "#444",
}

# ── Database ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    db_path = os.path.join(os.path.dirname(__file__), "nitya_vfx.db")
    return Database(db_path)

db = get_db()

# ── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    "page": "projects",
    "current_project_id": None,
    "current_shot_id": None,
    "show_add_project": False,
    "show_add_shot": False,
    "edit_shot_id": None,
    "show_bulk_add": False,
    "show_import": False,
    "filter_status": "All",
    "filter_artist": "All",
    "filter_seq": "All",
    "filter_priority": "All",
    "search_query": "",
    "current_global_artist_id": None,
    "ga_show_add": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0a14; }
[data-testid="stSidebar"] {
    background-color: #0f0f2d;
    border-right: 1px solid #1e1e4a;
}
[data-testid="stSidebar"] * { color: #c8d0e0 !important; }
h1, h2, h3 { color: #e94560 !important; }
.stMarkdown p { color: #c8d0e0; }

[data-testid="metric-container"] {
    background: #16213e;
    border: 1px solid #1e1e4a;
    border-radius: 8px;
    padding: 12px;
}
[data-testid="stMetricValue"] { color: #e94560 !important; font-size: 2rem !important; }
[data-testid="stMetricLabel"] { color: #6c7a89 !important; }

.stButton > button {
    background: #16213e;
    color: #c8d0e0;
    border: 1px solid #2d3561;
    border-radius: 6px;
    transition: all 0.15s;
}
.stButton > button:hover {
    background: #e94560;
    border-color: #e94560;
    color: #fff;
}

.proj-card {
    background: #16213e;
    border: 1px solid #1e1e4a;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 12px;
    transition: border-color 0.15s;
}
.proj-card:hover { border-color: #e94560; }
.proj-card-name { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.proj-card-meta { font-size: 12px; color: #6c7a89; }
.proj-card-shots { font-size: 13px; font-weight: 700; color: #4a90d9; }

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

[data-testid="stDataFrame"] {
    background: #16213e !important;
    border: 1px solid #1e1e4a !important;
    border-radius: 8px;
}

.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background-color: #16213e !important;
    color: #c8d0e0 !important;
    border-color: #2d3561 !important;
}

.section-header {
    font-size: 22px;
    font-weight: 700;
    color: #e94560;
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e1e4a;
}

/* Shot detail 3-panel */
.shot-panel {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 12px;
    padding: 16px;
    height: 100%;
}
.shot-panel-header {
    font-family: monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: #6c7a89;
    text-transform: uppercase;
    border-bottom: 1px solid #1e2d4a;
    padding-bottom: 8px;
    margin-bottom: 14px;
}
.dept-card {
    background: #16213e;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    border-left: 3px solid #2d3561;
}
.dept-card-done  { border-left-color: #2ECC71; }
.dept-card-wip   { border-left-color: #4A90D9; }
.dept-card-pend  { border-left-color: #E67E22; }
.dept-card-na    { border-left-color: #444; }

.ver-card {
    background: #16213e;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
}
.ver-card-approved { border-color: #2ECC7140; }
.ver-card-changes  { border-color: #E74C3C40; }

.history-item {
    font-family: monospace;
    font-size: 11px;
    color: #6c7a89;
    padding: 4px 0;
    border-bottom: 1px solid #1e2d4a;
}
.history-action { color: #c8d0e0; }

.breadcrumb { font-size: 13px; color: #6c7a89; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def status_badge(status):
    c = STATUS_COLORS.get(status, "#6C7A89")
    return f'<span class="badge" style="background:{c}20;color:{c};border:1px solid {c}40">{status}</span>'

def priority_badge(priority):
    c = PRIORITY_COLORS.get(priority, "#4A90D9")
    return f'<span class="badge" style="background:{c}20;color:{c};border:1px solid {c}40">{priority}</span>'

def dept_badge(val):
    c = DEPT_COLORS.get(val, "#6C7A89")
    return f'<span class="badge" style="background:{c}20;color:{c};border:1px solid {c}40;font-size:10px">{val}</span>'

def stats_bar(stats):
    total = stats.get("total", 0)
    if total == 0:
        return
    cols = st.columns(7)
    cols[0].metric("Total", total)
    cols[1].metric("✅ Approved", stats.get("approved", 0))
    cols[2].metric("🔵 WIP", stats.get("wip", 0))
    cols[3].metric("⏳ Pending", stats.get("pending", 0))
    cols[4].metric("🔍 Review", stats.get("review", 0))
    cols[5].metric("🛑 Hold", stats.get("hold", 0))
    frames = stats.get("total_frames") or 0
    cols[6].metric("🎞 Frames", f"{frames:,}")

def nav(page, **kwargs):
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎬 Nitya VFX Studio")
        st.markdown("---")

        if st.button("📁  Projects", use_container_width=True):
            nav("projects", current_project_id=None, current_shot_id=None)

        if st.session_state.current_project_id:
            proj = db.get_project(st.session_state.current_project_id)
            if proj:
                st.markdown("---")
                st.markdown("**Current Project**")
                st.markdown(f"🎞 {proj['display_name']}")
                if st.button("📊  Shots", use_container_width=True):
                    nav("shots", current_shot_id=None)
                if st.button("👥  Artists", use_container_width=True):
                    nav("artists")

        if st.session_state.current_shot_id and st.session_state.page == "shot_detail":
            shot = db.get_shot(st.session_state.current_shot_id)
            if shot:
                st.markdown("---")
                st.markdown(f"🎯 **{shot['shot_name']}**")

            st.markdown("---")
        if st.button("🌐  All Artists", use_container_width=True):
            nav("global_artists")
        if st.button("📊  Workload", use_container_width=True):
            nav("workload")
        st.markdown("---")
        st.markdown(
            "<div style='font-size:11px;color:#3d4561;text-align:center'>"
            "Nitya VFX Studio v4.0<br>© 2025 Nitya VFX</div>",
            unsafe_allow_html=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PROJECTS
# ═══════════════════════════════════════════════════════════════════════════════
def page_projects():
    st.markdown('<div class="section-header">🎬 Projects</div>', unsafe_allow_html=True)

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search = st.text_input("", placeholder="Search projects…", label_visibility="collapsed", key="proj_search")
    with col_btn:
        if st.button("➕  New Project", use_container_width=True):
            st.session_state.show_add_project = True

    if st.session_state.show_add_project:
        with st.expander("📋 Create New Project", expanded=True):
            with st.form("new_project_form"):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("Project Name *", placeholder="e.g. Marvel_S01_VFX")
                    project_type = st.selectbox("Project Type", PROJECT_TYPES)
                with c2:
                    client = st.text_input("Client / Studio")
                    description = st.text_area("Description", height=68)
                s1, s2 = st.columns([1, 5])
                with s1:
                    if st.form_submit_button("✅ Create", use_container_width=True):
                        if not name.strip():
                            st.error("Project name is required.")
                        else:
                            db.create_project(name.strip(), project_type, client.strip(), description.strip())
                            st.session_state.show_add_project = False
                            st.success(f"Project '{name}' created!")
                            st.rerun()
                with s2:
                    if st.form_submit_button("✖ Cancel"):
                        st.session_state.show_add_project = False
                        st.rerun()

    projects = db.list_projects()
    if search:
        q = search.lower()
        projects = [p for p in projects if q in p.get("display_name", "").lower()
                    or q in p.get("client", "").lower()
                    or q in p.get("project_type", "").lower()]

    if not projects:
        st.info("No projects yet. Click '➕ New Project' to get started.")
        return

    cols = st.columns(3)
    for idx, proj in enumerate(projects):
        col = cols[idx % 3]
        with col:
            ptype  = proj.get("project_type", "") or ""
            client = proj.get("client", "") or ""
            shots  = proj.get("shot_count", 0)
            badge_html = (f'<span class="badge" style="background:#e9456020;color:#e94560;border:1px solid #e9456040">{ptype}</span>'
                          if ptype else "")
            st.markdown(f"""
            <div class="proj-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                    {badge_html}
                    <span class="proj-card-shots">{shots} shots</span>
                </div>
                <div class="proj-card-name">{proj['display_name']}</div>
                <div class="proj-card-meta">{client}</div>
                <div class="proj-card-meta" style="margin-top:4px">Created: {proj.get('created','')}</div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Open →", key=f"open_{proj['id']}", use_container_width=True):
                    nav("shots", current_project_id=proj["id"], current_shot_id=None)
            with b2:
                if st.button("Edit", key=f"edit_{proj['id']}", use_container_width=True):
                    st.session_state[f"editing_proj_{proj['id']}"] = True
            with b3:
                if st.button("🗑", key=f"del_{proj['id']}", use_container_width=True):
                    st.session_state[f"confirm_del_{proj['id']}"] = True

            if st.session_state.get(f"editing_proj_{proj['id']}"):
                with st.form(f"edit_proj_{proj['id']}"):
                    new_type   = st.selectbox("Type", PROJECT_TYPES, index=PROJECT_TYPES.index(ptype) if ptype in PROJECT_TYPES else 0)
                    new_client = st.text_input("Client", value=client)
                    new_desc   = st.text_area("Description", value=proj.get("description", ""), height=60)
                    s1, s2 = st.columns(2)
                    if s1.form_submit_button("Save"):
                        db.update_project(proj["id"], project_type=new_type, client=new_client, description=new_desc)
                        st.session_state[f"editing_proj_{proj['id']}"] = False
                        st.rerun()
                    if s2.form_submit_button("Cancel"):
                        st.session_state[f"editing_proj_{proj['id']}"] = False
                        st.rerun()

            if st.session_state.get(f"confirm_del_{proj['id']}"):
                st.warning(f"Delete '{proj['display_name']}' and ALL its shots?")
                d1, d2 = st.columns(2)
                if d1.button("Yes, Delete", key=f"yes_del_{proj['id']}", use_container_width=True):
                    db.delete_project(proj["id"])
                    if st.session_state.current_project_id == proj["id"]:
                        st.session_state.current_project_id = None
                        st.session_state.page = "projects"
                    st.session_state[f"confirm_del_{proj['id']}"] = False
                    st.rerun()
                if d2.button("Cancel", key=f"no_del_{proj['id']}", use_container_width=True):
                    st.session_state[f"confirm_del_{proj['id']}"] = False
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SHOTS
# ═══════════════════════════════════════════════════════════════════════════════
def page_shots():
    project_id = st.session_state.current_project_id
    proj = db.get_project(project_id)
    if not proj:
        st.error("Project not found.")
        return

    if st.button("← Back to Projects"):
        nav("projects", current_project_id=None, current_shot_id=None)

    st.markdown(f'<div class="section-header">🎞 {proj["display_name"]}</div>', unsafe_allow_html=True)
    stats = db.get_project_stats(project_id)
    stats_bar(stats)
    st.markdown("")

    # ── Toolbar ───────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5 = st.columns([2, 1, 1, 1, 1])
    with t1:
        st.session_state.search_query = st.text_input(
            "", placeholder="🔍 Search shots…",
            value=st.session_state.search_query,
            label_visibility="collapsed", key="shot_search"
        )
    with t2:
        if st.button("➕ Add Shot", use_container_width=True):
            st.session_state.show_add_shot = True
            st.session_state.edit_shot_id = None
    with t3:
        if st.button("📋 Bulk Add", use_container_width=True):
            st.session_state.show_bulk_add = True
    with t4:
        if st.button("📥 Import Excel", use_container_width=True):
            st.session_state.show_import = True
    with t5:
        shots_for_export = db.get_shots(project_id)
        if shots_for_export:
            excel_buf = io.BytesIO()
            export_to_excel(proj, shots_for_export, excel_buf)
            excel_buf.seek(0)
            st.download_button(
                "📤 Export Excel",
                data=excel_buf,
                file_name=f"{proj['display_name']}_shots.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # ── Filters ───────────────────────────────────────────────────────────────
    sequences    = ["All"] + db.get_sequences(project_id)
    artist_names = ["All"] + db.get_artist_names(project_id)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.session_state.filter_status   = st.selectbox("Status",   ["All"] + STATUSES,   key="filt_status")
    with f2:
        st.session_state.filter_artist   = st.selectbox("Artist",   artist_names,          key="filt_artist")
    with f3:
        st.session_state.filter_seq      = st.selectbox("Sequence", sequences,             key="filt_seq")
    with f4:
        st.session_state.filter_priority = st.selectbox("Priority", ["All"] + PRIORITIES,  key="filt_prio")

    # ── Add / Edit Shot form ──────────────────────────────────────────────────
    if st.session_state.show_add_shot:
        edit_shot = None
        if st.session_state.edit_shot_id:
            edit_shot = db.get_shot(st.session_state.edit_shot_id)
        title = "✏️ Edit Shot" if edit_shot else "🎞 Add New Shot"
        with st.expander(title, expanded=True):
            with st.form("add_shot_form"):
                artists_list = db.get_artist_names(project_id)
                c1, c2, c3 = st.columns(3)
                with c1:
                    sequence  = st.text_input("Sequence", value=edit_shot["sequence"] if edit_shot else "", placeholder="SEQ_010")
                    shot_name = st.text_input("Shot Name *", value=edit_shot["shot_name"] if edit_shot else "", placeholder="SH0010")
                with c2:
                    artist_opts = [""] + artists_list
                    cur_artist  = edit_shot["artist"] if edit_shot else ""
                    artist_idx  = artist_opts.index(cur_artist) if cur_artist in artist_opts else 0
                    artist      = st.selectbox("Artist", artist_opts, index=artist_idx)
                    status_idx  = STATUSES.index(edit_shot["status"]) if edit_shot and edit_shot.get("status") in STATUSES else 0
                    status      = st.selectbox("Status", STATUSES, index=status_idx)
                with c3:
                    pri_idx     = PRIORITIES.index(edit_shot["priority"]) if edit_shot and edit_shot.get("priority") in PRIORITIES else 1
                    priority    = st.selectbox("Priority", PRIORITIES, index=pri_idx)
                    frame_count = st.number_input("Frame Count", min_value=0, value=int(edit_shot["frame_count"]) if edit_shot else 0)

                c4, c5, c6 = st.columns(3)
                with c4:
                    start_frame = st.number_input("Start Frame", min_value=0, value=int(edit_shot["start_frame"]) if edit_shot else 1001)
                with c5:
                    end_frame   = st.number_input("End Frame", min_value=0, value=int(edit_shot["end_frame"]) if edit_shot else 1001)
                with c6:
                    eta_val = None
                    if edit_shot and edit_shot.get("eta"):
                        try:
                            eta_val = datetime.datetime.strptime(edit_shot["eta"], "%d-%b-%Y").date()
                        except Exception:
                            pass
                    eta = st.date_input("ETA", value=eta_val or (datetime.date.today() + datetime.timedelta(days=7)))

                notes = st.text_area("Notes", value=edit_shot.get("notes", "") if edit_shot else "", height=60)

                s1, s2 = st.columns([1, 5])
                if s1.form_submit_button("✅ Save Shot"):
                    if not shot_name.strip():
                        st.error("Shot name is required.")
                    else:
                        eta_str = eta.strftime("%d-%b-%Y")
                        if edit_shot:
                            db.update_shot(
                                edit_shot["id"],
                                sequence=sequence, shot_name=shot_name.strip(),
                                artist=artist, frame_count=int(frame_count),
                                start_frame=int(start_frame), end_frame=int(end_frame),
                                eta=eta_str, status=status, priority=priority, notes=notes
                            )
                            db.add_shot_history(edit_shot["id"], "Shot updated", by_artist=artist)
                            st.success("Shot updated!")
                        else:
                            db.add_shot(
                                project_id, shot_name.strip(), sequence=sequence,
                                artist=artist, frame_count=int(frame_count),
                                start_frame=int(start_frame), end_frame=int(end_frame),
                                eta=eta_str, status=status, priority=priority, notes=notes
                            )
                            st.success(f"Shot '{shot_name}' added!")
                        st.session_state.show_add_shot = False
                        st.session_state.edit_shot_id  = None
                        st.rerun()
                if s2.form_submit_button("✖ Cancel"):
                    st.session_state.show_add_shot = False
                    st.session_state.edit_shot_id  = None
                    st.rerun()

    # ── Bulk Add ──────────────────────────────────────────────────────────────
    if st.session_state.show_bulk_add:
        with st.expander("📋 Bulk Add Shots", expanded=True):
            with st.form("bulk_add_form"):
                st.caption("One shot per line. Format: `SH0010` or `SEQ_010|SH0010`")
                shots_text = st.text_area("Shots", height=160, placeholder="SH0010\nSH0020\nSH0030")
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    default_seq    = st.text_input("Default Sequence", "")
                with bc2:
                    anl = db.get_artist_names(project_id)
                    default_artist = st.selectbox("Default Artist", [""] + anl)
                with bc3:
                    default_status = st.selectbox("Default Status", STATUSES)
                sb1, sb2 = st.columns([1, 5])
                if sb1.form_submit_button("✅ Add All"):
                    count = 0
                    for line in shots_text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        if "|" in line:
                            seq, sname = line.split("|", 1)
                            seq, sname = seq.strip(), sname.strip()
                        else:
                            seq, sname = default_seq, line
                        if sname:
                            db.add_shot(project_id, sname, sequence=seq, artist=default_artist, status=default_status)
                            count += 1
                    st.success(f"Added {count} shots!")
                    st.session_state.show_bulk_add = False
                    st.rerun()
                if sb2.form_submit_button("✖ Cancel"):
                    st.session_state.show_bulk_add = False
                    st.rerun()

    # ── Excel Import ──────────────────────────────────────────────────────────
    if st.session_state.show_import:
        with st.expander("📥 Import from Excel", expanded=True):
            uploaded = st.file_uploader("Choose Excel file", type=["xlsx", "xls"])
            ic1, ic2 = st.columns([1, 5])
            if uploaded and ic1.button("Import", use_container_width=True):
                shots_data = import_from_excel(uploaded)
                if shots_data:
                    db.bulk_insert_shots(project_id, shots_data)
                    st.success(f"Imported {len(shots_data)} shots!")
                    st.session_state.show_import = False
                    st.rerun()
                else:
                    st.error("No valid shots found.")
            if ic2.button("Cancel", use_container_width=False):
                st.session_state.show_import = False
                st.rerun()

    # ── Build filters & load shots ────────────────────────────────────────────
    filters = {}
    if st.session_state.filter_status   != "All": filters["status"]   = st.session_state.filter_status
    if st.session_state.filter_artist   != "All": filters["artist"]   = st.session_state.filter_artist
    if st.session_state.filter_seq      != "All": filters["sequence"] = st.session_state.filter_seq
    if st.session_state.filter_priority != "All": filters["priority"] = st.session_state.filter_priority
    if st.session_state.search_query:              filters["search"]   = st.session_state.search_query

    shots = db.get_shots(project_id, filters)

    if not shots:
        st.info("No shots found. Try adjusting filters or add new shots.")
        return

    st.markdown(f"**{len(shots)} shots** — click a shot to open the detail view")

    # ── Shot table with Open Detail button ────────────────────────────────────
    for shot in shots:
        with st.container():
            c_name, c_artist, c_status, c_pri, c_frames, c_eta, c_open, c_edit, c_del = st.columns(
                [2.5, 2, 1.5, 1.5, 1, 1.5, 1, 0.7, 0.7]
            )
            seq_prefix = f"[{shot['sequence']}] " if shot.get("sequence") else ""
            c_name.markdown(
                f"<span style='color:#fff;font-weight:700'>{seq_prefix}{shot['shot_name']}</span>",
                unsafe_allow_html=True
            )
            artist = shot.get("artist") or "—"
            c_artist.markdown(
                f"<span style='color:#f5a623'>{artist}</span>",
                unsafe_allow_html=True
            )
            c_status.markdown(status_badge(shot.get("status", "")), unsafe_allow_html=True)
            c_pri.markdown(priority_badge(shot.get("priority", "")), unsafe_allow_html=True)
            c_frames.markdown(f"<span style='color:#4a90d9'>{shot.get('frame_count',0)}</span>", unsafe_allow_html=True)
            c_eta.markdown(f"<span style='color:#6c7a89;font-size:11px'>{shot.get('eta','')}</span>", unsafe_allow_html=True)
            with c_open:
                if st.button("🎬 Open", key=f"open_shot_{shot['id']}", use_container_width=True):
                    nav("shot_detail", current_shot_id=shot["id"])
            with c_edit:
                if st.button("✏", key=f"edit_s_{shot['id']}", use_container_width=True):
                    st.session_state.edit_shot_id  = shot["id"]
                    st.session_state.show_add_shot = True
                    st.rerun()
            with c_del:
                if st.button("🗑", key=f"del_s_{shot['id']}", use_container_width=True):
                    st.session_state[f"confirm_del_shot_{shot['id']}"] = True

            if st.session_state.get(f"confirm_del_shot_{shot['id']}"):
                st.warning(f"Delete '{shot['shot_name']}'?")
                d1, d2 = st.columns(2)
                if d1.button("Yes", key=f"yes_ds_{shot['id']}"):
                    db.delete_shot(shot["id"])
                    st.session_state[f"confirm_del_shot_{shot['id']}"] = False
                    st.rerun()
                if d2.button("No", key=f"no_ds_{shot['id']}"):
                    st.session_state[f"confirm_del_shot_{shot['id']}"] = False
                    st.rerun()

        st.divider()

    # ── Quick status/artist update ────────────────────────────────────────────
    with st.expander("⚡ Quick Update", expanded=False):
        shot_map = {f"{s.get('sequence','')} | {s['shot_name']} ({s.get('status','')})": s for s in shots}
        selected_label = st.selectbox("Select Shot", list(shot_map.keys()), key="quick_sel")
        sel = shot_map.get(selected_label)
        if sel:
            qa1, qa2, qa3, qa4 = st.columns([2, 2, 2, 1])
            with qa1:
                new_status = st.selectbox("Status", STATUSES,
                    index=STATUSES.index(sel["status"]) if sel["status"] in STATUSES else 0,
                    key="qs_status")
            with qa2:
                new_priority = st.selectbox("Priority", PRIORITIES,
                    index=PRIORITIES.index(sel["priority"]) if sel["priority"] in PRIORITIES else 1,
                    key="qs_prio")
            with qa3:
                all_artists = [""] + db.get_artist_names(project_id)
                cur_a   = sel.get("artist", "") or ""
                a_idx   = all_artists.index(cur_a) if cur_a in all_artists else 0
                new_art = st.selectbox("Assign Artist", all_artists, index=a_idx, key="qs_artist")
            with qa4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Apply", use_container_width=True):
                    db.update_shot(sel["id"], status=new_status, priority=new_priority, artist=new_art)
                    db.add_shot_history(sel["id"], f"Quick update: {new_status} / {new_art}", by_artist=new_art)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SHOT DETAIL  (3-panel layout)
# ═══════════════════════════════════════════════════════════════════════════════
def page_shot_detail():
    shot_id    = st.session_state.current_shot_id
    project_id = st.session_state.current_project_id
    shot = db.get_shot(shot_id)
    if not shot:
        st.error("Shot not found.")
        return

    proj = db.get_project(project_id)
    versions = db.get_versions(shot_id)
    history  = db.get_shot_history(shot_id)

    # Back button
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Shots"):
            nav("shots")
    with col_title:
        st.markdown(
            f"<h2 style='color:#e94560;margin:0'>🎬 {shot['shot_name']}"
            f"<span style='font-size:14px;color:#6c7a89;margin-left:12px'>"
            f"{proj['display_name'] if proj else ''}</span></h2>",
            unsafe_allow_html=True
        )

    # Top info bar
    info_parts = []
    if shot.get("sequence"):
        info_parts.append(f"📂 <b style='color:#4a90d9'>{shot['sequence']}</b>")
    if shot.get("artist"):
        info_parts.append(f"🎨 <b style='color:#f5a623'>{shot['artist']}</b>")
    if shot.get("frame_count"):
        info_parts.append(f"🎞 <b style='color:#00e5a0'>{shot['frame_count']} frames</b>")
    if shot.get("eta"):
        info_parts.append(f"📅 <span style='color:#6c7a89'>{shot['eta']}</span>")
    info_parts.append(status_badge(shot.get("status", "")))
    info_parts.append(priority_badge(shot.get("priority", "")))
    st.markdown("&nbsp;&nbsp;·&nbsp;&nbsp;".join(info_parts), unsafe_allow_html=True)
    st.markdown("---")

    # ── 3-Panel Layout ────────────────────────────────────────────────────────
    left_col, center_col, right_col = st.columns([1.1, 1.3, 1.2])

    # ══ LEFT PANEL — Shot Details & Artist Assignment ══════════════════════════
    with left_col:
        st.markdown('<div class="shot-panel-header">🎬 SHOT DETAILS</div>', unsafe_allow_html=True)

        with st.form("shot_detail_form"):
            # Artist dropdown (key v4 feature)
            all_artists  = [""] + db.get_artist_names(project_id)
            cur_artist   = shot.get("artist", "") or ""
            artist_idx   = all_artists.index(cur_artist) if cur_artist in all_artists else 0
            new_artist   = st.selectbox("🎨 Assign Artist", all_artists, index=artist_idx)

            new_sequence = st.text_input("📂 Sequence", value=shot.get("sequence", ""))
            new_frames   = st.number_input("🎞 Frame Count", min_value=0, value=int(shot.get("frame_count", 0)))

            col_sf, col_ef = st.columns(2)
            with col_sf:
                new_sf = st.number_input("Start", min_value=0, value=int(shot.get("start_frame", 1001)))
            with col_ef:
                new_ef = st.number_input("End",   min_value=0, value=int(shot.get("end_frame", 1001)))

            try:
                eta_d = datetime.datetime.strptime(shot["eta"], "%d-%b-%Y").date() if shot.get("eta") else datetime.date.today()
            except Exception:
                eta_d = datetime.date.today()
            new_eta    = st.date_input("📅 ETA", value=eta_d)

            st_idx = STATUSES.index(shot["status"]) if shot.get("status") in STATUSES else 0
            new_status = st.selectbox("Status", STATUSES, index=st_idx)

            pri_idx    = PRIORITIES.index(shot["priority"]) if shot.get("priority") in PRIORITIES else 1
            new_prio   = st.selectbox("Priority", PRIORITIES, index=pri_idx)

            new_notes  = st.text_area("📝 Notes", value=shot.get("notes", ""), height=80)

            st.markdown("**🔗 Preview Links**")
            new_folder = st.text_input("📁 Folder Link", value=shot.get("folder_link", ""), placeholder="Google Drive URL…")
            new_slink  = st.text_input("🎬 Shot Link",   value=shot.get("shot_link", ""),   placeholder="Direct MP4/image URL…")

            if st.form_submit_button("💾 Save Details", use_container_width=True):
                old_artist = shot.get("artist", "")
                db.update_shot(
                    shot_id,
                    artist=new_artist, sequence=new_sequence,
                    frame_count=int(new_frames), start_frame=int(new_sf), end_frame=int(new_ef),
                    eta=new_eta.strftime("%d-%b-%Y"),
                    status=new_status, priority=new_prio, notes=new_notes,
                    folder_link=new_folder, shot_link=new_slink
                )
                if old_artist != new_artist:
                    db.add_shot_history(shot_id, f"Artist: {old_artist or 'none'} → {new_artist or 'none'}", by_artist=new_artist)
                else:
                    db.add_shot_history(shot_id, "Details updated", by_artist=new_artist)
                st.success("Saved!")
                st.rerun()

        # Delete shot
        st.markdown("---")
        if st.button("🗑 Delete Shot", use_container_width=True):
            st.session_state["confirm_del_detail"] = True
        if st.session_state.get("confirm_del_detail"):
            st.warning("Delete this shot permanently?")
            d1, d2 = st.columns(2)
            if d1.button("Yes, delete"):
                db.delete_shot(shot_id)
                st.session_state["confirm_del_detail"] = False
                nav("shots", current_shot_id=None)
            if d2.button("Cancel"):
                st.session_state["confirm_del_detail"] = False
                st.rerun()

    # ══ CENTER PANEL — Pipeline Workflow ═══════════════════════════════════════
    with center_col:
        st.markdown('<div class="shot-panel-header">⚡ PIPELINE WORKFLOW</div>', unsafe_allow_html=True)

        # Refresh shot for latest dept values
        shot = db.get_shot(shot_id)

        DEPT_META = [
            ("roto",     "✂️",  "ROTO",     DEPT_STATUSES),
            ("paint",    "🖌️", "PAINT",    DEPT_STATUSES),
            ("tracking", "🎯",  "TRACKING", DEPT_STATUSES),
            ("cg",       "🖥️", "CG",       DEPT_STATUSES),
            ("comp",     "🎨",  "COMP",     COMP_STATUSES),
        ]

        # Progress summary bar
        active_depts = [(d, shot.get(d, "N/A")) for d, *_ in DEPT_META if shot.get(d, "N/A") != "N/A"]
        done_count   = sum(1 for _, v in active_depts if v in ("Done", "Approved"))
        prog_pct     = int(done_count / max(len(active_depts), 1) * 100)

        st.markdown(
            f"<div style='margin-bottom:12px'>"
            f"<div style='font-family:monospace;font-size:10px;color:#6c7a89;letter-spacing:1px;margin-bottom:6px'>"
            f"PIPELINE PROGRESS — {done_count}/{len(active_depts)} stages complete</div>"
            f"<div style='background:#16213e;border-radius:4px;height:6px;width:100%'>"
            f"<div style='background:#2ECC71;height:6px;border-radius:4px;width:{prog_pct}%;transition:width .3s'></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

        # Per-dept update forms
        for dept_key, dept_icon, dept_label, dept_opts in DEPT_META:
            current_val = shot.get(dept_key, "N/A")
            color_map   = {"Done": "dept-card-done", "Approved": "dept-card-done",
                           "WIP": "dept-card-wip", "Pending": "dept-card-pend", "N/A": "dept-card-na"}
            card_cls    = color_map.get(current_val, "dept-card-na")

            st.markdown(
                f'<div class="dept-card {card_cls}">'
                f'<span style="font-size:13px">{dept_icon}</span>&nbsp;'
                f'<b style="letter-spacing:1px">{dept_label}</b>&nbsp;&nbsp;'
                f'{dept_badge(current_val)}'
                f'</div>',
                unsafe_allow_html=True
            )
            new_val = st.selectbox(
                f"{dept_label}", dept_opts,
                index=dept_opts.index(current_val) if current_val in dept_opts else 0,
                key=f"dept_{dept_key}_{shot_id}",
                label_visibility="collapsed"
            )
            if st.button(f"Save {dept_label}", key=f"save_dept_{dept_key}_{shot_id}", use_container_width=True):
                db.update_shot(shot_id, **{dept_key: new_val})
                db.add_shot_history(shot_id, f"{dept_label}: {current_val} → {new_val}", by_artist=shot.get("artist",""))
                st.success(f"{dept_label} → {new_val}")
                st.rerun()

        # ── Add Version ───────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="shot-panel-header" style="margin-top:8px">📤 SUBMIT NEW VERSION</div>', unsafe_allow_html=True)

        with st.form("add_version_form"):
            v1, v2 = st.columns(2)
            with v1:
                ver_num    = st.text_input("Version *", placeholder="v01")
                ver_date   = st.date_input("Date Sent", value=datetime.date.today())
            with v2:
                ver_artist = st.selectbox("Artist", [""] + db.get_artist_names(project_id), key="ver_artist_sel")
                ver_batch  = st.text_input("Batch #", placeholder="BATCH_01")
            ver_notes  = st.text_area("Delivery Notes", height=60, placeholder="What changed in this version…")

            if st.form_submit_button("✓ Submit Version", use_container_width=True):
                if not ver_num.strip():
                    st.error("Version number required (e.g. v01)")
                else:
                    db.add_version(
                        shot_id,
                        version=ver_num.strip(),
                        date_sent=ver_date.strftime("%d-%b-%Y"),
                        artist=ver_artist,
                        delivery_notes=ver_notes.strip(),
                        batch=ver_batch.strip()
                    )
                    st.success(f"Version {ver_num} submitted!")
                    st.rerun()

    # ══ RIGHT PANEL — Version History + Shot History ═══════════════════════════
    with right_col:
        st.markdown(
            f'<div class="shot-panel-header">📋 VERSION HISTORY&nbsp;&nbsp;'
            f'<span style="background:rgba(155,89,182,.15);color:#9b59b6;border:1px solid rgba(155,89,182,.3);'
            f'border-radius:100px;padding:1px 8px;font-size:9px">{len(versions)}</span></div>',
            unsafe_allow_html=True
        )

        if not versions:
            st.markdown(
                '<div style="text-align:center;padding:30px 10px;color:#6c7a89;font-family:monospace;font-size:11px">'
                '📭<br>No versions yet.<br>Submit the first version from the workflow panel.</div>',
                unsafe_allow_html=True
            )
        else:
            # Newest version first
            for ver in reversed(versions):
                fb = ver.get("feedback", "Pending")
                fb_color = {"Approved": "#2ECC71", "Changes Req.": "#E74C3C"}.get(fb, "#6c7a89")
                ver_card_cls = {"Approved": "ver-card-approved", "Changes Req.": "ver-card-changes"}.get(fb, "")

                with st.expander(
                    f"**{ver['version']}** · {ver.get('date_sent','—')} · "
                    f"{ver.get('artist','—')}",
                    expanded=False
                ):
                    # Info pills
                    pills = []
                    if ver.get("batch"):     pills.append(f"📦 {ver['batch']}")
                    if ver.get("feedback"):  pills.append(f"FB: {ver['feedback']}")
                    if ver.get("status"):    pills.append(f"Status: {ver['status']}")
                    if ver.get("feedback_date"): pills.append(f"FB Date: {ver['feedback_date']}")
                    if pills:
                        st.markdown(" &nbsp; ".join(
                            f'<span style="background:#16213e;border:1px solid #2d3561;border-radius:4px;'
                            f'padding:1px 7px;font-size:10px;color:#c8d0e0">{p}</span>'
                            for p in pills
                        ), unsafe_allow_html=True)

                    if ver.get("delivery_notes"):
                        st.markdown(f"**Delivery Notes:** {ver['delivery_notes']}")
                    if ver.get("feedback_detail"):
                        st.markdown(f"**Client Feedback:** {ver['feedback_detail']}")
                    if ver.get("action"):
                        st.markdown(f"**Action Required:** {ver['action']}")

                    # Edit feedback
                    st.markdown("---")
                    with st.form(f"fb_form_{ver['id']}"):
                        ef1, ef2 = st.columns(2)
                        with ef1:
                            fb_cur = ver.get("feedback", "Pending")
                            new_fb = st.selectbox("Feedback", VER_FEEDBACKS,
                                index=VER_FEEDBACKS.index(fb_cur) if fb_cur in VER_FEEDBACKS else 0,
                                key=f"vfb_{ver['id']}")
                            new_fb_date = st.date_input("FB Date",
                                value=datetime.date.today(), key=f"vfbd_{ver['id']}")
                        with ef2:
                            st_cur = ver.get("status", "Pending")
                            new_st = st.selectbox("Task Status", VER_STATUSES,
                                index=VER_STATUSES.index(st_cur) if st_cur in VER_STATUSES else 0,
                                key=f"vst_{ver['id']}")
                            new_dn = st.text_input("Delivery Notes", value=ver.get("delivery_notes", ""), key=f"vdn_{ver['id']}")
                        new_fbd  = st.text_area("Client Feedback Notes", value=ver.get("feedback_detail",""), height=60, key=f"vfbd2_{ver['id']}")
                        new_act  = st.text_input("Action Required", value=ver.get("action",""), key=f"vact_{ver['id']}")

                        if st.form_submit_button("💾 Save Feedback", use_container_width=True):
                            db.update_version(
                                ver["id"],
                                feedback=new_fb,
                                feedback_date=new_fb_date.strftime("%d-%b-%Y"),
                                status=new_st,
                                delivery_notes=new_dn,
                                feedback_detail=new_fbd,
                                action=new_act
                            )
                            db.add_shot_history(shot_id,
                                f"Feedback on {ver['version']}: {new_fb}",
                                by_artist=shot.get("artist",""))
                            st.success("Feedback saved!")
                            st.rerun()

        # ── Shot History ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="shot-panel-header">📅 SHOT HISTORY</div>', unsafe_allow_html=True)

        if not history:
            st.caption("No history yet.")
        else:
            for h in history[:15]:  # Show last 15 entries
                st.markdown(
                    f'<div class="history-item">'
                    f'<span style="color:#4a90d9">{h["date"]}</span> — '
                    f'<span class="history-action">{h["action"]}</span>'
                    + (f' <span style="color:#f5a623">({h["by_artist"]})</span>' if h.get("by_artist") else "")
                    + '</div>',
                    unsafe_allow_html=True
                )
            if len(history) > 15:
                st.caption(f"… and {len(history)-15} more entries")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ARTISTS
# ═══════════════════════════════════════════════════════════════════════════════
def page_artists():
    project_id = st.session_state.current_project_id
    proj = db.get_project(project_id)
    if not proj:
        st.error("Project not found.")
        return

    if st.button("← Back to Shots"):
        nav("shots")

    st.markdown(f'<div class="section-header">👥 Artists — {proj["display_name"]}</div>', unsafe_allow_html=True)

    with st.expander("➕ Add Artist", expanded=False):
        with st.form("add_artist_form"):
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                a_name = st.text_input("Name *", placeholder="Artist name")
                a_role = st.text_input("Role", placeholder="Roto, Comp, CG…")
            with ac2:
                a_email = st.text_input("Email", placeholder="artist@studio.com")
            with ac3:
                a_color = st.color_picker("Color tag", "#f5a623")
            if st.form_submit_button("✅ Add Artist"):
                if not a_name.strip():
                    st.error("Name is required.")
                else:
                    db.add_artist(project_id, a_name.strip(), a_role.strip(), a_email.strip(), a_color)
                    st.success(f"Added {a_name}!")
                    st.rerun()

    artists = db.list_artists(project_id)
    if not artists:
        st.info("No artists yet. Add your first artist above.")
        return

    st.markdown(f"**{len(artists)} artists on this project**")

    for a in artists:
        ac1, ac2, ac3, ac4, ac5, ac6 = st.columns([3, 2, 3, 1, 1, 1])
        color = a.get("color", "#f5a623")
        ac1.markdown(f'<span style="color:{color};font-weight:700">●</span> **{a["name"]}**', unsafe_allow_html=True)
        ac2.caption(a.get("role", ""))
        ac3.caption(a.get("email", ""))
        ac4.metric("Shots", a.get("shot_count", 0))
        with ac5:
            if st.button("✏", key=f"edit_artist_{a['id']}"):
                st.session_state[f"edit_a_{a['id']}"] = True
        with ac6:
            if st.button("🗑", key=f"del_artist_{a['id']}"):
                db.delete_artist(a["id"])
                st.rerun()

        if st.session_state.get(f"edit_a_{a['id']}"):
            with st.form(f"edit_artist_form_{a['id']}"):
                ea1, ea2 = st.columns(2)
                new_aname  = ea1.text_input("Name",  value=a["name"])
                new_arole  = ea2.text_input("Role",  value=a.get("role",""))
                new_aemail = ea1.text_input("Email", value=a.get("email",""))
                new_acolor = ea2.color_picker("Color", value=a.get("color","#f5a623"))
                s1, s2 = st.columns(2)
                if s1.form_submit_button("Save"):
                    db.update_artist(a["id"], name=new_aname, role=new_arole, email=new_aemail, color=new_acolor)
                    st.session_state[f"edit_a_{a['id']}"] = False
                    st.rerun()
                if s2.form_submit_button("Cancel"):
                    st.session_state[f"edit_a_{a['id']}"] = False
                    st.rerun()

        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
render_sidebar()

page = st.session_state.page
if page == "projects":
    page_projects()
elif page == "shots" and st.session_state.current_project_id:
    page_shots()
elif page == "shot_detail" and st.session_state.current_shot_id:
    page_shot_detail()
elif page == "artists" and st.session_state.current_project_id:
    page_artists()
elif page == "global_artists":
    page_global_artists(db, nav)
elif page == "artist_profile":
    page_artist_profile(db, nav)
elif page == "workload":
    page_workload(db, nav)
else:
    page_projects()
