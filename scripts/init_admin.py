import requests
import sys

# Configuration
API_URL = "http://localhost:5001/console/api/setup"
ADMIN_EMAIL = "kaijie.yu@cgu.edu"  # Default to teacher
ADMIN_NAME = "Yuri"
ADMIN_PASSWORD = "password123"

def init_admin():
    print(f"Attempting to initialize admin account: {ADMIN_EMAIL}")
    
    payload = {
        "email": ADMIN_EMAIL,
        "name": ADMIN_NAME,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 201:
            print("✅ Admin account created successfully!")
            print(f"Email: {ADMIN_EMAIL}")
            print(f"Password: {ADMIN_PASSWORD}")
        elif response.status_code == 403:
            print("⚠️  System is already initialized. Cannot create admin account via setup endpoint.")
        else:
            print(f"❌ Failed to create admin account. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")

if __name__ == "__main__":
    init_admin()
