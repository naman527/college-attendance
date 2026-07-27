import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random

# -------------------------------------------------------------
# DATABASE SETUP & AUTOMATIC MIGRATION
# -------------------------------------------------------------
conn = sqlite3.connect('college_attendance.db', check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, course TEXT, year TEXT, is_approved INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS attendance (student_name TEXT, course TEXT, year TEXT, subject TEXT, date TEXT, month TEXT, status TEXT, marked_by TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, content TEXT, file_data BLOB, file_name TEXT, posted_by TEXT, role TEXT, target_course TEXT, target_year TEXT, date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS holidays (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, date TEXT, category TEXT)")

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

c.execute("INSERT INTO users (username, password, role, course, year, is_approved) VALUES ('naman@1125', 'aniKet@124', 'Admin', 'ALL', 'ALL', 1) ON CONFLICT(username) DO UPDATE SET password='aniKet@124', is_approved=1")
conn.commit()

# -------------------------------------------------------------
# HELPER FUNCTIONS & JOKES DATASET
# -------------------------------------------------------------
COLLEGE_JOKES = [
    "Why do programmers prefer dark mode?\nBecause light attracts bugs!",
    "Student during exam: 'Is this a trick question?'\nProfessor: 'No, it's a test of your ability to answer questions you've never seen before.'",
    "Why was the computer late for class?\nIt had a hard drive!",
    "Teacher: 'Name two elements on the periodic table.'\nStudent: 'Unobtanium and surprise elements!'",
    "A student's favorite state of matter? Liquid, because everything flows when deadline approaches!",
    "There are 10 types of people in the world: Those who understand binary, and those who don't.",
    "Why did the student bring a ladder to college?\nTo get to high school levels of success!",
    "Professor: 'Write a program that prints Hello World.'\nStudent: *Spends 3 hours fixing semicolon errors*",
    "Why don't college students like math?\nBecause it has too many problems!",
    "How do you tell an extroverted computer scientist?\nThey look at YOUR shoes when talking to you!",
    "Why was the attendance sheet so popular?\nBecause everybody wanted to be present for it!",
    "What is a student's favorite dance move?\nThe Last-Minute Crunch!"
]

def calculate_75_shortfall(presents, total):
    if total == 0:
        return 0, "No lectures recorded yet."
    
    current_pct = (presents / total) * 100
    if current_pct >= 75.0:
        return 0, "Target Achieved! You are comfortably at or above 75% attendance."
    
    needed = (3 * total) - (4 * presents)
    return max(0, needed), f"You need to attend the next {needed} consecutive lecture(s) to reach 75%."

def render_notice_board(target_course="ALL", target_year="ALL", current_user="", user_role="", key_suffix=""):
    st.markdown("### Notices & Announcements")
    
    cat_filter = st.selectbox("Filter Category", ["ALL", "Notice", "Timetable", "Exam Schedule", "Urgent"], key=f"cat_fltr_{key_suffix}")
    
    query = "SELECT id, category, title, content, file_data, file_name, posted_by, role, date, target_course, target_year FROM notices WHERE 1=1"
    params = []
    
    if cat_filter != "ALL":
        query += " AND category=?"
        params.append(cat_filter)
        
    if target_course != "ALL":
        query += " AND (target_course=? OR target_course='ALL')"
        params.append(target_course)
    if target_year != "ALL":
        query += " AND (target_year=? OR target_year='ALL')"
        params.append(target_year)
        
    query += " ORDER BY id DESC"
    
    c.execute(query, params)
    notices = c.fetchall()
    
    if notices:
        for n_id, category, title, content, file_data, file_name, posted_by, role, date_posted, tc, ty in notices:
            with st.expander(f"[{category.upper()}] {title} - ({date_posted})", expanded=True):
                st.write(content)
                
                if file_data and file_name:
                    st.download_button(
                        label=f"Download Attachment: {file_name}",
                        data=file_data,
                        file_name=file_name,
                        key=f"dl_{n_id}_{key_suffix}"
                    )
                    
                col_cap, col_del = st.columns([3, 1])
                with col_cap:
                    st.caption(f"Posted by {posted_by} ({role}) | Target: {tc} - {ty}")
                
                with col_del:
                    if user_role == "Admin" or (user_role == "Teacher" and posted_by == current_user):
                        if st.button("Delete Notice", key=f"del_n_{n_id}_{key_suffix}"):
                            c.execute("DELETE FROM notices WHERE id=?", (n_id,))
                            conn.commit()
                            st.success("Deleted!")
                            st.rerun()
    else:
        st.info("No announcements found for this section.")

def render_holiday_calendar(user_role=""):
    st.markdown("### College Calendar & Holiday Schedule")
    
    if user_role == "Admin":
        with st.expander("Add Event or Holiday"):
            h_title = st.text_input("Event Title", key="h_title")
            h_date = st.date_input("Date", datetime.date.today(), key="h_date")
            h_cat = st.selectbox("Category", ["Official Holiday", "Exam Event", "Cultural / Sports", "Vacation"], key="h_cat")
            
            if st.button("Save Event"):
                if h_title:
                    c.execute("INSERT INTO holidays (title, date, category) VALUES (?, ?, ?)", (h_title, str(h_date), h_cat))
                    conn.commit()
                    st.success("Event Added!")
                    st.rerun()
                else:
                    st.warning("Please provide a title.")

    c.execute("SELECT id, title, date, category FROM holidays ORDER BY date ASC")
    holidays = c.fetchall()
    
    if holidays:
        df_h = pd.DataFrame(holidays, columns=["ID", "Event / Holiday Name", "Date", "Category"])
        st.dataframe(df_h[["Event / Holiday Name", "Date", "Category"]], use_container_width=True)
        
        if user_role == "Admin":
            h_del_id = st.selectbox("Select Event to Remove", [h[0] for h in holidays], format_func=lambda x: f"ID {x}")
            if st.button("Delete Selected Event"):
                c.execute("DELETE FROM holidays WHERE id=?", (h_del_id,))
                conn.commit()
                st.success("Event removed!")
                st.rerun()
    else:
        st.info("No upcoming calendar events scheduled.")

# -------------------------------------------------------------
# APP CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(page_title="College Attendance Portal", layout="wide", initial_sidebar_state="expanded")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

if 'current_joke' not in st.session_state:
    st.session_state['current_joke'] = random.choice(COLLEGE_JOKES)

st.sidebar.title("Campus Portal")

# -------------------------------------------------------------
# LOGIN & REGISTRATION PORTALS
# -------------------------------------------------------------
if not st.session_state['logged_in']:
    portal_choice = st.sidebar.radio("Select Portal", ["Admin Login", "Teacher Portal", "Student Portal"])

    if portal_choice == "Admin Login":
        st.title("Admin Access Control")
        st.caption("Secure administrative management system.")
        
        tab1, tab2 = st.tabs(["Admin Sign In", "Reset Password"])
        
        with tab1:
            admin_user = st.text_input("Admin Username").strip()
            admin_pass = st.text_input("Admin Password", type="password").strip()
            
            if st.button("Sign In", type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Admin'", (admin_user, admin_pass))
                user = c.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user[0]
                    st.session_state['role'] = user[2]
                    st.success("Welcome back, Admin!")
                    st.rerun()
                else:
                    st.error("Invalid Admin credentials.")
                    
        with tab2:
            st.markdown("### Reset Admin Account Password")
            reset_admin_user = st.text_input("Admin Username", key="fp_admin_user").strip()
            new_admin_pass = st.text_input("New Password", type="password", key="fp_admin_pass").strip()
            
            if st.button("Update Password"):
                if reset_admin_user and new_admin_pass:
                    c.execute("SELECT * FROM users WHERE username=? AND role='Admin'", (reset_admin_user,))
                    if c.fetchone():
                        c.execute("UPDATE users SET password=? WHERE username=? AND role='Admin'", (new_admin_pass, reset_admin_user))
                        conn.commit()
                        st.success("Admin password reset successfully! You can now log in.")
                    else:
                        st.error("Admin user not found.")
                else:
                    st.warning("Please fill in all fields.")

    elif portal_choice == "Teacher Portal":
        st.title("Teacher Management Portal")
        tab1, tab2, tab3 = st.tabs(["Sign In", "New Registration", "Reset Password"])
        
        with tab1:
            t_user = st.text_input("Teacher Email or Username", key="t_login_user").strip()
            t_pass = st.text_input("Password", type="password", key="t_login_pass").strip()
            
            if st.button("Sign In", type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Teacher'", (t_user, t_pass))
                user = c.fetchone()
                if user:
                    if user[5] == 0:
                        st.warning("Your account is pending approval by the Admin.")
                    else:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = user[0]
                        st.session_state['role'] = user[2]
                        st.session_state['course'] = user[3]
                        st.session_state['year'] = user[4]
                        st.success("Teacher login successful!")
                        st.rerun()
                else:
                    st.error("Invalid Teacher credentials.")
                    
        with tab2:
            reg_t_user = st.text_input("Work Email / Username", key="t_reg_user_new").strip()
            reg_t_pass = st.text_input("Choose Password", type="password", key="t_reg_pass_new").strip()
            t_course = st.selectbox("Department Course", ["BCom", "BMS", "BScIT"], key="t_reg_course_new")
            t_year = st.selectbox("Assigned Academic Year", ["FY", "SY", "TY"], key="t_reg_year_new")
            
            if st.button("Submit Registration"):
                if reg_t_user and reg_t_pass:
                    try:
                        c.execute("INSERT INTO users (username, password, role, course, year, is_approved) VALUES (?, ?, 'Teacher', ?, ?, 0)", (reg_t_user, reg_t_pass, t_course, t_year))
                        conn.commit()
                        st.success("Registration submitted! Pending Admin verification.")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists!")
                else:
                    st.warning("Please complete all required fields.")
                    
        with tab3:
            st.markdown("### Recover Teacher Account Password")
            fp_t_user = st.text_input("Teacher Email / Username", key="fp_t_user").strip()
            fp_t_course = st.selectbox("Department Course", ["BCom", "BMS", "BScIT"], key="fp_t_crs")
            fp_t_new_pass = st.text_input("New Password", type="password", key="fp_t_pass").strip()
            
            if st.button("Reset Password"):
                if fp_t_user and fp_t_new_pass:
                    c.execute("SELECT * FROM users WHERE username=? AND course=? AND role='Teacher'", (fp_t_user, fp_t_course))
                    if c.fetchone():
                        c.execute("UPDATE users SET password=? WHERE username=? AND role='Teacher'", (fp_t_new_pass, fp_t_user))
                        conn.commit()
                        st.success("Password successfully updated! You may sign in.")
                    else:
                        st.error("Matching record not found.")
                else:
                    st.warning("Please fill in all fields.")

    elif portal_choice == "Student Portal":
        st.title("Student Learning Portal")
        tab1, tab2, tab3 = st.tabs(["Sign In", "New Student Registration", "Reset Password"])
        
        with tab1:
            s_user = st.text_input("Student Email or Username", key="s_login_user").strip()
            s_pass = st.text_input("Password", type="password", key="s_login_pass").strip()
            
            if st.button("Sign In", type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Student'", (s_user, s_pass))
                user = c.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user[0]
                    st.session_state['role'] = user[2]
                    st.session_state['course'] = user[3]
                    st.session_state['year'] = user[4]
                    st.success("Welcome back!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                    
        with tab2:
            reg_s_user = st.text_input("Student Email / Username", key="s_reg_user_new").strip()
            reg_s_pass = st.text_input("Choose Password", type="password", key="s_reg_pass_new").strip()
            s_course = st.selectbox("Enrolled Course", ["BCom", "BMS", "BScIT"], key="s_reg_course_new")
            s_year = st.selectbox("Current Year", ["FY", "SY", "TY"], key="s_reg_year_new")
            
            if st.button("Create Student Account"):
                if reg_s_user and reg_s_pass:
                    try:
                        c.execute("INSERT INTO users (username, password, role, course, year, is_approved) VALUES (?, ?, 'Student', ?, ?, 1)", (reg_s_user, reg_s_pass, s_course, s_year))
                        conn.commit()
                        st.success("Account created! You can sign in immediately.")
                    except sqlite3.IntegrityError:
                        st.error("Username already registered!")
                else:
                    st.warning("Please fill out all fields.")
                    
        with tab3:
            st.markdown("### Recover Student Account")
            fp_s_user = st.text_input("Student Email / Username", key="fp_s_user").strip()
            fp_s_course = st.selectbox("Enrolled Course", ["BCom", "BMS", "BScIT"], key="fp_s_crs")
            fp_s_new_pass = st.text_input("New Password", type="password", key="fp_s_pass").strip()
            
            if st.button("Reset Password"):
                if fp_s_user and fp_s_new_pass:
                    c.execute("SELECT * FROM users WHERE username=? AND course=? AND role='Student'", (fp_s_user, fp_s_course))
                    if c.fetchone():
                        c.execute("UPDATE users SET password=? WHERE username=? AND role='Student'", (fp_s_new_pass, fp_s_user))
                        conn.commit()
                        st.success("Password reset successfully! Please sign in.")
                    else:
                        st.error("Record not found.")
                else:
                    st.warning("Please fill in all fields.")

# -------------------------------------------------------------
# LOGGED-IN DASHBOARDS
# -------------------------------------------------------------
else:
    st.sidebar.markdown(f"**Logged User:** `{st.session_state['user']}`")
    st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("Security Options"):
        new_pw = st.text_input("New Password", type="password", key="chg_pw")
        if st.button("Update Password"):
            if new_pw:
                c.execute("UPDATE users SET password=? WHERE username=?", (new_pw, st.session_state['user']))
                conn.commit()
                st.success("Password updated!")
            else:
                st.warning("Enter a valid password.")
                
    if st.sidebar.button("Log Out", type="secondary"):
        st.session_state['logged_in'] = False
        st.rerun()

    if st.session_state['role'] == "Admin":
        st.title("Master Administrative Hub")
        
        tab_stats, tab_notice, tab_defaulters, tab_users, tab_approvals, tab_calendar = st.tabs([
            "Global Overview", 
            "Announcements & Timetables",
            "Defaulters List (<75%)", 
            "User Records", 
            "Teacher Approvals",
            "Academic Calendar"
        ])

        with tab_stats:
            st.markdown("### System Key Metrics")
            
            c.execute("SELECT COUNT(*) FROM users WHERE role='Student'")
            total_students = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM attendance")
            total_records = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
            total_presents = c.fetchone()[0]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Enrolled Students", total_students)
            col2.metric("Lectures Recorded", total_records)
            col3.metric("Presents Logged", total_presents)
            overall_pct = (total_presents / total_records * 100) if total_records > 0 else 0
            col4.metric("Average Attendance", f"{overall_pct:.1f}%")

            st.markdown("---")
            st.markdown("### Search & Filter Attendance Database")
            
            col_fc, col_fy = st.columns(2)
            with col_fc:
                filter_course = st.selectbox("Course Filter", ["ALL", "BCom", "BMS", "BScIT"])
            with col_fy:
                filter_year = st.selectbox("Year Filter", ["ALL", "FY", "SY", "TY"])
            
            query = "SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance WHERE 1=1"
            params = []
            
            if filter_course != "ALL":
                query += " AND course=?"
                params.append(filter_course)
            if
