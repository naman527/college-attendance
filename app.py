import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import create_engine, text

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Campus Portal",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# --- SECURE CREDENTIALS & DB CONNECTION ---
ADMIN_USER = st.secrets.get("ADMIN_USER", "9321481833")
ADMIN_PASS = st.secrets.get("ADMIN_PASS", "aniKet@1124")

try:
    db_url = st.secrets["connections"]["neon"]["url"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)
except Exception as e:
    st.error(f"Database Connection Error: Check your Streamlit Secrets configuration. Details: {e}")
    st.stop()

# --- INITIALIZE POSTGRES TABLES ---
def init_db():
    with engine.begin() as conn_sql:
        conn_sql.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            course TEXT,
            year TEXT,
            is_approved INTEGER
        )
        """)
        conn_sql.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS attendance (
            student_name TEXT,
            course TEXT,
            year TEXT,
            subject TEXT,
            date TEXT,
            month TEXT,
            status TEXT,
            marked_by TEXT
        )
        """)
        conn_sql.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS notices (
            id SERIAL PRIMARY KEY,
            category TEXT,
            title TEXT,
            content TEXT,
            file_data BYTEA,
            file_name TEXT,
            posted_by TEXT,
            role TEXT,
            target_course TEXT,
            target_year TEXT,
            date TEXT
        )
        """)
        conn_sql.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS holidays (
            id SERIAL PRIMARY KEY,
            title TEXT,
            date TEXT,
            category TEXT
        )
        """)
        
        conn_sql.exec_driver_sql("""
        INSERT INTO users (username, password, role, course, year, is_approved)
        VALUES (%s, %s, 'Admin', 'ALL', 'ALL', 1)
        ON CONFLICT (username) DO UPDATE 
        SET password = EXCLUDED.password, role = 'Admin', is_approved = 1
        """, (ADMIN_USER, ADMIN_PASS))

init_db()

# --- MOBILE-FIRST CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

#MainMenu, header, footer, 
div[data-testid="stToolbar"], 
div[data-testid="stDecoration"], 
div[data-testid="stStatusWidget"] {
    display: none !important;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stApp {
    background: #f8fafc !important;
    color: #0f172a !important;
}

label, .stTextInput label, .stSelectbox label, .stTextArea label {
    color: #1e293b !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
}

.stTextInput > div > div > input, 
.stSelectbox > div > div, 
.stTextArea > div > div > textarea {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 2px solid #cbd5e1 !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    padding: 12px !important;
}

.stButton > button {
    width: 100% !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 12px 20px !important;
    border: none !important;
    margin-top: 10px !important;
    background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.25) !important;
}

