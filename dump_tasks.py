import os
import sqlalchemy as sa
from backend.core.config import settings

engine = sa.create_engine(settings.DATABASE_URL)
insp = sa.inspect(engine)
print("tasks columns:")
for c in insp.get_columns("tasks"):
    print(c["name"], ":", c["type"])
