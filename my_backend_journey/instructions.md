# HOW TO INSTALL VENV
### 1. Create a new folder for your project
mkdir my_backend_app
cd my_backend_app

### 2. Create a virtual environment named "venv"
python -m venv venv

### 3. Activate the environment
# Windows:
venv\Scripts\activate
### Mac/Linux:
source venv/bin/activate

### (You should see (venv) appear in your terminal prompt)

### 4. Install the engine and the framework
pip install fastapi uvicorn