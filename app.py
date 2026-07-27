import streamlit as st
import sqlite3
import pandas as pd
import datetime

# -------------------------------------------------------------
# DATABASE SETUP & AUTOMATIC MIGRATION
# -------------------------------------------------------------
conn = sqlite3.connect('college_attendance.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, password TEXT, role TEXT, course TEXT, year TEXT, is_approved INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS attendance
             (student_name TEXT, course TEXT, year TEXT, date TEXT, status TEXT, marked_by TEXT)''')

# Auto-migrate database: Check if 'month' column exists in attendance table, add if missing
c.execute("PRAGMA table_info(attendance)")
columns = [column[1] for column in c.fetchall()]
if 'month' not in columns:
    c.execute("ALTER TABLE attendance ADD COLUMN month TEXT")

conn.commit()

# Ensure Admin Credentials exist
c.execute("""
    INSERT INTO users (username, password, role, course, year, is_approved)
    VALUES ('naman@1125', 'aniKet@124', 'Admin', 'ALL', 'ALL', 1)
    ON CONFLICT(username) DO UPDATE SET password='aniKet@124', is_approved=1
""")
conn.commit()

# Helper function to calculate 75% attendance requirement
def calculate_75_shortfall(presents, total):
    if total == 0:
        return 0, "No lectures recorded yet."
    
    current_pct = (presents / total) * 100
    if current_pct >= 75.0:
        return 0, "🎯 Target Achieved! You are at or above 75%."
    
    needed = (3 * total) - (4 * presents)
    return max(0, needed), f"⚠️ You need to attend the next **{needed}** consecutive lecture(s) to reach 75%."

# -------------------------------------------------------------
# APP CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(page_title="College Attendance Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

st.sidebar.title("📌 Navigation Portal")

# -------------------------------------------------------------
# LOGIN & REGISTRATION PORTALS
# -------------------------------------------------------------
if not st.session_state['logged_in']:
    portal_choice = st.sidebar.radio("Select Portal", ["👑 Admin Login", "👨‍🏫 Teacher Portal", "🎓 Student Portal"])

    # --- 1. ADMIN PORTAL ---
    if portal_choice == "👑 Admin Login":
        st.header("🔑 Admin Sign-In")
        st.caption("Restricted administrative control panel.")
        
        admin_user = st.text_input("Admin Username").strip()
        admin_pass = st.text_input("Admin Password", type="password").strip()
        
        if st.button("Sign In as Admin"):
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

    # --- 2. TEACHER PORTAL ---
    elif portal_choice == "👨‍🏫 Teacher Portal":
        st.header("👨‍🏫 Teacher Portal")
        tab1, tab2 = st.tabs(["Teacher Login", "Teacher Register"])
        
        with tab1:
            t_user = st.text_input("Teacher Username / Email", key="t_login_user").strip()
            t_pass = st.text_input("Password", type="password", key="t_login_pass").strip()
            
            if st.button("Teacher Login"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Teacher'", (t_user, t_pass))
                user = c.fetchone()
                if user:
                    if user[5] == 0:
                        st.warning("⚠️ Your teacher account is pending Admin approval.")
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
            reg_user = st.text_input("New Teacher Username / Email", key="t_reg_user").strip()
            reg_pass = st.text_input("New Password", type="password", key="t_reg_pass").strip()
            course = st.selectbox("Assigned Course", ["BCom", "BMS", "BScIT"], key="t_reg_course")
            year = st.selectbox("Assigned Year", ["FY", "SY", "TY"], key="t_reg_year")
            
            if st.button("Register Teacher Account"):
                if reg_user and reg_pass:
                    try:
                        c.execute("INSERT INTO users VALUES (?, ?, 'Teacher', ?, ?, 0)", 
                                  (reg_user, reg_pass, course, year))
                        conn.commit()
                        st.info("Registration submitted! Admin approval required before logging in.")
                    except sqlite3.IntegrityError:
                        st.error("Username already registered!")
                else:
                    st.warning("Please fill out all fields.")

    # --- 3. STUDENT PORTAL ---
    elif portal_choice == "🎓 Student Portal":
        st.header("🎓 Student Portal")
        tab1, tab2 = st.tabs(["Student Login", "Student Register"])
        
        with tab1:
            s_user = st.text_input("Student Username / Email", key="s_login_user").strip()
            s_pass = st.text_input("Password", type="password", key="s_login_pass").strip()
            
            if st.button("Student Login"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Student'", (s_user, s_pass))
                user = c.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user[0]
                    st.session_state['role'] = user[2]
                    st.session_state['course'] = user[3]
                    st.session_state['year'] = user[4]
                    st.success("Student login successful!")
                    st.rerun()
                else:
                    st.error("Invalid Student credentials.")
                    
        with tab2:
            reg_user = st.text_input("New Student Username / Email", key="s_reg_user").strip()
            reg_pass = st.text_input("New Password", type="password", key="s_reg_pass").strip()
            course = st.selectbox("Course Enrolled", ["BCom", "BMS", "BScIT"], key="s_reg_course")
            year = st.selectbox("Year", ["FY", "SY", "TY"], key="s_reg_year")
            
            if st.button("Register Student Account"):
                if reg_user and reg_pass:
                    try:
                        c.execute("INSERT INTO users VALUES (?, ?, 'Student', ?, ?, 1)", 
                                  (reg_user, reg_pass, course, year))
                        conn.commit()
                        st.success("Student account created successfully! You can log in now.")
                    except sqlite3.IntegrityError:
                        st.error("Username already registered!")
                else:
                    st.warning("Please fill out all fields.")

# -------------------------------------------------------------
# LOGGED-IN DASHBOARDS
# -------------------------------------------------------------
else:
    st.sidebar.markdown(f"**Logged in as:** `{st.session_state['user']}`")
    st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state['role'] == "Admin":
        st.title("👑 Master Admin Command Center")
        
        tab_stats, tab_users, tab_approvals = st.tabs(["📊 Global Statistics & Records", "👥 User Management", "🔔 Teacher Approvals"])

        # Tab 1: Global Stats & Reports
        with tab_stats:
            st.subheader("Global Attendance Overview")
            
            c.execute("SELECT COUNT(*) FROM users WHERE role='Student'")
            total_students = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM attendance")
            total_records = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
            total_presents = c.fetchone()[0]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Students", total_students)
            col2.metric("Total Lectures Logged", total_records)
            col3.metric("Total Present Logged", total_presents)
            overall_pct = (total_presents / total_records * 100) if total_records > 0 else 0
            col4.metric("Avg Overall Attendance", f"{overall_pct:.1f}%")

            st.markdown("---")
            st.subheader("Filter Attendance by Course & Year")
            
            filter_course = st.selectbox("Select Course", ["ALL", "BCom", "BMS", "BScIT"])
            filter_year = st.selectbox("Select Year", ["ALL", "FY", "SY", "TY"])
            
            query = "SELECT student_name, course, year, date, month, status, marked_by FROM attendance WHERE 1=1"
            params = []
            
            if filter_course != "ALL":
                query += " AND course=?"
                params.append(filter_course)
            if filter_year != "ALL":
                query += " AND year=?"
                params.append(filter_year)
                
            c.execute(query, params)
            records = c.fetchall()
            
            if records:
                df_all = pd.DataFrame(records, columns=["Student", "Course", "Year", "Date", "Month", "Status", "Teacher"])
                st.dataframe(df_all, use_container_width=True)
                
                st.subheader("Monthly Report Breakdown")
                monthly_summary = df_all.groupby(["Month", "Status"]).size().unstack(fill_value=0)
                st.bar_chart(monthly_summary)
            else:
                st.info("No attendance records match the selected filter.")

        # Tab 2: Manage Users
        with tab_users:
            st.subheader("Registered System Users")
            c.execute("SELECT username, role, course, year, is_approved FROM users")
            all_users = pd.DataFrame(c.fetchall(), columns=["Username", "Role", "Course", "Year", "Approved"])
            st.dataframe(all_users, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Delete User Account")
            user_to_delete = st.selectbox("Select User to Remove", [u for u in all_users['Username'] if u != "naman@1125"])
            if st.button("Delete Selected User"):
                c.execute("DELETE FROM users WHERE username=?", (user_to_delete,))
                c.execute("DELETE FROM attendance WHERE student_name=?", (user_to_delete,))
                conn.commit()
                st.success(f"User `{user_to_delete}` and their records have been removed.")
                st.rerun()

        # Tab 3: Teacher Approvals
        with tab_approvals:
            st.subheader("Pending Teacher Registrations")
            c.execute("SELECT username, course, year FROM users WHERE role='Teacher' AND is_approved=0")
            pending = c.fetchall()
            
            if pending:
                df_pending = pd.DataFrame(pending, columns=["Teacher Email", "Course", "Year"])
                st.dataframe(df_pending)
                
                t_approve = st.selectbox("Select Teacher to Approve", [t[0] for t in pending])
                if st.button("Approve Selected Teacher"):
                    c.execute("UPDATE users SET is_approved=1 WHERE username=?", (t_approve,))
                    conn.commit()
                    st.success(f"Approved teacher `{t_approve}`!")
                    st.rerun()
            else:
                st.info("No pending teacher approval requests.")

    # --- TEACHER DASHBOARD ---
    elif st.session_state['role'] == "Teacher":
        st.title(f"👨‍🏫 Attendance Entry ({st.session_state['course']} - {st.session_state['year']})")
        
        tab_mark, tab_reports = st.tabs(["Mark Daily Attendance", "Course Monthly Reports"])
        
        with tab_mark:
            selected_date = st.date_input("Select Date", datetime.date.today())
            month_str = selected_date.strftime("%B %Y")
            
            c.execute("SELECT username FROM users WHERE role='Student' AND course=? AND year=?", 
                      (st.session_state['course'], st.session_state['year']))
            students = [s[0] for s in c.fetchall()]
            
            if students:
                st.subheader(f"Marking Attendance for {month_str}")
                attendance_data = {}
                for student in students:
                    attendance_data[student] = st.radio(f"Student: **{student}**", ["Present", "Absent"], key=student, horizontal=True)
                
                if st.button("Submit Attendance"):
                    for student, status in attendance_data.items():
                        c.execute("INSERT INTO attendance (student_name, course, year, date, month, status, marked_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (student, st.session_state['course'], st.session_state['year'], str(selected_date), month_str, status, st.session_state['user']))
                    conn.commit()
                    st.success("Attendance successfully submitted!")
            else:
                st.warning("No students registered for your course and year yet.")

        with tab_reports:
            st.subheader("Class Monthly Attendance Report")
            c.execute("SELECT student_name, date, month, status FROM attendance WHERE course=? AND year=?", 
                      (st.session_state['course'], st.session_state['year']))
            records = c.fetchall()
            
            if records:
                df_cls = pd.DataFrame(records, columns=["Student", "Date", "Month", "Status"])
                st.dataframe(df_cls, use_container_width=True)
                
                st.subheader("Monthly Class Breakdown")
                pivot_chart = df_cls.groupby(["Month", "Status"]).size().unstack(fill_value=0)
                st.bar_chart(pivot_chart)
            else:
                st.info("No records recorded for your class yet.")

    # --- STUDENT DASHBOARD ---
    elif st.session_state['role'] == "Student":
        st.title(f"🎓 Student Attendance & 75% Target Tracker")
        
        c.execute("SELECT date, month, status, marked_by FROM attendance WHERE student_name=?", (st.session_state['user'],))
        records = c.fetchall()
        
        if records:
            df_st = pd.DataFrame(records, columns=["Date", "Month", "Status", "Marked By Teacher"])
            
            total = len(df_st)
            presents = len(df_st[df_st['Status'] == "Present"])
            absents = total - presents
            current_pct = (presents / total) * 100 if total > 0 else 0.0
            
            needed_lectures, status_msg = calculate_75_shortfall(presents, total)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Lectures", total)
            col2.metric("Presents Logged", presents)
            col3.metric("Absents Logged", absents)
            col4.metric("Current Percentage", f"{current_pct:.1f}%")
            
            st.markdown("---")
            
            if current_pct < 75.0:
                st.error(f"### ⚠️ Below Attendance Criteria\n{status_msg}")
            else:
                st.success(f"### 🎯 Criteria Satisfied\n{status_msg}")
                
            st.markdown("---")
            
            tab_rec, tab_m_report = st.tabs(["Detailed Log", "Monthly Summary Breakdown"])
            
            with tab_rec:
                st.subheader("Date-wise Record")
                st.dataframe(df_st, use_container_width=True)
                
            with tab_m_report:
                st.subheader("Monthly Attendance Breakdown")
                monthly_st = df_st.groupby(["Month", "Status"]).size().unstack(fill_value=0)
                st.bar_chart(monthly_st)
        else:
            st.info("No attendance entries recorded for your account yet.")