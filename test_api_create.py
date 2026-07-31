from dotenv import load_dotenv
load_dotenv()
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import SessionLocal
from backend.db.models.core import User
from backend.core.jwt import create_access_token

db = SessionLocal()
user = db.query(User).first()
token = create_access_token(data={"sub": str(user.id)})
client = TestClient(app)

res_post = client.post(
    "/tasks",
    headers={"Authorization": f"Bearer {token}"},
    json={"title": "Test Timezone Task", "due_date": "2026-07-30T00:00:00"}
)
print("POST Response:", res_post.json())
