import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="Niranjana Majithia College - Campus Portal", 
    layout="wide", 
    page_icon="🎓"
)

ADMIN_USER = st.secrets.get("ADMIN_USER", "9321481833")
ADMIN_PASS = st.secrets.get("ADMIN_PASS", "aniKet@1124")

try:
    # Safely extract URL from secrets supporting multiple formats
    if "connections" in st.secrets and "neon" in st.secrets["connections"]:
        db_url = st.secrets["connections"]["neon"]["url"]
    elif "neon_url" in st.secrets:
        db_url = st.secrets["neon_url"]
    else:
        db_url = st.secrets.get("DATABASE_URL", "")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(db_url)
except Exception as e:
    st.error(f"Database Connection Configuration Error: {e}")
    st.stop()

def init_db():
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, course TEXT, year TEXT, is_approved INTEGER)")
            conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS attendance (student_name TEXT, course TEXT, year TEXT, subject TEXT, date TEXT, month TEXT, status TEXT, marked_by TEXT)")
            conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS notices (id SERIAL PRIMARY KEY, category TEXT, title TEXT, content TEXT, file_data BYTEA, file_name TEXT, posted_by TEXT, role TEXT, target_course TEXT, target_year TEXT, date TEXT)")
            conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS holidays (id SERIAL PRIMARY KEY, title TEXT, date TEXT, category TEXT)")
            conn.exec_driver_sql(
                "INSERT INTO users (username, password, role, course, year, is_approved) VALUES (%s, %s, 'Admin', 'ALL', 'ALL', 1) ON CONFLICT (username) DO UPDATE SET password = EXCLUDED.password, role = 'Admin', is_approved = 1",
                (ADMIN_USER, ADMIN_PASS)
            )
    except Exception as e:
        st.error(f"Database Initialization Error: {e}")
        st.stop()

init_db()
