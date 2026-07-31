import requests
import json

# Register user
user = {"email": "test_popup@example.com", "password": "password", "timezone": "UTC"}
requests.post("http://localhost:8000/auth/register", json=user)

# Login
resp = requests.post("http://localhost:8000/auth/token", data={"username": "test_popup@example.com", "password": "password"})
token = resp.json()["access_token"]

# Create task
headers = {"Authorization": f"Bearer {token}"}
task_data = {
    "title": "Popup Task",
    "requires_reason": True,
    "allows_alternate": True
}
resp = requests.post("http://localhost:8000/tasks", json=task_data, headers=headers)
print("Create Task Response:", resp.status_code, resp.text)
