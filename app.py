import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="Niranjana Majithia College - Enterprise Portal", 
    layout="wide", 
    page_icon="🎓"
)

ADMIN_USER = st.secrets.get("ADMIN_USER", "9321481833")
ADMIN_PASS = st.secrets.get("ADMIN_PASS", "aniKet@1124")

try:
    db_url = st.secrets["connections"]["neon"]["url"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

def init_db():
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, course TEXT, year TEXT, is_approved INTEGER)")
        conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS attendance (student_name TEXT, course TEXT, year TEXT, subject TEXT, date TEXT, month TEXT, status TEXT, marked_by TEXT)")
        conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS notices (id SERIAL PRIMARY KEY, category TEXT, title TEXT, content TEXT, file_data BYTEA, file_name TEXT, posted_by TEXT, role TEXT, target_course TEXT, target_year TEXT, date TEXT)")
        conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS holidays (id SERIAL PRIMARY KEY, title TEXT, date TEXT, category TEXT)")
        conn.exec_driver_sql(
            "INSERT INTO users (username, password, role, course, year, is_approved) VALUES (%s, %s, 'Admin', 'ALL', 'ALL', 1) ON CONFLICT (username) DO UPDATE SET password = EXCLUDED.password, role = 'Admin', is_approved = 1",
            (ADMIN_USER, ADMIN_PASS)
        )

init_db()

