"""Service layer for activity check-ins."""

from sqlalchemy.orm import Session, selectinload

from backend.db.models.checkin_table import (
    ActivityCheckin,
    AlternateActivity,
    MissedReason,
)
from backend.db.models.planner_table import Activity
from backend.schemas.checkin_schema import CheckinCreate, CheckinStatus


class CheckinService:
    """Handles check-in creation, validation, and retrieval."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_checkin(
        self,
        db: Session,
        user_id: int,
        activity: Activity,
        data: CheckinCreate,
    ) -> ActivityCheckin:
        """Create a check-in, enforce policy rules, and update activity status.

        Raises ``ValueError`` when the payload violates the activity's policy.
        """
        # --- Enforce policy for not_done status ---
        if data.status == CheckinStatus.not_done:
            policy = activity.policy
            if policy and policy.requires_reason and data.missed_reason is None:
                raise ValueError(
                    "A reason is required when marking this activity as not done."
                )
        # (If allows_alternate is false, we simply ignore any provided alternate)

        # --- Persist the check-in ---
        checkin = ActivityCheckin(
            activity_id=activity.id,
            user_id=user_id,
            status=data.status.value,
            notes=data.notes,
        )
        db.add(checkin)
        db.flush()  # get checkin.id

        # --- Conditional child records ---
        if data.status == CheckinStatus.not_done:
            if data.missed_reason is not None:
                db.add(
                    MissedReason(
                        checkin_id=checkin.id,
                        reason_code=data.missed_reason.reason_code.value,
                        free_text=data.missed_reason.free_text,
                    )
                )

            if (
                data.alternate_activity is not None
                and activity.policy
                and activity.policy.allows_alternate
            ):
                db.add(
                    AlternateActivity(
                        checkin_id=checkin.id,
                        description=data.alternate_activity.description,
                        category=data.alternate_activity.category,
                    )
                )

        # --- Update the activity's status column ---
        activity.status = data.status.value
        db.commit()
        db.refresh(checkin)

        return self._load_checkin(db, checkin.id)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_checkins_for_activity(
        self, db: Session, user_id: int, activity_id: int
    ) -> list[ActivityCheckin]:
        """Return all check-ins for an activity, newest first."""
        return (
            db.query(ActivityCheckin)
            .options(
                selectinload(ActivityCheckin.missed_reason),
                selectinload(ActivityCheckin.alternate_activity),
            )
            .filter(
                ActivityCheckin.activity_id == activity_id,
                ActivityCheckin.user_id == user_id,
            )
            .order_by(ActivityCheckin.checked_in_at.desc())
            .all()
        )

    def get_checkin(
        self, db: Session, user_id: int, checkin_id: int
    ) -> ActivityCheckin | None:
        """Return a single check-in by id if it belongs to the user."""
        return self._load_checkin_for_user(db, user_id, checkin_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_checkin(db: Session, checkin_id: int) -> ActivityCheckin:
        return (
            db.query(ActivityCheckin)
            .options(
                selectinload(ActivityCheckin.missed_reason),
                selectinload(ActivityCheckin.alternate_activity),
            )
            .filter(ActivityCheckin.id == checkin_id)
            .one()
        )

    @staticmethod
    def _load_checkin_for_user(
        db: Session, user_id: int, checkin_id: int
    ) -> ActivityCheckin | None:
        return (
            db.query(ActivityCheckin)
            .options(
                selectinload(ActivityCheckin.missed_reason),
                selectinload(ActivityCheckin.alternate_activity),
            )
            .filter(
                ActivityCheckin.id == checkin_id,
                ActivityCheckin.user_id == user_id,
            )
            .first()
        )
