import sqlite3
import csv
import os

def import_courses_from_csv(csv_filename):
    # 1. Connect to your existing database
    conn = sqlite3.connect('med_app_data.db')
    cursor = conn.cursor()

    # 2. Update the table structure (Schema Migration)
    # We verify if columns exist to prevent errors if you run this script twice.
    new_columns = ["link", "category", "image_url"]
    for col in new_columns:
        try:
            cursor.execute(f"ALTER TABLE courses ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            # Column likely already exists, ignore error
            pass

    print(f"📂 Reading data from {csv_filename}...")

    # 3. Read the CSV file
    try:
        with open(csv_filename, 'r', encoding='utf-8') as file:
            # Use DictReader to handle headers automatically
            reader = csv.DictReader(file)
            
            count = 0
            for row in reader:
                # 4. Insert into Database
                cursor.execute('''
                    INSERT INTO courses (title, provider, cme_credits, link, category, image_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row['title'], 
                    row['provider'], 
                    float(row['cme_credits']), 
                    row['link'], 
                    row['category'],
                    row['image_url']
                ))
                count += 1
            
        conn.commit()
        print(f"✅ Success! Imported {count} courses into the database.")
        
        # 5. Verify the data
        print("\n--- DATABASE PREVIEW (Last 5 Uploads) ---")
        cursor.execute("SELECT title, provider, category, cme_credits FROM courses ORDER BY course_id DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"📚 {row[0]} | {row[1]} ({row[2]}) - {row[3]} Credits")

    except FileNotFoundError:
        print(f"❌ Error: The file '{csv_filename}' was not found.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        # 6. Close the connection
        conn.close()

# --- HELPER: Create a dummy CSV so you can test this right now ---
def create_dummy_csv(filename):
    if not os.path.exists(filename):
        headers = ['title', 'provider', 'cme_credits', 'link', 'category', 'image_url']
        data = [
            ['Modern Diabetes Care', 'Harvard Medical', '2.5', 'http://harvard.edu', 'Endocrinology', 'img_dia.png'],
            ['Pediatric Triage', 'WHO', '1.0', 'http://who.int', 'Pediatrics', 'img_ped.png'],
            ['AI in Radiology', 'Stanford', '3.0', 'http://stanford.edu', 'Technology', 'img_ai.png']
        ]
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        print(f"📝 Created sample file: {filename}")

# --- EXECUTION ---
if __name__ == "__main__":
    csv_file = 'courses_sample.csv'
    
    # Step A: Create a fake CSV file (so the script doesn't crash)
    create_dummy_csv(csv_file)
    
    # Step B: Run your import function
    import_courses_from_csv(csv_file)