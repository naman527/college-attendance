import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Campus Portal",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# --- HARDCODED ADMIN CREDENTIALS ---
ADMIN_USER = "9321481833"
ADMIN_PASS = "aniKet@1124"

# --- CLEAN HIGH-CONTRAST MOBILE-FIRST CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* HIDE STREAMLIT BRANDING & FOOTER BADGES */
#MainMenu, header, footer, 
div[data-testid="stToolbar"], 
div[data-testid="stDecoration"], 
div[data-testid="stStatusWidget"],
button[title="View app source"],
.viewerBadge_container__1S-5D,
a[href*="github.com"],
[data-testid="stActionButtonIcon"] {
    display: none !important;
    visibility: hidden !important;
}

/* Global Light Clean Theme */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: #f8fafc !important;
    color: #0f172a !important;
}

/* HIGH-CONTRAST INPUT LABELS */
label, .stTextInput label, .stSelectbox label, .stTextArea label {
    color: #1e293b !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    margin-bottom: 6px !important;
}

/* HIGH-CONTRAST TABS */
button[data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 16px !important;
    background: transparent !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #4f46e5 !important;
    border-bottom: 3px solid #4f46e5 !important;
}

/* Mobile Input Field Boxes */
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

.stTextInput > div > div > input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2) !important;
}

/* Buttons */
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

/* Form Container Card */
div[data-testid="stForm"], div[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
}

/* Metric Display */
div[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #4f46e5 !important;
}

