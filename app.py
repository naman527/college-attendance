import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Campus Portal",
    layout="wide",
    page_icon="🎓"
)

# --- ADVANCED UI & PRIVACY STYLING ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* HIDE STREAMLIT BRANDING, GITHUB LINK & FORK BUTTON */
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
div[data-testid="stToolbar"] {visibility: hidden !important;}
div[data-testid="stDecoration"] {visibility: hidden !important;}
div[data-testid="stStatusWidget"] {visibility: hidden !important;}
button[title="View app source"] {display: none !important;}
.viewerBadge_container__1S-5D {display: none !important;}
a[href*="github.com"] {display: none !important;}

/* Font and Dark Theme */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #0f172a;
    color: #f8fafc;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #1e293b !important;
    border-right: 1px solid #334155;
}

/* Metric Cards */
div[data-testid="metric-container"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
}

div[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #818cf8 !important;
}

div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-weight: 600 !important;
}

/* High-Contrast Mobile-Friendly Buttons */
.stButton > button {
    width: 100% !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 12px 20px !important;
    border: none !important;
    transition: all 0.25s ease-in-out !important;
    box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.3) !important;
}

/* Primary Button Styling */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.5) !important;
}

/* Secondary Button Styling */
.stButton > button[kind="secondary"] {
    background-color: #334155 !important;
    color: #f8fafc !important;
    border: 1px solid #475569 !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #475569 !important;
    transform: translateY(-2px) !important;
}

/* Form Inputs for iPhone & Touch Displays */
.stTextInput > div > div > input, 
.stSelectbox > div > div, 
.stTextArea > div > div > textarea {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-size: 16px !important; /* Prevents auto-zoom on iOS */
}

.stTextInput > div > div > input:focus, 
.stSelectbox > div > div:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border-radius: 12px !important;
    border: 1px solid #334155 !important;
    font-weight: 600 !important;
}

/* Navigation Tabs */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 8px 16px !important;
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

# Database Migrations
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

# Master Admin Account Setup
c.execute("""
INSERT INTO users (
    username, password, role, course, year, is_approved
) VALUES (
    'naman@1125', 'aniKet@124', 'Admin', 'ALL', 'ALL', 1
) ON CONFLICT(username) DO UPDATE SET 
    password='aniKet@124', is_approved=1
""")
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
    return f"⚠️ Attend the next {max(0, needed)} lectures continuously to reach 75%."

def show_notices(t_crs="ALL", t_yr="ALL", c_user="", u_role="", pfx=""):
    st.subheader("📢 Class Notices & Updates")
    c_flt = st.selectbox(
        "Filter Category",
        ["ALL", "Notice", "Exam", "Urgent"],
        key=f"c_{pfx}"
    )
    
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
                    st.download_button(
                        "📎 Download Attachment",
                        data=n[4],
                        file_name=n[5],
                        key=f"dl_{n[0]}_{pfx}",
                        type="secondary"
                    )
                st.caption(f"Posted by: {n[6]} ({n[7]})")
                if u_role == "Admin" or (u_role == "Teacher" and n[6] == c_user):
                    if st.button("🗑️ Delete Notice", key=f"del_{n[0]}_{pfx}", type="secondary"):
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
            if st.button("💾 Save Event", type="primary"):
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
            if st.button("🗑️ Remove Event", type="secondary"):
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

st.sidebar.title("🏛️ Campus Portal")

