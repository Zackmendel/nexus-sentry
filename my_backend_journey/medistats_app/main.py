import sqlite3
import csv
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# Initialize the App
app = FastAPI(title="MedConnect API", description="Backend for Medical App MVP")

# --- CONFIGURATION ---
DATABASE_NAME = 'med_app_data.db'
CSV_FILENAME = 'courses_sample.csv'

# --- DATA MODELS ---
class UserSignup(BaseModel):
    name: str
    role: str
    specialty: str
    license_number: str

class CourseCompletion(BaseModel):
    user_id: int
    course_id: int

# --- HELPER: Database Connection ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

# --- HELPER: CSV Loader (Added Here) ---
def import_courses_on_startup():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Ensure Tables Exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT, role TEXT, specialty TEXT, license_number TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY,
        title TEXT, provider TEXT, cme_credits REAL, 
        link TEXT, category TEXT, image_url TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS certificates (
        cert_id INTEGER PRIMARY KEY,
        user_id INTEGER, course_id INTEGER, completion_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )''')

    # 2. Check if courses are already loaded (to avoid duplicates)
    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] > 0:
        print("✅ Database already contains courses. Skipping CSV import.")
        conn.close()
        return

    # 3. Load CSV if database is empty
    if os.path.exists(CSV_FILENAME):
        print(f"📂 Loading data from {CSV_FILENAME}...")
        try:
            with open(CSV_FILENAME, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                for row in reader:
                    cursor.execute('''
                        INSERT INTO courses (title, provider, cme_credits, link, category, image_url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        row['title'], row['provider'], float(row['cme_credits']), 
                        row['link'], row['category'], row.get('image_url', '')
                    ))
                    count += 1
                conn.commit()
                print(f"✅ Imported {count} courses.")
        except Exception as e:
            print(f"❌ Error importing CSV: {e}")
    else:
        print(f"⚠️ Warning: {CSV_FILENAME} not found. Database initialized empty.")
        
    conn.close()

# --- FASTAPI STARTUP EVENT ---
# This runs automatically when you start the server
@app.on_event("startup")
def startup_event():
    import_courses_on_startup()

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/news/{topic}")
def get_medical_news(topic: str):
    # (Same logic as before - fetching from PubMed)
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    try:
        resp = requests.get(search_url, params={"db": "pubmed", "term": topic, "retmode": "json", "retmax": 3}).json()
        id_list = resp["esearchresult"]["idlist"]
        
        details = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", 
                               params={"db": "pubmed", "id": ",".join(id_list), "retmode": "xml"})
        root = ET.fromstring(details.content)
        
        articles = []
        for article in root.findall(".//PubmedArticle"):
            title = article.find(".//ArticleTitle").text
            pmid = article.find(".//PMID").text
            articles.append({
                "id": pmid,
                "title": title,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "summary": "AI Summary: Click to read full abstract..." 
            })
        return {"topic": topic, "articles": articles}
    except Exception:
        return {"error": "Could not fetch data from PubMed"}

@app.get("/courses")
def list_available_courses():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return {"courses": [dict(row) for row in courses]}

@app.post("/signup")
def create_user(user: UserSignup):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (full_name, role, specialty, license_number) VALUES (?, ?, ?, ?)",
                   (user.name, user.role, user.specialty, user.license_number))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "User created", "user_id": new_id}

@app.post("/complete_course")
def complete_course(data: CourseCompletion):
    conn = get_db_connection()
    date = datetime.now().strftime("%Y-%m-%d")
    conn.execute("INSERT INTO certificates (user_id, course_id, completion_date) VALUES (?, ?, ?)",
                 (data.user_id, data.course_id, date))
    conn.commit()
    conn.close()
    return {"message": "Course marked complete"}

@app.get("/download_cv/{user_id}")
def download_cv(user_id: int):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    certs = conn.execute('''
        SELECT c.title, c.provider, c.cme_credits 
        FROM certificates cert
        JOIN courses c ON cert.course_id = c.course_id
        WHERE cert.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"CV: {user['full_name']}", 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Role: {user['role']} | License: {user['license_number']}", 0, 1)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Completed Courses:", 0, 1)
    pdf.set_font('Arial', '', 10)
    for c in certs:
        pdf.cell(0, 8, f"- {c['title']} ({c['provider']}) | {c['cme_credits']} Credits", 0, 1)

    filename = f"cv_user_{user_id}.pdf"
    pdf.output(filename)
    return FileResponse(path=filename, filename=filename, media_type='application/pdf')