div[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
conn = sqlite3.connect('college_attendance.db', check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT,
    course TEXT,
    year TEXT,
    is_approved INTEGER
)
""")

c.execute("""
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

c.execute("""
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    content TEXT,
    file_data BLOB,
    file_name TEXT,
    posted_by TEXT,
    role TEXT,
    target_course TEXT,
    target_year TEXT,
    date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT,
    category TEXT
)
""")

# Migrations Check
c.execute("PRAGMA table_info(notices)")
n_cols = [col[1] for col in c.fetchall()]
if 'file_data' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN file_data BLOB")
if 'file_name' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN file_name TEXT")
if 'category' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN category DEFAULT 'Notice'")

c.execute("PRAGMA table_info(attendance)")
a_cols = [col[1] for col in c.fetchall()]
if 'month' not in a_cols:
    c.execute("ALTER TABLE attendance ADD COLUMN month TEXT")
if 'subject' not in a_cols:
    c.execute("ALTER TABLE attendance ADD COLUMN subject DEFAULT 'General'")

conn.commit()

# Ensure Exact Admin Credentials Exist
c.execute("""
INSERT INTO users (
    username, password, role, course, year, is_approved
) VALUES (
    ?, ?, 'Admin', 'ALL', 'ALL', 1
) ON CONFLICT(username) DO UPDATE SET 
    password=?, role='Admin', is_approved=1
""", (ADMIN_USER, ADMIN_PASS, ADMIN_PASS))
conn.commit()

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
    
    q = "SELECT id, category, title, content, file_data, file_name, posted_by, role, date FROM notices WHERE 1=1"
    prms = []
    if c_flt != "ALL":
        q += " AND category=?"
        prms.append(c_flt)
    if t_crs != "ALL":
        q += " AND (target_course=? OR target_course='ALL')"
        prms.append(t_crs)
    if t_yr != "ALL":
        q += " AND (target_year=? OR target_year='ALL')"
        prms.append(t_yr)
    q += " ORDER BY id DESC"
    
    c.execute(q, prms)
    notices = c.fetchall()
    if notices:
        for n in notices:
            with st.expander(f"📌 [{n[1]}] {n[2]} ({n[8]})"):
                st.write(n[3])
                if n[4] and n[5]:
                    st.download_button("📎 Download Attachment", data=n[4], file_name=n[5], key=f"dl_{n[0]}_{pfx}")
                st.caption(f"Posted by: {n[6]} ({n[7]})")
                if u_role == "Admin" or (u_role == "Teacher" and n[6] == c_user):
                    if st.button("🗑️ Delete Notice", key=f"del_{n[0]}_{pfx}"):
                        c.execute("DELETE FROM notices WHERE id=?", (n[0],))
                        conn.commit()
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
                    c.execute("INSERT INTO holidays (title, date, category) VALUES (?, ?, ?)", (ht, str(hd), hc))
                    conn.commit()
                    st.success("Event Added!")
                    st.rerun()

    c.execute("SELECT id, title, date, category FROM holidays ORDER BY date ASC")
    evs = c.fetchall()
    if evs:
        df = pd.DataFrame(evs, columns=["ID", "Event", "Date", "Category"])
        st.dataframe(df[["Event", "Date", "Category"]], use_container_width=True)
        if u_role == "Admin":
            del_id = st.selectbox("Select Event ID to Delete", [e[0] for e in evs])
            if st.button("🗑️ Remove Event"):
                c.execute("DELETE FROM holidays WHERE id=?", (del_id,))
                conn.commit()
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
    
    portal = st.radio(
        "Select Portal",
        options=["🎓 Student", "👨‍🏫 Teacher", "👑 Admin"],
        horizontal=True
    )

    st.markdown("---")

    if portal == "🎓 Student":
        st.markdown("### 🎓 Student Access")
        t1, t2, t3 = st.tabs(["🔐 Sign In", "📝 Create Account", "🔑 Reset Password"])
        with t1:
            u = st.text_input("Student Email", key="su").strip()
            p = st.text_input("Password", type="password", key="sp").strip()
            if st.button("Student Sign In"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Student'", (u, p))
                res = c.fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.session_state['course'] = res[3]
                    st.session_state['year'] = res[4]
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        with t2:
            ru = st.text_input("Email ID", key="rsu").strip()
            rp = st.text_input("Password", type="password", key="rsp").strip()
            rc = st.selectbox("Course", ["BCom", "BMS", "BScIT"], key="rsc")
            ry = st.selectbox("Year", ["FY", "SY", "TY"], key="rsy")
            if st.button("Create Account"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Student', ?, ?, 1)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Account Created! Sign in now.")
                except:
                    st.error("User already exists.")
        with t3:
            fu = st.text_input("Registered Email", key="fsu").strip()
            fp = st.text_input("New Password", type="password", key="fsp").strip()
            if st.button("Reset Password"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Student'", (fp, fu))
                conn.commit()
                st.success("Password Updated!")

    elif portal == "👨‍🏫 Teacher":
        st.markdown("### 👨‍🏫 Faculty Access")
        t1, t2, t3 = st.tabs(["🔐 Sign In", "📝 Register Account", "🔑 Reset Password"])
        with t1:
            u = st.text_input("Teacher Email", key="tu").strip()
            p = st.text_input("Password", type="password", key="tp").strip()
            if st.button("Teacher Sign In"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Teacher'", (u, p))
                res = c.fetchone()
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
        with t2:
            ru = st.text_input("Email ID", key="rtu").strip()
            rp = st.text_input("Password", type="password", key="rtp").strip()
            rc = st.selectbox("Assigned Course", ["BCom", "BMS", "BScIT"], key="rtc")
            ry = st.selectbox("Assigned Year", ["FY", "SY", "TY"], key="rty")
            if st.button("Submit Registration"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Teacher', ?, ?, 0)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Registered! Awaiting admin approval.")
                except:
                    st.error("User already registered.")
        with t3:
            fu = st.text_input("Registered Email", key="ftu").strip()
            fp = st.text_input("New Password", type="password", key="ftp").strip()
            if st.button("Reset Password"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Teacher'", (fp, fu))
                conn.commit()
                st.success("Password Updated!")

    elif portal == "👑 Admin":
        st.markdown("### 👑 Admin Access")
        st.info("💡 Use Username: `9321481833` and Password: `aniKet@1124`")
        t1, t2 = st.tabs(["🔐 Sign In", "🔑 Reset Password"])
        with t1:
            u = st.text_input("Admin Username", key="ad_u").strip()
            p = st.text_input("Password", type="password", key="ad_p").strip()
            if st.button("Sign In to Control Center"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Admin'", (u, p))
                res = c.fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.rerun()
                else:
                    st.error("Invalid Admin Credentials. Please check username & password.")
        with t2:
            ru = st.text_input("Username to Force Reset", key="au").strip()
            rp = st.text_input("New Admin Password", type="password", key="ap").strip()
            if st.button("Update Admin Password"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Admin'", (rp, ru))
                conn.commit()
                st.success("Admin Password Updated! You can now sign in.")

# --- LOGGED-IN DASHBOARDS WITH PROMINENT LOGOUT BUTTON ---
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

    st.sidebar.markdown(f"👤 **User:** `{st.session_state.get('user', '')}`")
    st.sidebar.markdown(f"🏷️ **Role:** `{st.session_state.get('role', '')}`")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("⚙️ Account Settings"):
        npw = st.text_input("Change Password", type="password", key="sb_npw")
        if st.button("Update Password", key="sb_upd"):
            c.execute("UPDATE users SET password=? WHERE username=?", (npw, st.session_state.get('user', '')))
            conn.commit()
            st.success("Password Updated!")

    if st.sidebar.button("🚪 Logout from Sidebar", key="side_logout_btn"):
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.session_state['role'] = None
        st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state.get('role') == "Admin":
        st.title("👑 Master Admin Control Center")
        t_o, t_n, t_d, t_u, t_a, t_c = st.tabs([
            "📊 Overview", "📢 Post Notice", "⚠️ Defaulters", 
            "👥 User List", "✅ Approvals", "📅 Calendar"
        ])
        
        with t_o:
            c.execute("SELECT COUNT(*) FROM attendance")
            att = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
            prs = c.fetchone()[0]
            
            c1, c2 = st.columns(2)
            c1.metric("Total Attendance Logs", att)
            c2.metric("Overall Attendance Rate", f"{(prs/att*100) if att>0 else 0:.1f}%")
            
            st.markdown("---")
            st.subheader("📥 Download Class-Specific Attendance CSV")
            dl_course = st.selectbox("Select Course for Download", ["ALL", "BCom", "BMS", "BScIT"], key="dl_crs")
            dl_year = st.selectbox("Select Year for Download", ["ALL", "FY", "SY", "TY"], key="dl_yr")
            
            q_dl = "SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance WHERE 1=1"
            p_dl = []
            if dl_course != "ALL":
                q_dl += " AND course=?"
                p_dl.append(dl_course)
            if dl_year != "ALL":
                q_dl += " AND year=?"
                p_dl.append(dl_year)
                
            c.execute(q_dl, p_dl)
            recs_dl = c.fetchall()
            
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

        with t_n:
            nc = st.selectbox("Category", ["Notice", "Exam", "Urgent"])
            nt = st.text_input("Notice Title")
            nb = st.text_area("Notice Details")
            crs = st.selectbox("Target Course", ["ALL", "BCom", "BMS", "BScIT"])
            yr = st.selectbox("Target Year", ["ALL", "FY", "SY", "TY"])
            if st.button("🚀 Publish Notice Broadcast"):
                c.execute("INSERT INTO notices (category, title, content, posted_by, role, target_course, target_year, date) VALUES (?, ?, ?, ?, 'Admin', ?, ?, ?)", (nc, nt, nb, st.session_state.get('user', ''), crs, yr, str(datetime.date.today())))
                conn.commit()
                st.success("Notice Published!")
                st.rerun()
            st.markdown("---")
            show_notices(c_user=st.session_state.get('user', ''), u_role="Admin", pfx="adm")

        with t_d:
            st.subheader("⚠️ Low Attendance Report (<75%)")
            c.execute("SELECT username, course, year FROM users WHERE role='Student'")
            stds = c.fetchall()
            d_list = []
            for s in stds:
                c.execute("SELECT status FROM attendance WHERE student_name=?", (s[0],))
                ar = c.fetchall()
                t = len(ar)
                p = sum(1 for x in ar if x[0] == 'Present')
                pct = (p/t*100) if t > 0 else 0
                if pct < 75.0:
                    d_list.append([s[0], s[1], s[2], t, p, f"{pct:.1f}%"])
            if d_list:
                df_def = pd.DataFrame(d_list, columns=["Student", "Course", "Year", "Total", "Attended", "Percentage"])
