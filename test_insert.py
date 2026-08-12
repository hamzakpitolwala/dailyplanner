import asyncio
from sqlalchemy import select
from backend.db.database import SessionLocal
from backend.db.models.templates import PlannerTemplate, TemplateTask
import datetime

async def test_insert():
    async with SessionLocal() as session:
        # just try to insert a template task to see if it works
        task = TemplateTask(
            template_id='b4dd83a6-e091-4d8c-b920-08cb170e53a9',
            title='Test Task',
            target_time='10:00:00'
        )
        session.add(task)
        try:
            await session.commit()
            print("Insert successful")
        except Exception as e:
            print("Error:", str(e))

asyncio.run(test_insert())
