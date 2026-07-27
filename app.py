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
             (student_name TEXT, course TEXT, year TEXT, subject TEXT, date TEXT, month TEXT, status TEXT, marked_by TEXT)''')

# Extended Notices table with file attachments
c.execute('''CREATE TABLE IF NOT EXISTS notices
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, content TEXT, file_data BLOB, file_name TEXT, posted_by TEXT, role TEXT, target_course TEXT, target_year TEXT, date TEXT)''')

# Holiday Calendar table
c.execute('''CREATE TABLE IF NOT EXISTS holidays
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, date TEXT, category TEXT)''')

# Schema Migrations
c.execute("PRAGMA table_info(notices)")
n_cols = [col[1] for col in c.fetchall()]
if 'file_data' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN file_data BLOB")
if 'file_name' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN file_name TEXT")
if 'category' not in n_cols:
    c.execute("ALTER TABLE notices ADD COLUMN category TEXT DEFAULT '📢 Notice'")

c.execute("PRAGMA table_info(attendance)")
a_cols = [col[1] for col in c.fetchall()]
if 'month' not in a_cols:
    c.execute("ALTER TABLE attendance ADD COLUMN month TEXT")
if 'subject' not in a_cols:
    c.execute("ALTER TABLE attendance ADD COLUMN subject TEXT DEFAULT 'General'")

conn.commit()

# Ensure Default Admin Exists
c.execute("""
    INSERT INTO users (username, password, role, course, year, is_approved)
    VALUES ('naman@1125', 'aniKet@124', 'Admin', 'ALL', 'ALL', 1)
    ON CONFLICT(username) DO UPDATE SET password='aniKet@124', is_approved=1
""")
conn.commit()

# Helper: Calculate 75% attendance shortfall
def calculate_75_shortfall(presents, total):
    if total == 0:
        return 0, "No lectures recorded yet."
    
    current_pct = (presents / total) * 100
    if current_pct >= 75.0:
        return 0, "🎯 Target Achieved! You are at or above 75%."
    
    needed = (3 * total) - (4 * presents)
    return max(0, needed), f"⚠️ You need to attend the next **{needed}** consecutive lecture(s) to reach 75%."

# Helper: Render Notices & Timetables Board with Delete and Download
def render_notice_board(target_course="ALL", target_year="ALL", current_user="", user_role="", key_suffix=""):
    st.subheader("📌 Notices, Timetables & Announcements")
    
    cat_filter = st.selectbox("Filter by Category", ["ALL", "📢 Notice", "📅 Timetable", "📝 Exam Schedule", "⚠️ Urgent"], key=f"cat_fltr_{key_suffix}")
    
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
            with st.expander(f"{category} | {title} ({date_posted})", expanded=True):
                st.write(content)
                
                # Render file download button if an attachment exists
                if file_data and file_name:
                    st.download_button(
                        label=f"📎 Download Attachment ({file_name})",
                        data=file_data,
                        file_name=file_name,
                        key=f"dl_{n_id}_{key_suffix}"
                    )
                    
                col_cap, col_del = st.columns([3, 1])
                with col_cap:
                    st.caption(f"Posted by: **{posted_by}** ({role}) | Target: Course `{tc}`, Year `{ty}`")
                
                # Delete permission for Admins or the teacher who posted it
                with col_del:
                    if user_role == "Admin" or (user_role == "Teacher" and posted_by == current_user):
                        if st.button("🗑️ Delete", key=f"del_n_{n_id}_{key_suffix}"):
                            c.execute("DELETE FROM notices WHERE id=?", (n_id,))
                            conn.commit()
                            st.success("Deleted successfully!")
                            st.rerun()
    else:
        st.info("No notices or timetables posted for this view.")

# Helper: Render Academic & Holiday Calendar
def render_holiday_calendar(user_role=""):
    st.subheader("📅 College Holiday & Academic Calendar")
    
    if user_role == "Admin":
        with st.expander("➕ Add New Holiday / Event"):
            h_title = st.text_input("Event / Holiday Name", key="h_title")
            h_date = st.date_input("Date", datetime.date.today(), key="h_date")
            h_cat = st.selectbox("Type", ["Official Holiday", "Exam Event", "Cultural / Sports", "Vacation"], key="h_cat")
            
            if st.button("Add to Calendar"):
                if h_title:
                    c.execute("INSERT INTO holidays (title, date, category) VALUES (?, ?, ?)",
                              (h_title, str(h_date), h_cat))
                    conn.commit()
                    st.success("Added to calendar!")
                    st.rerun()
                else:
                    st.warning("Please enter a title.")

    c.execute("SELECT id, title, date, category FROM holidays ORDER BY date ASC")
    holidays = c.fetchall()
    
    if holidays:
        df_h = pd.DataFrame(holidays, columns=["ID", "Event / Holiday", "Date", "Category"])
        st.dataframe(df_h[["Event / Holiday", "Date", "Category"]], use_container_width=True)
        
        if user_role == "Admin":
            h_del_id = st.selectbox("Select Event ID to Delete", [h[0] for h in holidays], format_func=lambda x: f"ID {x}")
            if st.button("Delete Event"):
                c.execute("DELETE FROM holidays WHERE id=?", (h_del_id,))
                conn.commit()
                st.success("Event removed.")
                st.rerun()
    else:
        st.info("No holidays or events added to the calendar yet.")

# -------------------------------------------------------------
# APP CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(page_title="College Attendance Portal", layout="wide", page_icon="🎓")

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
        
        if st.button("Sign In as Admin", type="primary"):
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
            
            if st.button("Teacher Login", type="primary"):
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
            
            if st.button("Student Login", type="primary"):
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
    st.sidebar.markdown(f"👤 **User:** `{st.session_state['user']}`")
    st.sidebar.markdown(f"🏷️ **Role:** `{st.session_state['role']}`")
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔑 Change Password"):
        new_pw = st.text_input("New Password", type="password", key="chg_pw")
        if st.button("Update Password"):
            if new_pw:
                c.execute("UPDATE users SET password=? WHERE username=?", (new_pw, st.session_state['user']))
                conn.commit()
                st.success("Password updated!")
            else:
                st.warning("Enter a valid password.")
                
    if st.sidebar.button("Logout", type="secondary"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state['role'] == "Admin":
        st.title("👑 Master Admin Command Center")
        
        tab_stats, tab_notice, tab_defaulters, tab_users, tab_approvals, tab_calendar = st.tabs([
            "📊 Global Stats & Reports", 
            "📢 Notices & Timetables",
            "⚠️ Defaulter List (<75%)", 
            "👥 User Management", 
            "🔔 Teacher Approvals",
            "📅 Academic Calendar"
        ])

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
            st.subheader("Filter Attendance Records")
            
            filter_course = st.selectbox("Select Course", ["ALL", "BCom", "BMS", "BScIT"])
            filter_year = st.selectbox("Select Year", ["ALL", "FY", "SY", "TY"])
            
            query = "SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance WHERE 1=1"
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
                df_all = pd.DataFrame(records, columns=["Student", "Course", "Year", "Subject", "Date", "Month", "Status", "Teacher"])
                st.dataframe(df_all, use_container_width=True)
                
                csv_data = df_all.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Attendance Report as CSV",
                    data=csv_data,
                    file_name=f"Attendance_Report_{filter_course}_{filter_year}.csv",
                    mime="text/csv"
                )
                
                st.subheader("Monthly Report Breakdown")
                monthly_summary = df_all.groupby(["Month", "Status"]).size().unstack(fill_value=0)
                st.bar_chart(monthly_summary)
            else:
                st.info("No attendance records match the selected filter.")

        # Tab 2: Admin Notice & Timetable Management
        with tab_notice:
            st.subheader("Post Notice, Timetable, or Announcement")
            
            col_cat, col_t = st.columns([1, 2])
            with col_cat:
                n_category = st.selectbox("Category Type", ["📢 Notice", "📅 Timetable", "📝 Exam Schedule", "⚠️ Urgent"], key="adm_n_cat")
            with col_t:
                n_title = st.text_input("Title / Heading", key="adm_n_title")
                
            n_content = st.text_area("Content / Details / Schedule", key="adm_n_content")
            uploaded_file = st.file_uploader("Attach PDF or Image (Optional)", type=["pdf", "png", "jpg", "jpeg"], key="adm_n_file")
            
            col_c, col_y = st.columns(2)
            with col_c:
                n_course = st.selectbox("Target Course", ["ALL", "BCom", "BMS", "BScIT"], key="adm_n_crs")
            with col_y:
                n_year = st.selectbox("Target Year", ["ALL", "FY", "SY", "TY"], key="adm_n_yr")
                
            if st.button("Publish Entry", type="primary"):
                if n_title and n_content:
                    today_str = str(datetime.date.today())
                    file_bytes = uploaded_file.read() if uploaded_file else None
                    file_name = uploaded_file.name if uploaded_file else None
                    
                    c.execute("""INSERT INTO notices 
                                 (category, title, content, file_data, file_name, posted_by, role, target_course, target_year, date) 
                                 VALUES (?, ?, ?, ?, ?, ?, 'Admin', ?, ?, ?)""",
                              (n_category, n_title, n_content, file_bytes, file_name, st.session_state['user'], n_course, n_year, today_str))
                    conn.commit()
                    st.success("Entry published successfully!")
                    st.rerun()
                else:
                    st.warning("Title and content are required.")
                    
            st.markdown("---")
            render_notice_board(current_user=st.session_state['user'], user_role=st.session_state['role'], key_suffix="adm")

        # Tab 3: Defaulter List (<75%)
        with tab_defaulters:
            st.subheader("⚠️ Students Below 75% Attendance")
            c.execute("SELECT username, course, year FROM users WHERE role='Student'")
            all_st = c.fetchall()
            
            defaulter_data = []
            for s_user, s_crs, s_yr in all_st:
                c.execute("SELECT status FROM attendance WHERE student_name=?", (s_user,))
                s_recs = c.fetchall()
                t_count = len(s_recs)
                p_count = sum(1 for r in s_recs if r[0] == 'Present')
                pct = (p_count / t_count * 100) if t_count > 0 else 0.0
                
                if pct < 75.0:
                    defaulter_data.append([s_user, s_crs, s_yr, t_count, p_count, f"{pct:.1f}%"])
                    
            if defaulter_data:
                df_def =
