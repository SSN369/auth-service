import requests

url = "http://localhost:5001/auth/register"  # change to your actual endpoint

NEW_USER_DATA = {
    'username': 'admin1',
    'password': 'admin1',
    'email': 'admin@12345',
    'full_name': 'admin1',
    'role_name': 'Admin'  # Must match a role_name in your 'roles' table
}

response = requests.post(url, json=NEW_USER_DATA)

print("Status Code:", response.status_code)
print("Response:", response.text)