# Custom SaaS Dark/Light Enterprise UI Styling inspired by Tiimi Dashboard Designs
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global App Background */
    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Hide default Streamlit elements */
    #MainMenu, header, footer {visibility: hidden;}

    /* Enterprise Top App Header Bar */
    .saas-topbar {
        background: #0f172a;
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    }
    .saas-topbar h2 {
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* SaaS Dashboard Header Banner */
    .college-banner {
        background: #ffffff;
        padding: 1.75rem 2rem;
        border-radius: 16px;
        color: #0f172a;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .college-banner h1 {
        font-weight: 800;
        font-size: 1.8rem;
        margin: 0 0 0.25rem 0;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .college-banner p {
        font-size: 0.95rem;
        color: #64748b;
        margin: 0;
        font-weight: 500;
    }

    /* Modern Card Containers */
    .custom-card, div.stExpander {
        background: #ffffff !important;
        padding: 1.25rem;
        border-radius: 14px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 1.25rem;
    }

    /* Enhanced Interactive Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        background: #0f172a;
        color: white;
        padding: 0.6rem 1rem;
        border: none;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background: #1e293b;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* SaaS Metric Cards */
    div[data-testid="stMetric"] {
        background: #ffffff;
        padding: 1rem 1.25rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
    }
</style>

<div class="saas-topbar">
    <h2>⚡ Tiimi Workspace <span style="font-size: 0.8rem; background: #2563eb; padding: 2px 8px; border-radius: 6px; font-weight: 500;">Enterprise Edition</span></h2>
    <div style="font-size: 0.85rem; color: #94a3b8;">Niranjana Majithia College Portal</div>
</div>

<div class="college-banner">
    <div>
        <h1>🏛️ Niranjana Majithia College</h1>
        <p>Centralized Attendance, Metrics & Academic Operations Hub</p>
    </div>
    <div style="text-align: right;">
        <span style="background: #eff6ff; color: #1d4ed8; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; border: 1px solid #bfdbfe;">🟢 Live System Active</span>
    </div>
</div>
""", unsafe_allow_html=True)

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
    "Student in exam: Is this a trick question? Prof: No, it's a test! 🧠",
    "Why was the computer late? It had a hard drive! 💻"
]

def get_shortfall(p, t):
    if t == 0:
        return "ℹ️ No lectures recorded yet."
    pcent = (p / t) * 100
    if pcent >= 75.0:
        return "🎉 Excellent! You are safely above the 75% requirement."
    needed = (3 * t) - (4 * p)
    return f"⚠️ Attention required: Attend the next {max(0, int(needed))} lectures consistently to meet the 75% threshold."

def show_notices(t_crs="ALL", t_yr="ALL", c_user="", u_role="", pfx=""):
    st.subheader("📢 Announcements & Notice Board")
    c_flt = st.selectbox("Filter Category", ["ALL", "Notice", "Exam", "Urgent"], key=f"c_{pfx}")
    q = "SELECT id, category, title, content, encode(file_data, 'escape'), file_name, posted_by, role, date FROM notices WHERE 1=1"
    prms = []
    if c_flt != "ALL":
        q += " AND category=%s"
        prms.append(c_flt)
    if t_crs != "ALL":
        q += " AND (target_course=%s OR target_course='ALL')"
        prms.append(t_crs)
    if t_yr != "ALL":
        q += " AND (target_year=%s OR target_year='ALL')"
        prms.append(t_yr)
    q += " ORDER BY id DESC"
    
    with engine.connect() as conn:
        notices = conn.execute(text(q), tuple(prms)).fetchall()
        
    if notices:
        for n in notices:
            with st.expander(f"📌 [{n[1]}] {n[2]} ({n[8]})"):
                st.write(n[3])
                if n[4] and n[5]:
                    st.download_button("📎 Download Attachment", data=n[4].encode('latin1'), file_name=n[5], key=f"dl_{n[0]}_{pfx}")
                st.caption(f"Posted by: {n[6]} ({n[7]})")
                if u_role == "Admin" or (u_role == "Teacher" and n[6] == c_user):
                    if st.button("🗑️ Delete Notice", key=f"del_{n[0]}_{pfx}"):
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM notices WHERE id=:id"), {"id": n[0]})
                        st.success("Notice removed successfully!")
                        st.rerun()
    else:
        st.info("No active notices found.")

def show_cal(u_role=""):
    st.subheader("📅 Academic Schedule & Events")
    if u_role == "Admin":
        with st.expander("➕ Schedule New Event"):
            ht = st.text_input("Event Title", key="ht")
            hd = st.date_input("Event Date", datetime.date.today(), key="hd")
            hc = st.selectbox("Category", ["Holiday", "Exam", "Sports", "Cultural"], key="hc")
            if st.button("💾 Save Event"):
                if ht:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO holidays (title, date, category) VALUES (:t, :d, :c)"), {"t": ht, "d": str(hd), "c": hc})
                    st.success("Event Added!")
                    st.rerun()

    with engine.connect() as conn:
        evs = conn.execute(text("SELECT id, title, date, category FROM holidays ORDER BY date ASC")).fetchall()
    if evs:
        df = pd.DataFrame(evs, columns=["ID", "Event", "Date", "Category"])
        st.dataframe(df[["Event", "Date", "Category"]], use_container_width=True)
        if u_role == "Admin":
            del_id = st.selectbox("Select Event ID to Delete", [e[0] for e in evs], key="del_ev_id")
            if st.button("🗑️ Remove Event"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM holidays WHERE id=:id"), {"id": del_id})
                st.success("Event Deleted!")
                st.rerun()
    else:
        st.info("No scheduled events in calendar.")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

if 'joke' not in st.session_state:
    st.session_state['joke'] = random.choice(JOKES)

if not st.session_state['logged_in']:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        st.markdown("<h3 style='text-align: center; color: #0f172a; margin-bottom: 1.5rem;'>🔐 Portal Authentication</h3>", unsafe_allow_html=True)
        portal = st.selectbox("Select Access Role", options=["🎓 Student", "👨‍🏫 Teacher", "👑 Admin"])
        st.markdown("---")

        if portal == "🎓 Student":
            tab_sel = st.radio("Options", ["Sign In", "Create Account", "Reset Password"], horizontal=True, label_visibility="collapsed")
            if tab_sel == "Sign In":
                u = st.text_input("Student Email", key="su").strip()
                p = st.text_input("Password", type="password", key="sp").strip()
                if st.button("Student Sign In"):
                    with engine.connect() as conn:
                        res = conn.execute(text("SELECT * FROM users WHERE username=:u AND password=:p AND role='Student'"), {"u": u, "p": p}).fetchone()
                    if res:
                        st.session_state.update({'logged_in': True, 'user': res[0], 'role': res[2], 'course': res[3], 'year': res[4]})
                        st.rerun()
                    else:
                        st.error("Invalid Credentials")
            elif tab_sel == "Create Account":
                ru = st.text_input("Email ID", key="rsu").strip()
                rp = st.text_input("Password", type="password", key="rsp").strip()
                rc = st.selectbox("Course", ["BCom", "BMS", "BScIT"], key="rsc")
                ry = st.selectbox("Year", ["FY", "SY", "TY"], key="rsy")
                if st.button("Create Account"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO users VALUES (:u, :p, 'Student', :c, :y, 1)"), {"u": ru, "p": rp, "c": rc, "y": ry})
                        st.success("Account Created! You can sign in now.")
                    except:
                        st.error("User already exists.")
            elif tab_sel == "Reset Password":
                fu = st.text_input("Registered Email", key="fsu").strip()
                fp = st.text_input("New Password", type="password", key="fsp").strip()
                if st.button("Reset Password"):
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE users SET password=:p WHERE username=:u AND role='Student'"), {"p": fp, "u": fu})
                    st.success("Password Updated!")

        elif portal == "👨‍🏫 Teacher":
            tab_sel = st.radio("Options", ["Sign In", "Register Account", "Reset Password"], horizontal=True, label_visibility="collapsed")
            if tab_sel == "Sign In":
                u = st.text_input("Teacher Email", key="tu").strip()
                p = st.text_input("Password", type="password", key="tp").strip()
                if st.button("Teacher Sign In"):
                    with engine.connect() as conn:
                        res = conn.execute(text("SELECT * FROM users WHERE username=:u AND password=:p AND role='Teacher'"), {"u": u, "p": p}).fetchone()
                    if res:
                        if res[5] == 0:
                            st.warning("Account pending administrative approval.")
                        else:
                            st.session_state.update({'logged_in': True, 'user': res[0], 'role': res[2], 'course': res[3], 'year': res[4]})
                            st.rerun()
                    else:
                        st.error("Invalid Credentials")
            elif tab_sel == "Register Account":
                ru = st.text_input("Email ID", key="rtu").strip()
                rp = st.text_input("Password", type="password", key="rtp").strip()
                rc = st.selectbox("Assigned Course", ["BCom", "BMS", "BScIT"], key="rtc")
                ry = st.selectbox("Assigned Year", ["FY", "SY", "TY"], key="rty")
                if st.button("Submit Registration"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO users VALUES (:u, :p, 'Teacher', :c, :y, 0)"), {"u": ru, "p": rp, "c": rc, "y": ry})
                        st.success("Registered! Pending admin approval.")
                    except:
                        st.error("User already registered.")
            elif tab_sel == "Reset Password":
                fu = st.text_input("Registered Email", key="ftu").strip()
                fp = st.text_input("New Password", type="password", key="ftp").strip()
                if st.button("Reset Password"):
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE users SET password=:p WHERE username=:u AND role='Teacher'"), {"p": fp, "u": fu})
                    st.success("Password Updated!")

        elif portal == "👑 Admin":
            tab_sel = st.radio("Options", ["Sign In", "Reset Password"], horizontal=True, label_visibility="collapsed")
            if tab_sel == "Sign In":
                u = st.text_input("Admin Username", key="ad_u").strip()
                p = st.text_input("Password", type="password", key="ad_p").strip()
                if st.button("Sign In to Control Center"):
                    with engine.connect() as conn:
                        res = conn.execute(text("SELECT * FROM users WHERE username=:u AND password=:p AND role='Admin'"), {"u": u, "p": p}).fetchone()
                    if res:
                        st.session_state.update({'logged_in': True, 'user': res[0], 'role': res[2]})
                        st.rerun()
                    else:
                        st.error("Invalid Admin Credentials.")
            elif tab_sel == "Reset Password":
                ru = st.text_input("Username to Force Reset", key="au").strip()
                rp = st.text_input("New Admin Password", type="password", key="ap").strip()
                if st.button("Update Admin Password"):
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE users SET password=:p WHERE username=:u AND role='Admin'"), {"p": rp, "u": ru})
                    st.success("Admin Password Updated!")

else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"👤 Authenticated User: **{st.session_state.get('user', '')}** &nbsp;|&nbsp; Role: **{st.session_state.get('role', '')}**")
    with col2:
        if st.button("🚪 Logout Session"):
            st.session_state.update({'logged_in': False, 'user': None, 'role': None})
            st.rerun()
            
    st.markdown("---")

    role = st.session_state.get('role')

    if role == "Admin":
        st.title("👑 Executive Admin Management Dashboard")
        admin_menu = st.radio("Menu", ["📊 Overview", "📢 Post Notice", "⚠️ Defaulters", "👥 User List", "✅ Approvals", "📅 Calendar"], horizontal=True, key="admin_menu_radio")
        st.markdown("---")
        
        if admin_menu == "📊 Overview":
            with engine.connect() as conn:
                att = conn.execute(text("SELECT COUNT(*) FROM attendance")).fetchone()[0]
                prs = conn.execute(text("SELECT COUNT(*) FROM attendance WHERE status='Present'")).fetchone()[0]
            c1, c2 = st.columns(2)
            c1.metric("Total Attendance Logs", att)
            c2.metric("Overall Attendance Rate", f"{(prs/att*100) if att>0 else 0:.1f}%")
            
            dl_course = st.selectbox("Filter Course for Export", ["ALL", "BCom", "BMS", "BScIT"], key="dl_crs")
            dl_year = st.selectbox("Filter Year for Export", ["ALL", "FY", "SY", "TY"], key="dl_yr")
            q_dl = "SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance WHERE 1=1"
            p_dl = {}
            if dl_course != "ALL":
                q_dl += " AND course=:crs"
                p_dl["crs"] = dl_course
            if dl_year != "ALL":
                q_dl += " AND year=:yr"
                p_dl["yr"] = dl_year
            with engine.connect() as conn:
                recs_dl = conn.execute(text(q_dl), p_dl).fetchall()
            if recs_dl:
                df_dl = pd.DataFrame(recs_dl, columns=["Student", "Course", "Year", "Subject", "Date", "Month", "Status", "Teacher"])
                st.dataframe(df_dl, use_container_width=True)
                st.download_button("📥 Export CSV Report", data=df_dl.to_csv(index=False).encode('utf-8'), file_name="attendance_report.csv", mime="text/csv")
            else:
                st.info("No records found.")

        elif admin_menu == "📢 Post Notice":
            nc = st.selectbox("Category", ["Notice", "Exam", "Urgent"], key="adm_nc")
            nt = st.text_input("Notice Title", key="adm_nt")
            nb = st.text_area("Notice Details", key="adm_nb")
            crs = st.selectbox("Target Course", ["ALL", "BCom", "BMS", "BScIT"], key="adm_crs")
            yr = st.selectbox("Target Year", ["ALL", "FY", "SY", "TY"], key="adm_yr")
            if st.button("🚀 Publish Notice Broadcast", key="adm_pub_btn"):
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO notices (category, title, content, posted_by, role, target_course, target_year, date) VALUES (:c, :t, :cnt, :pb, 'Admin', :tc, :ty, :d)"),
                        {"c": nc, "t": nt, "cnt": nb, "pb": st.session_state.get('user', ''), "tc": crs, "ty": yr, "d": str(datetime.date.today())}
                    )
                st.success("Notice Published Successfully!")
                st.rerun()
            st.markdown("---")
            show_notices(c_user=st.session_state.get('user', ''), u_role="Admin", pfx="adm")

        elif admin_menu == "⚠️ Defaulters":
            st.subheader("⚠️ Low Attendance Tracking (<75%)")
            with engine.connect() as conn:
                stds = conn.execute(text("SELECT username, course, year FROM users WHERE role='Student'")).fetchall()
            d_list = []
            for s in stds:
                with engine.connect() as conn:
                    ar = con
