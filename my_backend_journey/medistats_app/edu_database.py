import sqlite3
from datetime import datetime

# 1. Setup the Database (The "Memory")
def setup_database():
    conn = sqlite3.connect('med_app_data.db')
    cursor = conn.cursor()

    # Create USERS table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        role TEXT,
        specialty TEXT,
        license_number TEXT
    )
    ''')

    # Create COURSES table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY,
        title TEXT,
        provider TEXT,
        cme_credits REAL
    )
    ''')

    # Create CERTIFICATES table (The "CV" Records)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS certificates (
        cert_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        course_id INTEGER,
        completion_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    ''')
    
    conn.commit()
    return conn

# 2. Helper Functions (The App Logic)

def register_user(conn, name, role, specialty, license):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (full_name, role, specialty, license_number) VALUES (?, ?, ?, ?)",
                   (name, role, specialty, license))
    conn.commit()
    print(f"✅ User Registered: {name}")
    return cursor.lastrowid

def add_course(conn, title, provider, credits):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (title, provider, cme_credits) VALUES (?, ?, ?)",
                   (title, provider, credits))
    conn.commit()

def mark_course_complete(conn, user_id, course_id):
    """This represents the user clicking 'I finished this'"""
    date = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO certificates (user_id, course_id, completion_date) VALUES (?, ?, ?)",
                   (user_id, course_id, date))
    conn.commit()
    print(f"🏆 Certificate Issued for User ID {user_id}")

def generate_digital_cv(conn, user_id):
    """Queries the database to build the CV"""
    cursor = conn.cursor()
    
    # Get User Details
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    # Get Their Completed Courses
    query = '''
    SELECT c.title, c.provider, c.cme_credits, cert.completion_date 
    FROM certificates cert
    JOIN courses c ON cert.course_id = c.course_id
    WHERE cert.user_id = ?
    '''
    cursor.execute(query, (user_id,))
    certificates = cursor.fetchall()
    
    # --- DISPLAY THE CV ---
    print("\n" + "="*40)
    print(f"DIGITAL CV: {user[1]}")
    print("="*40)
    print(f"Role: {user[2]}")
    print(f"Specialty: {user[3]}")
    print(f"License #: {user[4]}")
    print("-" * 40)
    print("CONTINUOUS PROFESSIONAL DEVELOPMENT (CPD):")
    
    total_credits = 0
    for cert in certificates:
        print(f"[x] {cert[0]} ({cert[1]})")
        print(f"    Completed: {cert[3]} | Credits: {cert[2]}")
        total_credits += cert[2]
        
    print("-" * 40)
    print(f"TOTAL CME CREDITS EARNED: {total_credits}")
    print("="*40 + "\n")

# --- 3. RUN THE SIMULATION ---
if __name__ == "__main__":
    # Initialize
    db_conn = setup_database()

    # Step A: A new user signs up
    my_user_id = register_user(db_conn, "Dr. Sarah Johnson", "Doctor", "Cardiology", "MD-5592-X")

    # Step B: We populate the app with some real courses (Backend work)
    add_course(db_conn, "Infection Prevention Control", "WHO", 1.5)
    add_course(db_conn, "Management of Hypertension", "Coursera/Stanford", 3.0)
    add_course(db_conn, "Introduction to Telehealth", "CDC", 1.0)

    # Step C: The User finishes two courses
    # (In the real app, this happens when they click a button)
    mark_course_complete(db_conn, my_user_id, 1) # Finished Infection Control
    mark_course_complete(db_conn, my_user_id, 2) # Finished Hypertension

    # Step D: View the Profile/CV
    generate_digital_cv(db_conn, my_user_id)