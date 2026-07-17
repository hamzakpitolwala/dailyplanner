from datetime import date

from sqlalchemy.orm import Session, selectinload

from backend.db.models.history_table import ActivityHistoryEvent
from backend.db.models.planner_table import Activity, ActivityPolicy, DailyPlanner


def _activity_load_options():
    """Reusable selectinload options for Activity relationships."""
    return [
        selectinload(DailyPlanner.activities).selectinload(Activity.policy),
        selectinload(DailyPlanner.activities)
        .selectinload(Activity.history_events)
        .selectinload(ActivityHistoryEvent.missed_reason),
        selectinload(DailyPlanner.activities)
        .selectinload(Activity.history_events)
        .selectinload(ActivityHistoryEvent.alternate_activity),
    ]
from backend.schemas.planner_schema import (
    ActivityCreate,
    ActivityPolicyBase,
    ActivityUpdate,
    DailyPlannerCreate,
    DailyPlannerUpdate,
)


class PlannerService:
    def list_planners(self, db: Session, user_id: int) -> list[DailyPlanner]:
        return (
            db.query(DailyPlanner)
            .options(*_activity_load_options())
            .filter(DailyPlanner.user_id == user_id)
            .order_by(DailyPlanner.planner_date.desc())
            .all()
        )

    def get_planner(self, db: Session, user_id: int, planner_id: int) -> DailyPlanner | None:
        return (
            db.query(DailyPlanner)
            .options(*_activity_load_options())
            .filter(DailyPlanner.id == planner_id, DailyPlanner.user_id == user_id)
            .first()
        )

    def get_planner_by_date(
        self, db: Session, user_id: int, planner_date: date
    ) -> DailyPlanner | None:
        return (
            db.query(DailyPlanner)
            .options(*_activity_load_options())
            .filter(
                DailyPlanner.user_id == user_id,
                DailyPlanner.planner_date == planner_date,
            )
            .first()
        )

    def get_or_create_planner_for_date(
        self, db: Session, user_id: int, planner_date: date
    ) -> DailyPlanner:
        planner = self.get_planner_by_date(db, user_id, planner_date)
        if planner:
            return planner

        planner = DailyPlanner(
            user_id=user_id,
            planner_date=planner_date,
            title=f"Planner for {planner_date.isoformat()}",
        )
        db.add(planner)
        db.commit()
        db.refresh(planner)
        return self.get_planner(db, user_id, planner.id) or planner

    def create_planner(
        self, db: Session, user_id: int, data: DailyPlannerCreate
    ) -> DailyPlanner:
        if self.get_planner_by_date(db, user_id, data.planner_date):
            raise ValueError("Planner already exists for this date")

        planner = DailyPlanner(user_id=user_id, **data.model_dump())
        db.add(planner)
        db.commit()
        db.refresh(planner)
        return self.get_planner(db, user_id, planner.id) or planner

    def update_planner(
        self, db: Session, planner: DailyPlanner, data: DailyPlannerUpdate
    ) -> DailyPlanner:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(planner, field, value)
        db.commit()
        db.refresh(planner)
        return planner

    def delete_planner(self, db: Session, planner: DailyPlanner) -> None:
        db.delete(planner)
        db.commit()

    def create_activity(
        self, db: Session, planner: DailyPlanner, data: ActivityCreate
    ) -> Activity:
        payload = data.model_dump(exclude={"policy"})
        activity = Activity(user_id=planner.user_id, planner_id=planner.id, **payload)
        db.add(activity)
        db.flush()

        policy_data = data.policy or ActivityPolicyBase()
        db.add(ActivityPolicy(activity_id=activity.id, **policy_data.model_dump()))
        db.commit()
        db.refresh(activity)
        return activity

    def get_activity(self, db: Session, user_id: int, activity_id: int) -> Activity | None:
        return (
            db.query(Activity)
            .options(
                selectinload(Activity.policy),
                selectinload(Activity.history_events).selectinload(ActivityHistoryEvent.missed_reason),
                selectinload(Activity.history_events).selectinload(ActivityHistoryEvent.alternate_activity),
            )
            .filter(Activity.id == activity_id, Activity.user_id == user_id)
            .first()
        )

    def update_activity(
        self, db: Session, activity: Activity, data: ActivityUpdate
    ) -> Activity:
        payload = data.model_dump(exclude_unset=True, exclude={"policy"})
        for field, value in payload.items():
            setattr(activity, field, value)

        if data.policy is not None:
            if activity.policy is None:
                activity.policy = ActivityPolicy(activity_id=activity.id)
            for field, value in data.policy.model_dump().items():
                setattr(activity.policy, field, value)

        db.commit()
        db.refresh(activity)
        return activity

    def delete_activity(self, db: Session, activity: Activity) -> None:
        db.delete(activity)
        db.commit()
