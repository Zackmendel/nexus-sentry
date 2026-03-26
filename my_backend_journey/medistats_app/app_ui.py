import streamlit as st
import requests
import pandas as pd

# CONFIGURATION
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="MedConnect", page_icon="🩺", layout="wide")

# --- SESSION STATE (Memory for the current user) ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🩺 MedConnect")
if st.session_state['user_name']:
    st.sidebar.success(f"Welcome, {st.session_state['user_name']}")
    menu = ["News Feed", "Course Catalog", "My Profile & CV"]
else:
    st.sidebar.warning("Please Sign Up to access features.")
    menu = ["Sign Up"]

choice = st.sidebar.radio("Go to:", menu)

# ==============================================
# 1. SIGN UP PAGE
# ==============================================
if choice == "Sign Up":
    st.title("Create Your Professional Profile")
    st.write("Join thousands of medical practitioners staying ahead.")
    
    # Check if we are already logged in to avoid showing the form again
    if st.session_state['user_id']:
        st.success(f"You are already logged in as {st.session_state['user_name']}")
        st.info("Use the sidebar to navigate to News or Courses.")
    else:
        with st.form("signup_form"):
            name = st.text_input("Full Name (e.g. Dr. Chioma Adebayo)")
            role = st.selectbox("Role", ["Doctor", "Nurse", "Pharmacist", "Medical Student"])
            specialty = st.text_input("Specialty (e.g. Pediatrics, Cardiology)")
            license_num = st.text_input("License Number")
            submit = st.form_submit_button("Create Account")
            
            if submit:
                if name and license_num:
                    # Send data to FastAPI
                    payload = {
                        "name": name, "role": role, 
                        "specialty": specialty, "license_number": license_num
                    }
                    try:
                        response = requests.post(f"{API_URL}/signup", json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state['user_id'] = data['user_id']
                            st.session_state['user_name'] = name
                            
                            st.success("Account created! Redirecting...")
                            
                            # --- THE FIX IS HERE ---
                            st.rerun() 
                            # -----------------------
                            
                        else:
                            st.error("Error creating account.")
                    except Exception as e:
                        st.error(f"Could not connect to backend. Is main.py running? Error: {e}")
                else:
                    st.warning("Please fill in all details.")

# ==============================================
# 2. NEWS FEED (Trends)
# ==============================================
elif choice == "News Feed":
    st.title("📢 Global Medical Trends")
    st.write("Real-time updates from PubMed.")
    
    # Search Bar
    topic = st.text_input("Enter a medical topic:", value="Public Health")
    
    if st.button("Get Latest News"):
        with st.spinner(f"Searching latest research on {topic}..."):
            try:
                response = requests.get(f"{API_URL}/news/{topic}")
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    
                    for article in articles:
                        with st.expander(f"📄 {article['title']}"):
                            st.write(article['summary'])
                            st.markdown(f"[Read Full Paper on PubMed]({article['link']})")
                else:
                    st.error("Failed to fetch news.")
            except:
                st.error("Backend connection failed.")

# ==============================================
# 3. COURSE CATALOG (Education)
# ==============================================
elif choice == "Course Catalog":
    st.title("🎓 Accredited Micro-Courses")
    
    try:
        response = requests.get(f"{API_URL}/courses")
        if response.status_code == 200:
            courses = response.json()['courses']
            
            # Display as Cards
            for course in courses:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"{course['title']}")
                    st.write(f"**Provider:** {course['provider']} | **Credits:** {course['cme_credits']} CME")
                    st.caption(f"Category: {course['category']}")
                with col2:
                    st.write("") # Spacer
                    # The "Complete" button simulates finishing the course
                    if st.button(f"Mark Complete", key=course['course_id']):
                        payload = {
                            "user_id": st.session_state['user_id'],
                            "course_id": course['course_id']
                        }
                        res = requests.post(f"{API_URL}/complete_course", json=payload)
                        if res.status_code == 200:
                            st.success(f"Completed: {course['title']}")
                        
                st.divider()
        else:
            st.error("Could not load courses.")
    except:
        st.error("Backend is not running.")

# ==============================================
# 4. PROFILE & CV (Career)
# ==============================================
elif choice == "My Profile & CV":
    st.title("💼 My Professional Portfolio")
    
    st.info("Your certificates are automatically tracked here.")
    
    # Check if user has an ID
    user_id = st.session_state['user_id']
    
    if user_id:
        st.write("Click below to generate your official PDF CV.")
        
        # We need to fetch the binary PDF data from the API
        if st.button("📄 Generate & Download CV"):
            try:
                response = requests.get(f"{API_URL}/download_cv/{user_id}")
                
                if response.status_code == 200:
                    st.download_button(
                        label="📥 Click to Save PDF",
                        data=response.content,
                        file_name=f"Medical_CV_{st.session_state['user_name']}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Could not generate CV. Have you completed any courses?")
            except:
                st.error("Backend error.")