import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User

app = create_app()

def run_tests():
    with app.test_client() as client:
        print("Testing / route...")
        resp = client.get('/')
        print(f"/ status: {resp.status_code}")
        if resp.status_code != 200:
            print("Error on /")
        
        print("\nTesting /auth/login (GET)...")
        resp = client.get('/auth/login')
        print(f"/auth/login GET status: {resp.status_code}")
        
        print("\nTesting /auth/login (POST)...")
        # Find a user to log in
        with app.app_context():
            user = User.query.first()
            if not user:
                print("No users found in database.")
                return
            username = user.username
            password = 'password123' # Assuming default test password
            print(f"Attempting to log in as {username} (Role: {user.user_type})")
            
        resp = client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)
        print(f"Login POST status: {resp.status_code}")
        
        with client.session_transaction() as sess:
            role = sess.get('user_role')
            print(f"Logged in role: {role}")
            
            # Request the appropriate dashboard
            if role:
                dash_url = f"/{role.lower()}/dashboard"
                print(f"\nTesting dashboard route: {dash_url}")
                resp = client.get(dash_url)
                print(f"{dash_url} status: {resp.status_code}")
                if resp.status_code == 200:
                    print("Dashboard loaded successfully.")
                else:
                    print(f"Dashboard failed to load. Response: {resp.data[:200]}")
            else:
                print("Login failed, no role in session.")

if __name__ == '__main__':
    run_tests()
