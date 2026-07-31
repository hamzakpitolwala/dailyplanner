import os
import sqlalchemy as sa
from dotenv import load_dotenv
load_dotenv()
engine = sa.create_engine(os.environ["DATABASE_URL"])
insp = sa.inspect(engine)
print("users.id type:", insp.get_columns("users")[0]["type"])
print("tasks.user_id type:", [c for c in insp.get_columns("tasks") if c["name"] == "user_id"][0]["type"])
