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

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Student in exam: Is this a trick question? Prof: No, it is a test!",
    "Why was the computer late? It had a hard drive!",
    "Teacher: Name two elements. Student: Unobtanium and surprise elements!",
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

def show_notices(t_crs="ALL", t_yr="ALL", c_user="", u_role="", pfx=""):
    st.subheader("Notice Board")
    c_flt = st.selectbox("Category", ["ALL", "Notice", "Exam", "Urgent"], key=f"c_{pfx}")
    
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
            with st.expander(f"[{n[1]}] {n[2]} ({n[8]})"):
                st.write(n[3])
                if n[4] and n[5]:
                    st.download_button("Download", data=n[4], file_name=n[5], key=f"dl_{n[0]}_{pfx}")
                st.caption(f"By: {n[6]}")
                if u_role == "Admin" or (u_role == "Teacher" and n[6] == c_user):
                    if st.button("Delete", key=f"del_{n[0]}_{pfx}"):
                        c.execute("DELETE FROM notices WHERE id=?", (n[0],))
                        conn.commit()
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No notices.")

def show_cal(u_role=""):
    st.subheader("Calendar")
    if u_role == "Admin":
        with st.expander("Add Event"):
            ht = st.text_input("Event", key="ht")
            hd = st.date_input("Date", datetime.date.today(), key="hd")
            hc = st.selectbox("Type", ["Holiday", "Exam", "Sports"], key="hc")
            if st.button("Save Event"):
                if ht:
                    c.execute("INSERT INTO holidays (title, date, category) VALUES (?, ?, ?)", (ht, str(hd), hc))
                    conn.commit()
                    st.success("Saved!")
                    st.rerun()

    c.execute("SELECT id, title, date, category FROM holidays ORDER BY date ASC")
    evs = c.fetchall()
    if evs:
        df = pd.DataFrame(evs, columns=["ID", "Event", "Date", "Category"])
        st.dataframe(df[["Event", "Date", "Category"]], use_container_width=True)
        if u_role == "Admin":
            del_id = st.selectbox("Delete ID", [e[0] for e in evs])
            if st.button("Remove Event"):
                c.execute("DELETE FROM holidays WHERE id=?", (del_id,))
                conn.commit()
                st.success("Removed!")
                st.rerun()
    else:
        st.info("No events.")

# --- MAIN APP ---
st.set_page_config(page_title="Portal", layout="wide")

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
        st.title("Admin")
        t1, t2 = st.tabs(["Login", "Reset"])
        with t1:
            u = st.text_input("User").strip()
            p = st.text_input("Pass", type="password").strip()
            if st.button("Login"):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Admin'", (u, p))
                res = c.fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = res[0]
                    st.session_state['role'] = res[2]
                    st.rerun()
                else:
                    st.error("Error")
        with t2:
            ru = st.text_input("User", key="au").strip()
            rp = st.text_input("New Pass", type="password", key="ap").strip()
            if st.button("Update"):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Admin'", (rp, ru))
                conn.commit()
                st.success("Updated!")

    elif portal == "Teacher":
        st.title("Teacher")
        t1, t2, t3 = st.tabs(["Login", "Register", "Reset"])
        with t1:
            u = st.text_input("Email", key="tu").strip()
            p = st.text_input("Pass", type="password", key="tp").strip()
            if st.button("Login "):
                c.execute("SELECT * FROM users WHERE username=? AND password=? AND role='Teacher'", (u, p))
                res = c.fetchone()
                if res:
                    if res[5] == 0:
                        st.warning("Pending")
                    else:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = res[0]
                        st.session_state['role'] = res[2]
                        st.session_state['course'] = res[3]
                        st.session_state['year'] = res[4]
                        st.rerun()
                else:
                    st.error("Error")
        with t2:
            ru = st.text_input("Email", key="rtu").strip()
            rp = st.text_input("Pass", type="password", key="rtp").strip()
            rc = st.selectbox("Course", ["BCom", "BMS", "BScIT"], key="rtc")
            ry = st.selectbox("Year", ["FY", "SY", "TY"], key="rty")
            if st.button("Submit Reg"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Teacher', ?, ?, 0)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Submitted!")
                except:
                    st.error("Exists")
        with t3:
            fu = st.text_input("Email", key="ftu").strip()
            fp = st.text_input("New Pass", type="password", key="ftp").strip()
            if st.button("Reset "):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Teacher'", (fp, fu))
                conn.commit()
                st.success("Updated!")

    elif portal == "Student":
        st.title("Student")
        t1, t2, t3 = st.tabs(["Login", "Register", "Reset"])
        with t1:
            u = st.text_input("Email", key="su").strip()
            p = st.text_input("Pass", type="password", key="sp").strip()
            if st.button("Login  "):
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
                    st.error("Error")
        with t2:
            ru = st.text_input("Email", key="rsu").strip()
            rp = st.text_input("Pass", type="password", key="rsp").strip()
            rc = st.selectbox("Course", ["BCom", "BMS", "BScIT"], key="rsc")
            ry = st.selectbox("Year", ["FY", "SY", "TY"], key="rsy")
            if st.button("Create"):
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 'Student', ?, ?, 1)", (ru, rp, rc, ry))
                    conn.commit()
                    st.success("Created!")
                except:
                    st.error("Exists")
        with t3:
            fu = st.text_input("Email", key="fsu").strip()
            fp = st.text_input("New Pass", type="password", key="fsp").strip()
            if st.button("Reset  "):
                c.execute("UPDATE users SET password=? WHERE username=? AND role='Student'", (fp, fu))
                conn.commit()
                st.success("Updated!")

