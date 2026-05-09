"""
page_global_artists.py — Global Artist Roster & Management
"""
import streamlit as st
import datetime

SENIORITY = ["Junior", "Mid", "Senior", "Lead", "Freelance"]
AVAIL = ["Available", "Busy", "On Leave", "Archived"]
SKILLS = ["Roto", "Paint", "Tracking", "CG", "Comp", "Motion Graphics",
          "Animation", "Lighting", "FX", "Lookdev", "Matte Painting", "VFX"]

AVAIL_COLORS = {"Available": "#2ECC71", "Busy": "#E67E22", "On Leave": "#4A90D9", "Archived": "#6C7A89"}
SEN_COLORS = {"Junior": "#6C7A89", "Mid": "#4A90D9", "Senior": "#E67E22", "Lead": "#E94560", "Freelance": "#9B59B6"}

def fmt_hours(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def page_global_artists(db, nav_fn):
    st.markdown('<div class="section-header">🌐 Global Artist Roster</div>', unsafe_allow_html=True)

    tc1, tc2, tc3 = st.columns([3, 1, 1])
    with tc1:
        search = st.text_input("", placeholder="Search artists…", label_visibility="collapsed", key="ga_search")
    with tc2:
        avail_filt = st.selectbox("Availability", ["All"] + AVAIL, key="ga_avail")
    with tc3:
        if st.button("➕ Add Artist", use_container_width=True):
            st.session_state["ga_show_add"] = not st.session_state.get("ga_show_add", False)

    # Add form
    if st.session_state.get("ga_show_add"):
        with st.expander("🎨 New Global Artist", expanded=True):
            with st.form("ga_add_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    name = st.text_input("Full Name *")
                    role = st.text_input("Primary Role", placeholder="Roto Artist, Compositor…")
                    sen = st.selectbox("Seniority", SENIORITY, index=1)
                with c2:
                    email = st.text_input("Email")
                    phone = st.text_input("Phone")
                    joined = st.date_input("Joined", value=datetime.date.today())
                with c3:
                    color = st.color_picker("Color Tag", "#f5a623")
                    avail = st.selectbox("Availability", AVAIL)
                    skills = st.multiselect("Skills", SKILLS)
                notes = st.text_area("Bio", height=60)
                s1, s2 = st.columns([1, 5])
                if s1.form_submit_button("✅ Create"):
                    if not name.strip():
                        st.error("Name required")
                    else:
                        db.create_global_artist(
                            name.strip(), role.strip(), email.strip(), phone.strip(), color,
                            ",".join(skills), sen, avail, notes.strip(), joined.strftime("%d-%b-%Y")
                        )
                        st.session_state["ga_show_add"] = False
                        st.success(f"Artist '{name}' added!")
                        st.rerun()
                if s2.form_submit_button("✖ Cancel"):
                    st.session_state["ga_show_add"] = False
                    st.rerun()

    # Load & filter
    artists = db.list_global_artists()
    if search:
        q = search.lower()
        artists = [a for a in artists if q in a.get("name","").lower() or q in a.get("role","").lower()]
    if avail_filt != "All":
        artists = [a for a in artists if a.get("availability") == avail_filt]

    # Stats
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🎨 Total", len(artists))
    m2.metric("✅ Available", sum(1 for a in artists if a.get("availability")=="Available"))
    m3.metric("🔵 Busy", sum(1 for a in artists if a.get("availability")=="Busy"))
    m4.metric("🎬 Shots", sum(a.get("total_shots",0) for a in artists))
    m5.metric("⏱ Tracked", fmt_hours(sum(a.get("total_seconds",0) for a in artists)))
    st.markdown("")

    if not artists:
        st.info("No artists. Click '➕ Add Artist' to start.")
        return

    # Cards (3 per row)
    cols_per_row = 3
    for i in range(0, len(artists), cols_per_row):
        row = artists[i:i+cols_per_row]
        card_cols = st.columns(cols_per_row)
        for col, a in zip(card_cols, row):
            with col:
                avail = a.get("availability", "Available")
                sen = a.get("seniority", "Mid")
                color = a.get("color", "#f5a623")
                skills_raw = a.get("skills", "") or ""
                skill_list = [s.strip() for s in skills_raw.split(",") if s.strip()][:4]
                skill_html = " ".join(
                    f'<span style="background:#16213e;border:1px solid #2d3561;border-radius:4px;'
                    f'padding:1px 6px;font-size:9px;color:#c8d0e0">{s}</span>'
                    for s in skill_list
                )
                ac = AVAIL_COLORS.get(avail, "#6C7A89")
                sc = SEN_COLORS.get(sen, "#4A90D9")
                active = a.get("active_shots", 0)
                total_s = a.get("total_shots", 0)
                hours_str = fmt_hours(a.get("total_seconds", 0))

                st.markdown(f"""
                <div style="background:#16213e;border:1px solid #1e2d4a;border-radius:12px;
                            padding:14px;border-top:3px solid {color}">
                  <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <div>
                      <div style="font-weight:700;color:{color};font-size:15px">{a['name']}</div>
                      <div style="font-size:10px;color:#6c7a89;margin-top:1px">{a.get('role','')}</div>
                    </div>
                    <div style="text-align:right;font-size:8px">
                      <span style="background:{ac}20;color:{ac};border:1px solid {ac}40;border-radius:100px;
                                   padding:1px 6px;display:inline-block;font-weight:700">{avail}</span><br>
                      <span style="background:{sc}20;color:{sc};border:1px solid {sc}40;border-radius:100px;
                                   padding:1px 6px;display:inline-block;font-weight:700;margin-top:2px">{sen}</span>
                    </div>
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px;text-align:center">
                    <div>
                      <div style="font-weight:700;color:#e94560;font-size:16px">{active}</div>
                      <div style="font-size:8px;color:#6c7a89">ACTIVE</div>
                    </div>
                    <div>
                      <div style="font-weight:700;color:#4a90d9;font-size:16px">{total_s}</div>
                      <div style="font-size:8px;color:#6c7a89">TOTAL</div>
                    </div>
                    <div>
                      <div style="font-weight:700;color:#2ECC71;font-size:16px">{hours_str}</div>
                      <div style="font-size:8px;color:#6c7a89">TIME</div>
                    </div>
                  </div>
                  {f'<div style="margin-bottom:8px;font-size:8px">{skill_html}</div>' if skill_html else ''}
                  <div style="font-size:9px;color:#3d4561">
                    {('📧 ' + a['email']) if a.get('email') else ''}{(' · 📞 ' + a['phone']) if a.get('phone') else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("👤", key=f"ga_view_{a['id']}", use_container_width=True):
                        st.session_state["current_global_artist_id"] = a["id"]
                        st.session_state["page"] = "artist_profile"
                        st.rerun()
                with b2:
                    if st.button("✏", key=f"ga_edit_{a['id']}", use_container_width=True):
                        st.session_state[f"ga_editing_{a['id']}"] = True
                with b3:
                    if st.button("🗑", key=f"ga_del_{a['id']}", use_container_width=True):
                        st.session_state[f"ga_del_confirm_{a['id']}"] = True

                # Edit
                if st.session_state.get(f"ga_editing_{a['id']}"):
                    skill_curr = [s.strip() for s in (a.get("skills","") or "").split(",") if s.strip()]
                    with st.form(f"ga_edit_{a['id']}"):
                        new_role = st.text_input("Role", value=a.get("role",""))
                        new_email = st.text_input("Email", value=a.get("email",""))
                        new_sen = st.selectbox("Seniority", SENIORITY, index=SENIORITY.index(a.get("seniority","Mid")))
                        new_avail = st.selectbox("Avail", AVAIL, index=AVAIL.index(a.get("availability","Available")))
                        new_color = st.color_picker("Color", value=a.get("color","#f5a623"))
                        new_skills = st.multiselect("Skills", SKILLS, default=skill_curr)
                        s1, s2 = st.columns(2)
                        if s1.form_submit_button("Save"):
                            db.update_global_artist(a["id"], role=new_role, email=new_email,
                                                   seniority=new_sen, availability=new_avail,
                                                   color=new_color, skills=",".join(new_skills))
                            st.session_state[f"ga_editing_{a['id']}"] = False
                            st.rerun()
                        if s2.form_submit_button("✖"):
                            st.session_state[f"ga_editing_{a['id']}"] = False
                            st.rerun()

                # Delete
                if st.session_state.get(f"ga_del_confirm_{a['id']}"):
                    st.warning(f"Delete '{a['name']}'?")
                    d1, d2 = st.columns(2)
                    if d1.button("Yes", key=f"ga_del_yes_{a['id']}"):
                        db.delete_global_artist(a["id"])
                        st.rerun()
                    if d2.button("No", key=f"ga_del_no_{a['id']}"):
                        st.session_state[f"ga_del_confirm_{a['id']}"] = False
                        st.rerun()

        st.markdown("")