div[data-testid="stForm"], div[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 24px !important;
}
</style>
""", unsafe_allow_html=True)

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
    "Student in exam: Is this a trick question? Prof: No, it's a test! 🧠",
    "Why was the computer late? It had a hard drive! 💻",
    "Teacher: Name two elements. Student: Unobtanium and surprise elements! 🧪",
    "Why don't students like math? Too many problems! 📐"
]

def get_shortfall(presents, total):
    if total == 0:
        return "ℹ️ No lectures recorded yet."
    pct = (presents / total) * 100
    if pct >= 75.0:
        return "🎉 Excellent! You are above the 75% attendance target."
    needed = (3 * total) - (4 * presents)
    return f"⚠️ Attend the next {max(0, int(needed))} lectures continuously to reach 75%."

def show_notices(t_crs="ALL", t_yr="ALL", c_user="", u_role="", pfx=""):
    st.subheader("📢 Class Notices & Updates")
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
    
    with engine.connect() as conn_sql:
        notices = conn_sql.execute(text(q), tuple(prms)).fetchall()
        
    if notices:
        for n in notices:
            with st.expander(f"📌 [{n[1]}] {n[2]} ({n[8]})"):
                st.write(n[3])
                if n[4] and n[5]:
                    st.download_button("📎 Download Attachment", data=n[4].encode('latin1'), file_name=n[5], key=f"dl_{n[0]}_{pfx}")
                st.caption(f"Posted by: {n[6]} ({n[7]})")
                if u_role == "Admin" or (u_role == "Teacher" and n[6] == c_user):
                    if st.button("🗑️ Delete Notice", key=f"del_{n[0]}_{pfx}"):
                        with engine.begin() as conn_sql:
                            conn_sql.execute(text("DELETE FROM notices WHERE id=:id"), {"id": n[0]})
                        st.success("Notice removed!")
                        st.rerun()
    else:
        st.info("No notices posted right now.")

def show_cal(u_role=""):
    st.subheader("📅 Academic Calendar & Holidays")
    if u_role == "Admin":
        with st.expander("➕ Add New Calendar Event"):
            ht = st.text_input("Event Title", key="ht")
            hd = st.date_input("Event Date", datetime.date.today(), key="hd")
            hc = st.selectbox("Category", ["Holiday", "Exam", "Sports", "Cultural"], key="hc")
            if st.button("💾 Save Event"):
                if ht:
                    with engine.begin() as conn_sql:
                        conn_sql.execute(
                            text("INSERT INTO holidays (title, date, category) VALUES (:t, :d, :c)"),
                            {"t": ht, "d": str(hd), "c": hc}
                        )
                    st.success("Event Added!")
                    st.rerun()

    with engine.connect() as conn_sql:
        evs = conn_sql.execute(text("SELECT id, title, date, category FROM holidays ORDER BY date ASC")).fetchall()
        
    if evs:
        df = pd.DataFrame(evs, columns=["ID", "Event", "Date", "Category"])
        st.dataframe(df[["Event", "Date", "Category"]], use_container_width=True)
        if u_role == "Admin":
            del_id = st.selectbox("Select Event ID to Delete", [e[0] for e in evs], key="del_ev_id")
            if st.button("🗑️ Remove Event"):
                with engine.begin() as conn_sql:
                    conn_sql.execute(text("DELETE FROM holidays WHERE id=:id"), {"id": del_id})
                st.success("Event Deleted!")
                st.rerun()
    else:
        st.info("No upcoming events scheduled.")

# --- STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

if 'joke' not in st.session_state:
    st.session_state['joke'] = random.choice(JOKES)

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.markdown("## 🎓 Campus Portal")
    
    portal = st.selectbox(
        "Select Portal",
        options=["🎓 Student", "👨‍🏫 Teacher", "👑 Admin"]
    )

    st.markdown("---")

    if portal == "🎓 Student":
        st.markdown("### 🎓 Student Access")
        tab_sel = st.radio("Student Options", ["Sign In", "Create Account", "Reset Password"], horizontal=True, label_visibility="collapsed")
        
        if tab_sel == "Sign In":
            u = st.text_input("Student Email", key="su").strip()
            p = st.text_input("Password", type="password", key="sp").strip()
            if st.button("Student Sign In"):
                with engine.connect() as conn_sql:
                    res = conn_sql.execute(
                        text("SELECT * FROM users WHERE username=:u AND password=:p AND role='Student'"),
                        {"u": u, "p": p}
                    ).fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.session_state['course'] = res[3]
                    st.session_state['year'] = res[4]
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
                    with engine.begin() as conn_sql:
                        conn_sql.execute(
                            text("INSERT INTO users VALUES (:u, :p, 'Student', :c, :y, 1)"),
                            {"u": ru, "p": rp, "c": rc, "y": ry}
                        )
                    st.success("Account Created! Sign in now.")
                except:
                    st.error("User already exists.")
                    
        elif tab_sel == "Reset Password":
            fu = st.text_input("Registered Email", key="fsu").strip()
            fp = st.text_input("New Password", type="password", key="fsp").strip()
            if st.button("Reset Password"):
                with engine.begin() as conn_sql:
                    conn_sql.execute(
                        text("UPDATE users SET password=:p WHERE username=:u AND role='Student'"),
                        {"p": fp, "u": fu}
                    )
                st.success("Password Updated!")

    elif portal == "👨‍🏫 Teacher":
        st.markdown("### 👨‍🏫 Faculty Access")
        tab_sel = st.radio("Teacher Options", ["Sign In", "Register Account", "Reset Password"], horizontal=True, label_visibility="collapsed")
        
        if tab_sel == "Sign In":
            u = st.text_input("Teacher Email", key="tu").strip()
            p = st.text_input("Password", type="password", key="tp").strip()
            if st.button("Teacher Sign In"):
                with engine.connect() as conn_sql:
                    res = conn_sql.execute(
                        text("SELECT * FROM users WHERE username=:u AND password=:p AND role='Teacher'"),
                        {"u": u, "p": p}
                    ).fetchone()
                if res:
                    if res[5] == 0:
                        st.warning("Account pending admin approval.")
                    else:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = res[0]
                        st.session_state['role'] = res[2]
                        st.session_state['course'] = res[3]
                        st.session_state['year'] = res[4]
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
                    with engine.begin() as conn_sql:
                        conn_sql.execute(
                            text("INSERT INTO users VALUES (:u, :p, 'Teacher', :c, :y, 0)"),
                            {"u": ru, "p": rp, "c": rc, "y": ry}
                        )
                    st.success("Registered! Awaiting admin approval.")
                except:
                    st.error("User already registered.")
                    
        elif tab_sel == "Reset Password":
            fu = st.text_input("Registered Email", key="ftu").strip()
            fp = st.text_input("New Password", type="password", key="ftp").strip()
            if st.button("Reset Password"):
                with engine.begin() as conn_sql:
                    conn_sql.execute(
                        text("UPDATE users SET password=:p WHERE username=:u AND role='Teacher'"),
                        {"p": fp, "u": fu}
                    )
                st.success("Password Updated!")

    elif portal == "👑 Admin":
        st.markdown("### 👑 Admin Access")
        tab_sel = st.radio("Admin Options", ["Sign In", "Reset Password"], horizontal=True, label_visibility="collapsed")
        
        if tab_sel == "Sign In":
            u = st.text_input("Admin Username", key="ad_u").strip()
            p = st.text_input("Password", type="password", key="ad_p").strip()
            if st.button("Sign In to Control Center"):
                with engine.connect() as conn_sql:
                    res = conn_sql.execute(
                        text("SELECT * FROM users WHERE username=:u AND password=:p AND role='Admin'"),
                        {"u": u, "p": p}
                    ).fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.rerun()
                else:
                    st.error("Invalid Admin Credentials.")
                    
        elif tab_sel == "Reset Password":
            ru = st.text_input("Username to Force Reset", key="au").strip()
            rp = st.text_input("New Admin Password", type="password", key="ap").strip()
            if st.button("Update Admin Password"):
                with engine.begin() as conn_sql:
                    conn_sql.execute(
                        text("UPDATE users SET password=:p WHERE username=:u AND role='Admin'"),
                        {"p": rp, "u": ru}
                    )
                st.success("Admin Password Updated!")

# --- LOGGED-IN DASHBOARDS ---
else:
    col_info, col_logout = st.columns([3, 1])
    with col_info:
        st.markdown(f"👤 Logged in as: **{st.session_state.get('user', '')}** | Role: **{st.session_state.get('role', '')}**")
    with col_logout:
        if st.button("🚪 Logout Now", key="top_logout_btn"):
            st.session_state['logged_in'] = False
            st.session_state['user'] = None
            st.session_state['role'] = None
            st.rerun()
            
    st.markdown("---")

    # --- ADMIN DASHBOARD ---
    if st.session_state.get('role') == "Admin":
        st.title("👑 Master Admin Control Center")
        
        admin_menu = st.radio(
            "Admin Menu", 
            ["📊 Overview", "📢 Post Notice", "⚠️ Defaulters", "👥 User List", "✅ Approvals", "📅 Calendar"], 
            horizontal=True
        )
        st.markdown("---")
        
        if admin_menu == "📊 Overview":
            with engine.connect() as conn_sql:
                att = conn_sql.execute(text("SELECT COUNT(*) FROM attendance")).fetchone()[0]
                prs = conn_sql.execute(text("SELECT COUNT(*) FROM attendance WHERE status='Present'")).fetchone()[0]
            
            c1, c2 = st.columns(2)
            c1.metric("Total Attendance Logs", att)
            c2.metric("Overall Attendance Rate", f"{(prs/att*100) if att>0 else 0:.1f}%")
            
            st.markdown("---")
            st.subheader("📥 Download Class-Specific Attendance CSV")
            dl_course = st.selectbox("Select Course for Download", ["ALL", "BCom", "BMS", "BScIT"], key="dl_crs")
            dl_year = st.selectbox("Select Year for Download", ["ALL", "FY", "SY", "TY"], key="dl_yr")
            
            q_dl = "SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance WHERE 1=1"
            p_dl = {}
            if dl_course != "ALL":
                q_dl += " AND course=:crs"
                p_dl["crs"] = dl_course
            if dl_year != "ALL":
                q_dl += " AND year=:yr"
                p_dl["yr"] = dl_year
                
            with engine.connect() as conn_sql:
                recs_dl = conn_sql.execute(text(q_dl), p_dl).fetchall()
            
            if recs_dl:
                df_dl = pd.DataFrame(recs_dl, columns=["Student", "Course", "Year", "Subject", "Date", "Month", "Status", "Teacher"])
                st.dataframe(df_dl, use_container_width=True)
                
                csv_data = df_dl.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download CSV for {dl_course} - {dl_year}",
                    data=csv_data,
                    file_name=f"attendance_{dl_course}_{dl_year}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No attendance records found for this specific class selection.")

        elif admin_menu == "📢 Post Notice":
            nc = st.selectbox("Category", ["Notice", "Exam", "Urgent"])
            nt = st.text_input("Notice Title")
            nb = st.text_area("Notice Details")
            crs = st.selectbox("Target Course", ["ALL", "BCom", "BMS", "BScIT"])
            yr = st.selectbox("Target Year", ["ALL", "FY", "SY", "TY"])
            if st.button("🚀 Publish Notice Broadcast"):
                with engine.begin() as conn_sql:
                    conn_sql.execute(
                        text("INSERT INTO notices (category, title, content, posted_by, role, target_course, target_year, date) VALUES (:c, :t, :cnt, :pb, 'Admin', :tc, :ty, :d)"),
                        {"c": nc, "t": nt, "cnt": nb, "pb": st.session_state.get('user', ''), "tc": crs, "ty": yr, "d": str(datetime.date.today())}
                    )
                st.success("Notice Published!")
                st.rerun()
            st.markdown("---")
            show_notices(c_user=st.session_state.get('user', ''), u_role="Admin", pfx="adm")

        elif admin_menu == "⚠️ Defaulters":
            st.subheader("⚠️ Low Attendance Report (<75%)")
            with engine.connect() as conn_sql:
                stds = conn_sql.execute(text("SELECT username, course, year FROM users WHERE role='Student'")).fetchall()
            d_list = []
            for s in stds:
                with engine.connect() as conn_sql:
                    ar = conn_sql.execute(text("SELECT status FROM attendance WHERE student_name=:u"), {"u": s[0]}).fetchall()
                t = len(ar)
                p = sum(1 for x in ar if x[0] == 'Present')
                pct =