else:
    st.sidebar.markdown(f"**User:** `{st.session_state['user']}`")
    st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
    
    with st.sidebar.expander("Settings"):
        npw = st.text_input("New Pass", type="password")
        if st.button("Change"):
            c.execute("UPDATE users SET password=? WHERE username=?", (npw, st.session_state['user']))
            conn.commit()
            st.success("Updated!")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    if st.session_state['role'] == "Admin":
        st.title("Admin Panel")
        t_o, t_n, t_d, t_u, t_a, t_c = st.tabs(["View", "Post", "Defs", "Users", "Approve", "Cal"])
        
        with t_o:
            c.execute("SELECT COUNT(*) FROM attendance")
            att = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
            prs = c.fetchone()[0]
            
            st.metric("Avg", f"{(prs/att*100) if att>0 else 0:.1f}%")
            
            c.execute("SELECT student_name, course, year, subject, date, month, status, marked_by FROM attendance")
            recs = c.fetchall()
            if recs:
                st.dataframe(pd.DataFrame(recs, columns=["Std", "Crs", "Yr", "Sub", "Dt", "Mth", "Sts", "Tch"]))

        with t_n:
            nc = st.selectbox("Cat", ["Notice", "Exam", "Urgent"])
            nt = st.text_input("Title")
            nb = st.text_area("Body")
            crs = st.selectbox("Course", ["ALL", "BCom", "BMS", "BScIT"])
            yr = st.selectbox("Year", ["ALL", "FY", "SY", "TY"])
            if st.button("Post"):
                c.execute("INSERT INTO notices (category, title, content, posted_by, role, target_course, target_year, date) VALUES (?, ?, ?, ?, 'Admin', ?, ?, ?)",
                          (nc, nt, nb, st.session_state['user'], crs, yr, str(datetime.date.today())))
                conn.commit()
                st.success("Posted!")
                st.rerun()
            st.markdown("---")
            show_notices(c_user=st.session_state['user'], u_role="Admin", pfx="adm")

        with t_d:
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
                st.dataframe(pd.DataFrame(d_list, columns=["Std", "Crs", "Yr", "Tot", "Prs", "Pct"]))

        with t_u:
            c.execute("SELECT username, role, course, year, is_approved FROM users")
            all_u = pd.DataFrame(c.fetchall(), columns=["User", "Role", "Course", "Year", "App"])
            st.dataframe(all_u)
            
            udel = st.selectbox("Delete", [u for u in all_u['User'] if u != 'naman@1125'])
            if st.button("Del User"):
                c.execute("DELETE FROM users WHERE username=?", (udel,))
                conn.commit()
                st.success("Deleted!")
                st.rerun()

        with t_a:
            c.execute("SELECT username FROM users WHERE role='Teacher' AND is_approved=0")
            p = c.fetchall()
            if p:
                sel = st.selectbox("Approve", [x[0] for x in p])
                if st.button("Approve Tch"):
                    c.execute("UPDATE users SET is_approved=1 WHERE username=?", (sel,))
                    conn.commit()
                    st.success("Approved!")
                    st.rerun()

        with t_c:
            show_cal(u_role="Admin")

    elif st.session_state['role'] == "Teacher":
        st.title("Teacher")
        tm, tn, tr, tc = st.tabs(["Mark", "Notice", "Rep", "Cal"])
        
        with tm:
            ld = st.date_input("Dt", datetime.date.today())
            ls = st.text_input("Sub", "Gen")
            lm = ld.strftime("%b %Y")
            
            c.execute("SELECT username FROM users WHERE role='Student' AND course=? AND year=?", (st.session_state['course'], st.session_state['year']))
            sl = [x[0] for x in c.fetchall()]
            
            if sl:
                mks = {}
                for s in sl:
                    mks[s] = st.radio(f"{s}", ["Present", "Absent"], key=s, horizontal=True)
                if st.button("Save"):
                    for s, stt in mks.items():
                        c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                  (s, st.session_state['course'], st.session_state['year'], ls, str(ld), lm, stt, st.session_state['user']))
                    conn.commit()
                    st.success("Saved!")

        with tn:
            nc = st.selectbox("Cat", ["Notice", "Exam", "Urgent"], key="tnc")
            nt = st.text_input("Title", key="tnt")
            nb = st.text_area("Body", key="tnb")
            if st.button("Post "):
                c.execute("INSERT INTO notices (category, title, content, posted_by, role, target_course, target_year, date) VALUES (?, ?, ?, ?, 'Teacher', ?, ?, ?)",
                          (nc, nt, nb, st.session_state['user'], st.session_state['course'], st.session_state['year'], str(datetime.date.today())))
                conn.commit()
                st.success("Posted!")
                st.rerun()
            show_notices(t_crs=st.session_state['course'], t_yr=st.session_state['year'], c_user=st.session_state['user'], u_role="Teacher", pfx="tch")

        with tr:
            c.execute("SELECT student_name, subject, date, status FROM attendance WHERE course=? AND year=?", (st.session_state['course'], st.session_state['year']))
            recs = c.fetchall()
            if recs:
                st.dataframe(pd.DataFrame(recs, columns=["Std", "Sub", "Dt", "Sts"]))

        with tc:
            show_cal(u_role="Teacher")

    elif st.session_state['role'] == "Student":
        st.title("Student")
        ta, tn, tc, tj = st.tabs(["Att", "Notices", "Cal", "Joke"])
        
        with ta:
            c.execute("SELECT date, subject, status FROM attendance WHERE student_name=?", (st.session_state['user'],))
            recs = c.fetchall()
            if recs:
                tot = len(recs)
                pr_count = 0
                for r in recs:
                    if r[2] == 'Present':
                        pr_count += 1
                
                pct = (pr_count / tot * 100) if tot > 0 else 0.0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Tot", tot)
                c2.metric("Prs", pr_count)
                c3.metric("Pct", f"{pct:.1f}%")
                
                st.info(get_shortfall(pr_count, tot))
                st.dataframe(pd.DataFrame(recs, columns=["Dt", "Sub", "Sts"]))
            else:
                st.info("No records.")

        with tn:
            show_notices(t_crs=st.session_state['course'], t_yr=st.session_state['year'], c_user=st.session_state['user'], u_role="Student", pfx="std")

        with tc:
            show_cal(u_role="Student")

        with tj:
            st.info(st.session_state['joke'])
            if st.button("New Joke"):
                st.session_state['joke'] = random.choice(JOKES)
                st.rerun()
