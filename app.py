import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random

# --- DATABASE SETUP ---
conn = sqlite3.connect('college_attendance.db', check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, course TEXT, year TEXT, is_approved INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS attendance (student_name TEXT, course TEXT, year TEXT, subject TEXT, date TEXT, month TEXT, status TEXT, marked_by TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, content TEXT, file_data BLOB, file_name TEXT, posted_by TEXT, role TEXT, target_course TEXT, target_year TEXT, date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS holidays (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, date TEXT, category TEXT)")

# Migration Checks
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

# Ensure default master admin
c.execute("INSERT INTO users (username, password, role, course, year, is_approved) VALUES ('naman@1125', 'aniKet@124', 'Admin', 'ALL', 'ALL', 1) ON CONFLICT(username) DO UPDATE SET password='aniKet@124', is_approved=1")
conn.commit()

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Student in exam: Is this a trick question? Prof: No, it is a test of your memory!",
    "Why was the computer late for class? It had a hard drive!",
    "Teacher: Name two elements on the periodic table. Student: Unobtanium and surprise elements!",
    "Why don't college students like math? Because it has too many problems!"
]

def get_shortfall(presents, total):
    if total == 0:
        return "No lectures recorded."
    pct = (presents / total) * 100
    if pct >= 75.0:
        return "Great! Above 75% target."
    needed = (3 * total) - (4 * presents)
    return f"Attend next {max(0, needed)} lectures to hit 75%."

def show_notices(target_course="ALL", target_year="ALL", current_user="", user_role="", key_prefix=""):
    st.subheader("Notice Board")
    c_filter = st.selectbox("Category", ["ALL", "Notice", "Timetable", "Exam Schedule", "Urgent"], key=f"cat_{key_prefix}")
    
    q = "SELECT id, category, title, content, file_data, file_name, posted_by, role, date FROM notices WHERE 1=1"
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
            with st.expander(f"[{n[1]}] {n[2]} ({n[8]})"):
                st.write(n[3])
                if n[4] and n[5]:
                    st.download_button("Download", data=n[4], file_name=n[5], key=f"dl_{n[0]}_{key_prefix}")
                st.caption(f"By: {n[6]} ({n[7]})")
                if user_role == "Admin" or (user_role == "Teacher" and n[6] == current_user):
                    if st.button("Delete", key=f"del_{n[0]}_{key_prefix}"):
                        c.execute("DELETE FROM notices WHERE id=?", (n[0],))
                        conn.commit()
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No notices.")

def show_calendar(user_role=""):
    st.subheader("Academic Calendar")
    if user_role == "Admin":
        with st.expander("Add Event"):
            ht = st.text_input("Event", key="ht")
            hd = st.date_input("Date", datetime.date.today(), key="hd")
            hc = st.selectbox("Type", ["Official Holiday", "Exam Event", "Cultural", "Vacation"], key="hc")
            if st.button("Save Event"):
                if ht:
                    c.execute("INSERT INTO holidays (title, date, category) VALUES (?, ?, ?)", (ht, str(hd), hc))
                    conn.commit()
                    st.success("Saved!")
                    st.rerun()

    c.execute("SELECT id, title, date, category FROM holidays ORDER BY date ASC")
    events = c.fetchall()
    if events:
        df = pd.DataFrame(events, columns=["ID", "Event", "Date", "Category"])
        st.dataframe(df[["Event", "Date", "Category"]], use_container_width=True)
        if user_role == "Admin":
            del_id = st.selectbox("Delete ID", [e[0] for e in events])
            if st.button("Remove Event"):
                c.execute("DELETE FROM holidays WHERE id=?", (del_id,))
                conn.commit()
                st.success("Removed!")
                st.rerun()
    else:
        st.info("No events.")

# --- MAIN APP ---
st.set_page_config(page_title="College Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

if 'joke' not in st.session_state:
    st.session_state['joke'] = random.choice(JOKES)

st.sidebar.title("Portal")

if not st.session_state['logged_in']:
    portal = st.sidebar.radio("Select", ["Admin", "Teacher", "Student"])

    if portal == "Admin":
        st.title("Admin Access")
        t1, t2 = st.tabs(["Login", "Reset"])
        with t1:
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.button("Login"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Admin'", (u, p))
                res = c.fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.rerun()
                else:
                    st.error("Invalid Login")
        with t2:
            ru = st.text_input("Admin User", key="rau").strip()
            rp = st.text_input("New Pass", type="password", key="rap").strip()
            if st.button("Update Pass"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Admin'", (rp, ru))
                conn.commit()
                st.success("Updated!")

    elif portal == "Teacher":
        st.title("Teacher Portal")
        t1, t2, t3 = st.tabs(["Login", "Register", "Reset"])
        with t1:
            u = st.text_input("Email", key="tu").strip()
            p = st.text_input("Password", type="password", key="tp").strip()
            if st.button("Teacher Login"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Teacher'", (u, p))
                res = c.fetchone()
                if res:
                    if res[5] == 0:
                        st.warning("Pending Approval")
                    else:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = res[0]
                        st.session_state['role'] = res[2]
                        st.session_state['course'] = res[3]
                        st.session_state['year'] = res[4]
                        st.rerun()
                else:
                    st.error("Invalid Login")
        with t2:
            ru = st.text_input("Email", key="rtu").strip()
            rp = st.text_input("Password", type="password", key="rtp").strip()
            rc = st.selectbox("Course", ["BCom", "BMS", "BScIT"], key="rtc")
            ry = st.selectbox("Year", ["FY", "SY", "TY"], key="rty")
            if st.button("Submit Teacher Reg"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Teacher', ?, ?, 0)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Submitted for approval!")
                except:
                    st.error("Already registered.")
        with t3:
            fu = st.text_input("Email", key="ftu").strip()
            fp = st.text_input("New Pass", type="password", key="ftp").strip()
            if st.button("Reset Teacher Pass"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Teacher'", (fp, fu))
                conn.commit()
                st.success("Updated!")

    elif portal == "Student":
        st.title("Student Portal")
        t1, t2, t3 = st.tabs(["Login", "Register", "Reset"])
        with t1:
            u = st.text_input("Email", key="su").strip()
            p = st.text_input("Password", type="password", key="sp").strip()
            if st.button("Student Login"):
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
                    st.error("Invalid Login")
        with t2:
            ru = st.text_input("Email", key="rsu").strip()
            rp = st.text_input("Password", type="password", key="rsp").strip()
            rc = st.selectbox("Course", ["BCom", "BMS", "BScIT"], key="rsc")
            ry = st.selectbox("Year", ["FY", "SY", "TY"], key="rsy")
            if st.button("Create Account"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Student', ?, ?, 1)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Created! You can login.")
                except:
                    st.error("Already registered.")
        with t3:
            fu = st.text_input("Email", key="fsu").strip()
            fp = st.text_input("New Pass", type="password", key="fsp").strip()
            if st.button("Reset Student Pass"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Student'", (fp, fu))
                conn.commit()
                st.success("Updated!")

else:
    st.sidebar.markdown(f"**User:** `{st.session_state['user']}`")
    st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
    
    with st.sidebar.expander("Settings"):
        npw = st.text_input("New Password", type="password")
        if st.button("Change Pass"):
            c.execute("UPDATE users SET password=? WHERE username=?", (npw, st.session_state['user']))
            conn.commit()
            st.success("Updated!")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state['role'] == "Admin":
        st.title("Admin Master Control")
        t_overview, t_notices, t_defaulters, t_users, t_app, t_cal = st.tabs([
            "Overview", "Notices", "Defaulters", "Users", "Approvals", "Calendar"
        ])
        
        with t_overview:
            c.execute("SELECT COUNT(*) FROM users WHERE role='Student'")
            st_cnt = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM attendance")
            att_cnt = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
            pr_cnt = c.fetchone()[0]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Students", st_cnt)
            c2.metric("Lectures", att_cnt)
            c3.metric("Presents", pr_cnt)
            c4.metric("Average", f"{(pr_cnt/att_cnt*100) if att_cnt>0 else 0:.1f}%")
            
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
                st.dataframe(pd.DataFrame(recs, columns=["Student", "Course", "Year", "Subject", "Date", "Month", "Status", "Teacher"]), use_container_width=True)

        with t_notices:
            nt_cat = st.selectbox("Category", ["Notice", "Timetable", "Exam Schedule", "Urgent"])
            nt_title = st.text_input("Title")
            nt_body = st.text_area("Content")
            nt_file = st.file_uploader("Attachment")
            nt_crs = st.selectbox("Course", ["ALL", "BCom", "BMS", "BScIT"])
            nt_yr = st.selectbox("Year", ["ALL", "FY", "SY", "TY"])
            if st.button("Post Notice"):
                fb = nt_file.read() if nt_file else None
                fn = nt_file.name if nt_file else None
                c.execute("INSERT INTO notices (category, title, content, file_data, file_name, posted_by, role, target_course, target_year, date) VALUES (?, ?, ?, ?, ?, ?, 'Admin', ?, ?, ?)",
                          (nt_cat, nt_title, nt_body, fb, fn, st.session_state['user'], nt_crs, nt_yr, str(datetime.date.today())))
                conn.commit()
                st.success("Posted!")
                st.rerun()
            st.markdown("---")
            show_notices(current_user=st.session_state['user'], user_role="Admin", key_prefix="adm")

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
                st.dataframe(pd.DataFrame(def_list, columns=["Student", "Course", "Year", "Total", "Attended", "Pct"]), use_container_width=True)
            else:
                st.success("No defaulters (<75%) found!")

        with t_users:
            c.execute("SELECT username, role, course, year, is_approved FROM users")
            all_u = pd.DataFrame(c.fetchall(), columns=["User", "Role", "Course", "Year", "Approved"])
            st.dataframe(all_u, use_container_width=True)
            
            user_del = st.selectbox("Delete User", [u for u in all_u['User'] if u != 'naman@1125'])
            if st.button("Delete Selected User"):
                c.execute("DELETE FROM users WHERE username=?", (user_del,))
                c.execute("DELETE FROM attendance WHERE student_name=?", (user_del,))
                conn.commit()
                st.success("Deleted!")
                st.rerun()

        with t_app:
            c.execute("SELECT username, course, year FROM users WHERE role='Teacher' AND is_approved=0")
            p = c.fetchall()
            if p:
                st.dataframe(pd.DataFrame(p, columns=["Teacher", "Course", "Year"]), use_container_width=True)
                sel_t = st.selectbox("Approve", [x[0] for x in p])
                if st.button("Approve Teacher"):
                    c.execute("UPDATE users SET is_approved=1 WHERE username=?", (sel_t,))
                    conn.commit()
                    st.success("Approved!")
                    st.rerun()
            else:
                st.info("No pending approvals.")

        with t_cal:
            show_calendar(user_role="Admin")

    # --- TEACHER DASHBOARD ---
    elif st.session_state['role'] == "Teacher":
        st.title(f"Teacher Portal ({st.session_state['course']} - {st.session_state['year']})")
        t_mark, t_notices, t_rep, t_cal = st.tabs(["Mark", "Notices", "Reports", "Calendar"])
        
        with t_mark:
            ldate = st.date_input("Date", datetime.date.today())
            lsubj = st.text_input("Subject", "General")
            lmonth = ldate.strftime("%B %Y")
            
            c.execute("SELECT username FROM users WHERE role='Student' AND course=? AND year=?", (st.session_state['course'], st.session_state['year']))
            st_list = [x[0] for x in c.fetchall()]
            
            if st_list:
                marks = {}
                for s in st_list:
                    marks[s] = st.radio(f"Student: {s}", ["Present", "Absent"], key=s, horizontal=True)
                if st.button("Save Attendance"):
                    for s, status in marks.items():
                        c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                  (s, st.session_state['course'], st.session_state['year'], lsubj, str(ldate), lmonth, status, st.session_state['user']))
                    conn.commit()
                    st.success("Saved!")
            else:
                st.warning("No students found.")

        with t_notices:
            nt_cat = st.selectbox("Category", ["Notice", "Timetable", "Exam Schedule", "Urgent"], key="tc")
            nt_title = st.text_input("Title", key="tt")
            nt_body = st.text_area("Content", key="tb")
            nt_file = st.file_uploader("File", key="tf")
            if st.button("Post to Class"):
                fb = nt_file.read() if nt_file else None
                fn = nt_file.name if nt_file else None
                c.execute("INSERT INTO notices (category, title, content, file_data, file_name, posted_by, role, target_course, target_year, date) VALUES (?, ?, ?, ?, ?, ?, 'Teacher', ?, ?, ?)",
                          (nt_cat, nt_title, nt_body, fb, fn, st.session_state['user'], st.session_state['course'], st.session_state['year'], str(datetime.date.today())))
                conn.commit()
                st.success("Posted!")
                st.rerun()
            st.markdown("---")
            show_notices(target_course=st.session_state['course'], target_year=st.session_state['year'], current_user=st.session_state['user'], user_role="Teacher", key_prefix="tch")

        with t_rep:
            c.execute("SELECT student_name, subject, date, month, status FROM attendance WHERE course=? AND year=?", (st.session_state['course'], st.session_state['year']))
            recs = c.fetchall()
            if recs:
                st.dataframe(pd.DataFrame(recs, columns=["Student", "Subject", "Date", "Month", "Status"]), use_container_width=True)

        with t_cal:
            show_calendar(user_role="Teacher")

    # --- STUDENT DASHBOARD ---
    elif st.session_state['role'] == "Student":
        st.title("Student Hub")
        t_att, t_notices, t_cal, t_joke = st.tabs(["Attendance", "Notices", "Calendar", "Jokes"])
        
        with t_att:
            c.execute("SELECT date, subject, month, status, marked_by FROM attendance WHERE student_name=?", (st.session_state['user'],))
            recs = c.fetchall()
            if recs:
                df = pd.DataFrame(recs, columns=["Date", "Subject", "Month", "Status", "Teacher"])
                tot = len(df)
                pr =
