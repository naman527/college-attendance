import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random

# --- SECURE DATABASE SETUP ---
conn = sqlite3.connect('college_attendance.db', check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, course TEXT, year TEXT, is_approved INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS attendance (student_name TEXT, course TEXT, year TEXT, subject TEXT, date TEXT, month TEXT, status TEXT, marked_by TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, content TEXT, file_data BLOB, file_name TEXT, posted_by TEXT, role TEXT, target_course TEXT, target_year TEXT, date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS holidays (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, date TEXT, category TEXT)")

# Schema Migrations
c.execute("PRAGMA table_info(notices)")
n_cols = [col[1] for col in c.fetchall()]
if 'file_data' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN file_data BLOB")
if 'file_name' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN file_name TEXT")
if 'category' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN category TEXT DEFAULT 'Notice'")

c.execute("PRAGMA table_info(attendance)")
a_cols = [col[1] for col in c.fetchall()]
if 'month' not in a_cols:
    c.execute("ALTER TABLE attendance ADD COLUMN month TEXT")
if 'subject' not in a_cols:
    c.execute("ALTER TABLE attendance ADD COLUMN subject DEFAULT 'General'")

conn.commit()

# Default Master Admin (Only Admin Account)
c.execute("INSERT INTO users (username, password, role, course, year, is_approved) VALUES ('naman@1125', 'aniKet@124', 'Admin', 'ALL', 'ALL', 1) ON CONFLICT(username) DO UPDATE SET password='aniKet@124', is_approved=1")
conn.commit()

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Student during exam: Is this a trick question?\nProfessor: No, it is a test of your ability to answer questions you have never seen before.",
    "Why was the computer late for class? It had a hard drive!",
    "Teacher: Name two elements on the periodic table.\nStudent: Unobtanium and surprise elements!",
    "Why don't college students like math? Because it has too many problems!",
    "There are 10 types of people in the world: Those who understand binary, and those who don't.",
    "Why did the student bring a ladder to college? To get to high school levels of success!",
    "Professor: Write a program that prints Hello World.\nStudent: *Spends 3 hours fixing semicolon errors*"
]

# --- HELPER FUNCTIONS WITH STRICT PERMISSIONS ---
def get_shortfall_message(presents, total):
    if total == 0:
        return "No lectures recorded yet."
    pct = (presents / total) * 100
    if pct >= 75.0:
        return "Target achieved! You are above the 75% attendance mark."
    needed = (3 * total) - (4 * presents)
    return f"You need to attend the next {max(0, needed)} consecutive lectures to reach 75%."

def show_notice_board(target_course="ALL", target_year="ALL", current_user="", user_role="", key_prefix=""):
    st.subheader("Announcements & Notices")
    c_filter = st.selectbox("Filter Category", ["ALL", "Notice", "Timetable", "Exam Schedule", "Urgent"], key=f"cat_{key_prefix}")
    
    q = "SELECT id, category, title, content, file_data, file_name, posted_by, role, date, target_course, target_year FROM notices WHERE 1=1"
    params = []
    if c_filter != "ALL":
        q += " AND category=?"
        params.append(c_filter)
    if target_course != "ALL":
        q += " AND (target_course=? OR target_course='ALL')"
        params.append(target_course)
    if target_year != "ALL":
        q += " AND (target_year=? OR target_year='ALL')"
        params.append(target_year)
    q += " ORDER BY id DESC"
    
    c.execute(q, params)
    notices = c.fetchall()
    if notices:
        for n in notices:
            with st.expander(f"[{n[1]}] {n[2]} - ({n[8]})", expanded=True):
                st.write(n[3])
                if n[4] and n[5]:
                    st.download_button(f"Download File: {n[5]}", data=n[4], file_name=n[5], key=f"dl_{n[0]}_{key_prefix}")
                st.caption(f"Posted by: {n[6]} ({n[7]}) | Target: {n[9]} {n[10]}")
                
                # RESTRICTED: Only Admin or the Teacher who posted can delete
                if user_role == "Admin" or (user_role == "Teacher" and n[6] == current_user):
                    if st.button("Delete Notice", key=f"del_{n[0]}_{key_prefix}"):
                        c.execute("DELETE FROM notices WHERE id=?", (n[0],))
                        conn.commit()
                        st.success("Notice deleted successfully.")
                        st.rerun()
    else:
        st.info("No notices available.")

def show_calendar(user_role=""):
    st.subheader("Academic Calendar")
    
    # RESTRICTED: Only Admin can add events
    if user_role == "Admin":
        with st.expander("➕ Add Event / Holiday (Admin Only)"):
            h_title = st.text_input("Event Name", key="htitle")
            h_date = st.date_input("Date", datetime.date.today(), key="hdate")
            h_cat = st.selectbox("Category", ["Official Holiday", "Exam Event", "Cultural / Sports", "Vacation"], key="hcat")
            if st.button("Save Event"):
                if h_title:
                    c.execute("INSERT INTO holidays (title, date, category) VALUES (?, ?, ?)", (h_title, str(h_date), h_cat))
                    conn.commit()
                    st.success("Event added!")
                    st.rerun()

    c.execute("SELECT id, title, date, category FROM holidays ORDER BY date ASC")
    events = c.fetchall()
    if events:
        df = pd.DataFrame(events, columns=["ID", "Event", "Date", "Category"])
        st.dataframe(df[["Event", "Date", "Category"]], use_container_width=True)
        
        # RESTRICTED: Only Admin can delete events
        if user_role == "Admin":
            del_id = st.selectbox("Select Event ID to Delete", [e[0] for e in events])
            if st.button("Delete Event"):
                c.execute("DELETE FROM holidays WHERE id=?", (del_id,))
                conn.commit()
                st.success("Event deleted.")
                st.rerun()
    else:
        st.info("No academic events scheduled.")

# --- APP LAYOUT ---
st.set_page_config(page_title="College Management Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

if 'joke' not in st.session_state:
    st.session_state['joke'] = random.choice(JOKES)

st.sidebar.title("🔐 College Portal")

# --- LOGIN & AUTHENTICATION ---
if not st.session_state['logged_in']:
    portal = st.sidebar.radio("Choose Portal", ["Admin Portal", "Teacher Portal", "Student Portal"])

    if portal == "Admin Portal":
        st.title("🛡️ Admin Secure Access")
        st.caption("Authorized administrative access only.")
        t1, t2 = st.tabs(["Admin Login", "Reset Password"])
        with t1:
            u = st.text_input("Admin Username").strip()
            p = st.text_input("Admin Password", type="password").strip()
            if st.button("Login as Admin", type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Admin'", (u, p))
                res = c.fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.rerun()
                else:
                    st.error("Invalid Admin Credentials.")
        with t2:
            ru = st.text_input("Admin Username", key="rau").strip()
            rp = st.text_input("New Password", type="password", key="rap").strip()
            if st.button("Reset Admin Password"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Admin'", (rp, ru))
                conn.commit()
                st.success("Admin password updated successfully.")

    elif portal == "Teacher Portal":
        st.title("👨‍🏫 Teacher Access")
        t1, t2, t3 = st.tabs(["Sign In", "New Registration", "Forgot Password"])
        with t1:
            u = st.text_input("Teacher Email/Username", key="tu").strip()
            p = st.text_input("Password", type="password", key="tp").strip()
            if st.button("Teacher Sign In", type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Teacher'", (u, p))
                res = c.fetchone()
                if res:
                    if res[5] == 0:
                        st.warning("Your account is pending Admin approval.")
                    else:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = res[0]
                        st.session_state['role'] = res[2]
                        st.session_state['course'] = res[3]
                        st.session_state['year'] = res[4]
                        st.rerun()
                else:
                    st.error("Invalid credentials.")
        with t2:
            ru = st.text_input("Teacher Email/Username", key="rtu").strip()
            rp = st.text_input("Choose Password", type="password", key="rtp").strip()
            rc = st.selectbox("Department Course", ["BCom", "BMS", "BScIT"], key="rtc")
            ry = st.selectbox("Assigned Year", ["FY", "SY", "TY"], key="rty")
            if st.button("Submit Registration"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Teacher', ?, ?, 0)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Registration submitted! Pending Admin verification.")
                except:
                    st.error("Username already registered.")
        with t3:
            fu = st.text_input("Teacher Email", key="ftu").strip()
            fp = st.text_input("New Password", type="password", key="ftp").strip()
            if st.button("Reset Password"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Teacher'", (fp, fu))
                conn.commit()
                st.success("Password updated!")

    elif portal == "Student Portal":
        st.title("🎓 Student Portal")
        t1, t2, t3 = st.tabs(["Sign In", "Register Account", "Forgot Password"])
        with t1:
            u = st.text_input("Student Email/Username", key="su").strip()
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
                    st.error("Invalid student credentials.")
        with t2:
            ru = st.text_input("Student Email/Username", key="rsu").strip()
            rp = st.text_input("Choose Password", type="password", key="rsp").strip()
            rc = st.selectbox("Enrolled Course", ["BCom", "BMS", "BScIT"], key="rsc")
            ry = st.selectbox("Current Year", ["FY", "SY", "TY"], key="rsy")
            if st.button("Create Account"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Student', ?, ?, 1)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Account created successfully! You can sign in now.")
                except:
                    st.error("Student username already exists.")
        with t3:
            fu = st.text_input("Student Email", key="fsu").strip()
            fp = st.text_input("New Password", type="password", key="fsp").strip()
            if st.button("Reset Password"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Student'", (fp, fu))
                conn.commit()
                st.success("Password updated!")

# --- LOGGED-IN PROTECTED AREA ---
else:
    st.sidebar.markdown(f"**User Logged:** `{st.session_state['user']}`")
    st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("⚙️ Account Settings"):
        npw = st.text_input("Change Password", type="password")
        if st.button("Update Password"):
            c.execute("UPDATE users SET password=? WHERE username=?", (npw, st.session_state['user']))
            conn.commit()
            st.success("Password updated!")

    if st.sidebar.button("Log Out", type="secondary"):
        st.session_state['logged_in'] = False
        st.rerun()

    # -------------------------------------------------------------
    # 👑 MASTER ADMIN DASHBOARD (ADMIN ONLY)
    # -------------------------------------------------------------
    if st.session_state['role'] == "Admin":
        st.title("👑 Master Admin Management Control")
        t_overview, t_notices, t_defaulters, t_users, t_app, t_cal = st.tabs([
            "Global Overview", "Broadcast Notice", "Defaulters List", "User Registry", "Teacher Approvals", "Academic Calendar"
        ])
        
        with t_overview:
            c.execute("SELECT COUNT(*) FROM users WHERE role='Student'")
            st_cnt = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM attendance")
            att_cnt = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
            pr_cnt = c.fetchone()[0]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Students", st_cnt)
            c2.metric("Lectures Recorded", att_cnt)
            c3.metric("Total Presents", pr_cnt)
            c4.metric("Global Attendance Avg", f"{(pr_cnt/att_cnt*100) if att_cnt>0 else 0:.1f}%")
            
            st.markdown("---")
            fc = st.selectbox("Course Filter", ["ALL", "BCom", "BMS", "BScIT"])
            fy = st.selectbox("Year Filter", ["ALL", "FY", "SY", "TY"])
            
            q = "SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance WHERE 1=1"
            params = []
            if fc != "ALL":
                q += " AND course=?"
                params.append(fc)
            if fy != "ALL":
                q += " AND year=?"
                params.append(fy)
            c.execute(q, params)
            recs = c.fetchall()
            if recs:
                df = pd.DataFrame(recs, columns=["Student", "Course", "Year", "Subject", "Date", "Month", "Status", "Teacher"])
                st.dataframe(df, use_container_width=True)

        with t_notices:
            nt_cat = st.selectbox("Notice Category", ["Notice", "Timetable", "Exam Schedule", "Urgent"])
            nt_title = st.text_input("Notice Title")
            nt_body = st.text_area("Notice Body / Details")
            nt_file = st.file_uploader("Attach PDF/Image")
            nt_crs = st.selectbox("Target Course", ["ALL", "BCom", "BMS", "BScIT"])
            nt_yr = st.selectbox("Target Year", ["ALL", "FY", "SY", "TY"])
            if st.button("Publish Global Notice", type="primary"):
                fb = nt_file.read() if nt_file else None
                fn = nt_file.name if nt_file else None
                c.execute("INSERT INTO notices (category, title, content, file_data, file_name, posted_by, role, target_course, target_year, date) VALUES (?, ?, ?, ?, ?, ?, 'Admin', ?, ?, ?)",
                          (nt_cat, nt_title, nt_body, fb, fn, st.session_state['user'], nt_crs, nt_yr, str(datetime.date.today())))
                conn.commit()
                st.success("Notice published!")
                st.rerun()
            st.markdown("---")
            show_notice_board(current_user=st.session_state['user'], user_role="Admin", key_prefix="adm")

        with t_defaulters:
            c.execute("SELECT username, course, year FROM users WHERE role='Student'")
            students = c.fetchall()
            def_list = []
            for s in students:
                c.execute("SELECT status FROM attendance WHERE student_name=?", (s[0],))
                ar = c.fetchall()
                tot = len(ar)
                pr = sum(1 for x in ar if x[0] == 'Present')
                pct = (pr/tot*100) if tot > 0 else 0
                if pct < 75.0:
                    def_list.append([s[0], s[1], s[2], tot, pr, f"{pct:.1f}%"])
            if def_list:
                st.dataframe(pd.DataFrame(def_list, columns=["Student", "Course", "Year", "Total", "Attended", "Percentage"]), use_container_width=True)
            else:
                st.success("No defaulters (<75%) found!")

        with t_users:
            st.subheader("Manage System Accounts")
            c.execute("SELECT username, role, course, year, is_approved FROM users")
            all_users = pd.DataFrame(c.fetchall(), columns=["Username", "Role", "Course", "Year", "Approved"])
            st.dataframe(all_users, use_container_width=True)
            
            st.markdown("---")
            user_del = st.selectbox("Select Account to Delete", [u for u in all_users['Username'] if u != 'naman@1125'])
            if st.button("Delete Selected Account", type="primary"):
                c.execute("DELETE FROM users WHERE username=?", (user_del,))
                c.execute("DELETE FROM attendance WHERE student_name=?", (user_del,))
                conn.commit()
                st.success(f"Account '{user_del}' removed.")
                st.rerun()

        with t_app:
            st.subheader("Pending Teacher Registration Requests")
            c.execute("SELECT username, course, year FROM users WHERE role='Teacher' AND is_approved=0")
            p = c.fetchall()
            if p:
                st.dataframe(pd.DataFrame(p, columns=["Teacher Email", "Course", "Year"]), use_container_width=True)
                sel_t = st.selectbox("Approve Teacher Account", [x[0] for x in p])
                if st.button("Approve Selected Teacher"):
                    c.execute("UPDATE users SET is_approved=1 WHERE username=?", (sel_t,))
                    conn.commit()
                    st.success("Teacher account approved!")
                    st.rerun()
            else:
                st.info("No pending teacher approvals.")

        with t_cal:
            show_calendar(user_role="Admin")

    # -------------------------------------------------------------
    # 👨‍🏫 TEACHER WORKSTATION (TEACHER ONLY)
    # -------------------------------------------------------------
    elif st.session_state['role'] == "Teacher":
        st.title(f"👨‍🏫 Teacher Workstation ({st.session_state['course']} - {st.session_state['year']})")
        t_mark, t_notices, t_rep, t_cal = st.tabs(["Mark Attendance", "Class Notices", "Class Analytics", "Calendar"])
        
        with t_mark:
            ldate = st.date_input("Date of Lecture", datetime.date.today())
            lsubj = st.text_input("Subject Name", "General")
            lmonth = ldate.strftime("%B %Y")
            
            c.execute("SELECT username FROM users WHERE role='Student' AND course=? AND year=?", (st.session_state['course'], st.session_state['year']))
            st_list = [x[0] for x in c.fetchall()]
            
            if st_list:
                marks = {}
                for s in st_list:
                    marks[s] = st.radio(f"Student: {s}", ["Present", "Absent"], key=s, horizontal=True)
                if st.button("Save & Submit A
