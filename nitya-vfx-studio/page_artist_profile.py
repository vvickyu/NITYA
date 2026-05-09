"""
page_artist_profile.py — Individual Artist Profile & Statistics
"""
import streamlit as st
import pandas as pd

def fmt_hours(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def page_artist_profile(db, artist_id, nav_fn):
    """Display full artist profile & work history."""
    
    artist = db.get_global_artist(artist_id)
    if not artist:
        st.error("Artist not found")
        return

    if st.button("← Back to Roster"):
        st.session_state["page"] = "global_artists"
        st.rerun()

    # Header
    color = artist.get("color", "#f5a623")
    sen = artist.get("seniority", "Mid")
    avail = artist.get("availability", "Available")

    st.markdown(f"""
    <div style="background:#16213e;border:1px solid #1e2d4a;border-radius:12px;padding:20px;border-left:5px solid {color};margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="font-size:32px;font-weight:700;color:{color}">{artist['name']}</div>
          <div style="font-size:16px;color:#c8d0e0;margin-top:4px">{artist.get('role', '—')}</div>
          <div style="font-size:12px;color:#6c7a89;margin-top:8px">
            {'📧 ' + artist['email'] if artist.get('email') else ''} 
            {' · 📞 ' + artist['phone'] if artist.get('phone') else ''}
            {' · Joined: ' + artist.get('joined_date', '—') if artist.get('joined_date') else ''}
          </div>
          <div style="margin-top:8px">
            <span style="background:#9B59B620;color:#9B59B6;border:1px solid #9B59B640;border-radius:100px;padding:4px 12px;font-size:11px;font-weight:700;margin-right:8px">{sen}</span>
            <span style="background:#2ECC7120;color:#2ECC71;border:1px solid #2ECC7140;border-radius:100px;padding:4px 12px;font-size:11px;font-weight:700">{avail}</span>
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:11px;color:#6c7a89;letter-spacing:1px;text-transform:uppercase">Bio</div>
          <div style="font-size:12px;color:#c8d0e0;max-width:400px;margin-top:8px">{artist.get('notes', '—')}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats columns
    shots = db.get_shots_for_artist(artist['name'])
    time_logs = db.get_artist_time_summary(artist['name'])
    total_s = sum(r.get("total_s") or 0 for r in time_logs)
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🎬 Total Shots", len(shots))
    m2.metric("✅ Approved", sum(1 for s in shots if s.get("status") == "Approved"))
    m3.metric("🔵 WIP", sum(1 for s in shots if s.get("status") == "WIP"))
    m4.metric("🎞 Frames", sum(s.get("frame_count", 0) for s in shots))
    m5.metric("⏱ Tracked Time", fmt_hours(total_s))

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Assigned Shots", "⏱ Time Logs", "🖼 Portfolio"])

    # ── SHOTS ──────────────────────────────────────────────────────
    with tab1:
        if not shots:
            st.info("No shots assigned yet.")
        else:
            df = pd.DataFrame([{
                "Project": s.get("display_name") or s.get("project_id", "—"),
                "Sequence": s.get("sequence", "—"),
                "Shot": s.get("shot_name"),
                "Status": s.get("status", "—"),
                "Priority": s.get("priority", "—"),
                "Frames": s.get("frame_count", 0),
                "ETA": s.get("eta", "—"),
            } for s in shots])
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── TIME LOGS ──────────────────────────────────────────────────
    with tab2:
        if not time_logs:
            st.info("No time entries yet.")
        else:
            df = pd.DataFrame([{
                "Project": r.get("project_name", "—"),
                "Shot": r.get("shot_name", "—"),
                "Task": r.get("dept", "—"),
                "Sessions": r.get("sessions", 0),
                "Total Time": fmt_hours(r.get("total_s", 0)),
            } for r in time_logs])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Timeline
            st.markdown("### Time Entry History")
            recent = db.get_time_sessions(artist_name=artist['name'], limit=20)
            if recent:
                for sess in recent:
                    dur = fmt_hours(sess.get("duration_s", 0))
                    st.markdown(f"""
                    <div style="background:#16213e;border-left:3px solid {color};padding:12px;margin-bottom:8px;border-radius:4px">
                      <div style="font-weight:700;color:#c8d0e0">{sess.get('project_name', '—')} — {sess.get('shot_name', '—')}</div>
                      <div style="font-size:11px;color:#6c7a89;margin-top:4px">
                        {sess.get('dept', '—')} | {dur} | {sess.get('created', '—')}
                      </div>
                      {f"<div style='font-size:10px;color:#3d4561;margin-top:4px;font-style:italic'>{sess.get('notes', '')}</div>" if sess.get('notes') else ''}
                    </div>
                    """, unsafe_allow_html=True)

    # ── PORTFOLIO ──────────────────────────────────────────────────
    with tab3:
        portfolio = db.get_portfolio(artist['id'])
        
        if st.button("➕ Add Portfolio Entry"):
            st.session_state["show_port_add"] = not st.session_state.get("show_port_add", False)
        
        if st.session_state.get("show_port_add"):
            with st.form("add_portfolio_form"):
                title = st.text_input("Title *")
                proj = st.text_input("Project")
                shot = st.text_input("Shot")
                cat = st.selectbox("Category", ["Roto", "Paint", "CG", "Comp", "VFX", "Other"])
                url = st.text_input("Media URL")
                thumb = st.text_input("Thumbnail URL")
                desc = st.text_area("Description", height=60)
                s1, s2 = st.columns([1, 5])
                if s1.form_submit_button("✅ Add"):
                    if title.strip():
                        db.add_portfolio_entry(artist['id'], title, proj, shot, url, thumb, cat, desc)
                        st.session_state["show_port_add"] = False
                        st.success("Added!")
                        st.rerun()
                if s2.form_submit_button("✖"):
                    st.session_state["show_port_add"] = False
                    st.rerun()

        if not portfolio:
            st.info("No portfolio entries yet.")
        else:
            for entry in portfolio:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if entry.get("thumbnail"):
                            st.image(entry["thumbnail"], use_column_width=True)
                    with col2:
                        st.markdown(f"""
                        **{entry['title']}**  
                        {entry.get('project', '—')} | {entry.get('shot', '—')} | **{entry.get('category', '—')}**  
                        {entry.get('description', '')}  
                        {f"[View]({entry['media_url']})" if entry.get('media_url') else ''}
                        """)
                    if st.button("🗑 Delete", key=f"del_port_{entry['id']}"):
                        db.delete_portfolio_entry(entry['id'])
                        st.rerun()
                    st.divider()