if not st.session_state['logged_in']:
    portal = st.sidebar.radio("Select Portal", ["👑 Admin", "👨‍🏫 Teacher", "🎓 Student"])

    if portal == "👑 Admin":
        st.title("👑 Admin Access Control")
        t1, t2 = st.tabs(["🔐 Sign In", "🔑 Reset Password"])
        with t1:
            u = st.text_input("Admin Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.button("Sign In to Control Center", type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Admin'", (u, p))
                res = c.fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.rerun()
                else:
                    st.error("Invalid Admin Credentials")
        with t2:
            ru = st.text_input("Username", key="au").strip()
            rp = st.text_input("New Password", type="password", key="ap").strip()
            if st.button("Update Admin Password", type="primary"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Admin'", (rp, ru))
                conn.commit()
                st.success("Password Updated!")

    elif portal == "👨‍🏫 Teacher":
        st.title("👨‍🏫 Faculty Portal")
        t1, t2, t3 = st.tabs(["🔐 Sign In", "📝 Register Account", "🔑 Reset Password"])
        with t1:
            u = st.text_input("Teacher Email", key="tu").strip()
            p = st.text_input("Password", type="password", key="tp").strip()
            if st.button("Teacher Sign In", type="primary"):
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
            if st.button("Submit Registration", type="primary"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Teacher', ?, ?, 0)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Registered! Awaiting admin approval.")
                except:
                    st.error("User already registered.")
        with t3:
            fu = st.text_input("Registered Email", key="ftu").strip()
            fp = st.text_input("New Password", type="password", key="ftp").strip()
            if st.button("Reset Password", type="primary"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Teacher'", (fp, fu))
                conn.commit()
                st.success("Password Updated!")

    elif portal == "🎓 Student":
        st.title("🎓 Student Portal")
        t1, t2, t3 = st.tabs(["🔐 Sign In", "📝 Create Account", "🔑 Reset Password"])
        with t1:
            u = st.text_input("Student Email", key="su").strip()
            p = st.text_input("Password", type="password", key="sp").strip()
            if st.button("Student Sign In", type="primary"):
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
            if st.button("Create Account", type="primary"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Student', ?, ?, 1)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Account Created! Sign in now.")
                except:
                    st.error("User already exists.")
        with t3:
            fu = st.text_input("Registered Email", key="fsu").strip()
            fp = st.text_input("New Password", type="password", key="fsp").strip()
            if st.button("Reset Password", type="primary"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Student'", (fp, fu))
                conn.commit()
                st.success("Password Updated!")

else:
    st.sidebar.markdown(f"👤 **User:** `{st.session_state.get('user', '')}`")
    st.sidebar.markdown(f"🏷️ **Role:** `{st.session_state.get('role', '')}`")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("⚙️ Account Settings"):
        npw = st.text_input("Change Password", type="password")
        if st.button("Update Password", type="primary"):
            c.execute("UPDATE users SET password=? WHERE username=?", (npw, st.session_state.get('user', '')))
            conn.commit()
            st.success("Updated!")

    if st.sidebar.button("🚪 Logout", type="secondary"):
        st.session_state['logged_in'] = False
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
            c.execute("SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance")
            recs = c.fetchall()
            if recs:
                df_att = pd.DataFrame(recs, columns=["Student", "Course", "Year", "Subject", "Date", "Month", "Status", "Teacher"])
                st.dataframe(df_att, use_container_width=True)
                
                csv = df_att.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Attendance Records (CSV)",
                    data=csv,
                    file_name="all_attendance_logs.csv",
                    mime="text/csv",
                    type="primary"
                )

        with t_n:
            nc = st.selectbox("Category", ["Notice", "Exam", "Urgent"])
            nt = st.text_input("Notice Title")
            nb = st.text_area("Notice Details")
            crs = st.selectbox("Target Course", ["ALL", "BCom", "BMS", "BScIT"])
            yr = st.selectbox("Target Year", ["ALL", "FY", "SY", "TY"])
            if st.button("🚀 Publish Notice Broadcast", type="primary"):
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
                st.dataframe(df_def, use_container_width=True)
            else:
                st.success("🎉 No defaulters found!")

        with t_u:
            st.subheader("👥 System User Management")
            c.execute("SELECT username, role, course, year, is_approved FROM users")
            all_u = pd.DataFrame(c.fetchall(), columns=["User", "Role", "Course", "Year", "Approved"])
            st.dataframe(all_u, use_container_width=True)
            
            udel = st.selectbox("Select User Account to Delete", [u for u in all_u['User'] if u != 'naman@1125'])
            if st.button("🗑️ Delete Selected User Account", type="primary"):
                c.execute("DELETE FROM users WHERE username=?", (udel,))
                conn.commit()
                st.success("User Deleted!")
                st.rerun()

        with t_a:
            st.subheader("✅ Pending Teacher Registrations")
