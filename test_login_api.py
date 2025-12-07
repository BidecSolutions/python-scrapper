"""Test login API directly"""
import requests
import json

# Test login
url = "http://localhost:8000/api/auth/login"
payload = {
    "email": "admin@admin.com",
    "password": "123123"
}

print("=" * 70)
print("Testing Login API")
print("=" * 70)
print(f"\nURL: {url}")
print(f"Email: {payload['email']}")
print(f"Password: {payload['password']}")

try:
    response = requests.post(url, json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Login successful!")
        print(f"Token: {data.get('access_token', '')[:50]}...")
    else:
        print("\n❌ Login failed!")
        try:
            error = response.json()
            print(f"Error detail: {error.get('detail', 'Unknown error')}")
        except:
            print(f"Error: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to backend!")
    print("   Make sure the backend is running on http://localhost:8000")
    print("   Start it with: python main.py")
except Exception as e:
    print(f"\n❌ Error: {e}")

