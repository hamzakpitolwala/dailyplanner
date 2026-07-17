"""Service layer for activity history and state machine."""

from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from backend.db.models.history_table import (
    ActivityHistoryEvent,
    AlternateActivity,
    MissedReason,
)
from backend.db.models.planner_table import Activity, ActivityPolicy
from backend.schemas.history_schema import ActionType, ActivityStatus, HistoryEventCreate
import datetime


class ActivityStateMachine:
    """Strict state machine for Activity transitions."""

    # Define valid transitions from a given state
    VALID_TRANSITIONS = {
        ActivityStatus.planned: {
            ActivityStatus.in_progress,
            ActivityStatus.partial,
            ActivityStatus.done,
            ActivityStatus.not_done,
            ActivityStatus.rescheduled,
            ActivityStatus.cancelled,
        },
        ActivityStatus.in_progress: {
            ActivityStatus.partial,
            ActivityStatus.done,
            ActivityStatus.not_done,
            ActivityStatus.rescheduled,
            ActivityStatus.cancelled,
        },
        ActivityStatus.partial: {
            ActivityStatus.done,
            ActivityStatus.not_done,
            ActivityStatus.rescheduled,
            ActivityStatus.cancelled,
        },
        ActivityStatus.done: set(),
        ActivityStatus.not_done: set(),
        ActivityStatus.rescheduled: set(),
        ActivityStatus.cancelled: set(),
    }

    @classmethod
    def validate_transition(
        cls, current_state: str, new_state: ActivityStatus, end_time=None
    ):
        """Validate if the transition is allowed."""
        if current_state == new_state.value:
            return  # No change

        # Ensure transition is valid
        allowed_states = cls.VALID_TRANSITIONS.get(ActivityStatus(current_state), set())
        if new_state not in allowed_states:
            raise ValueError(
                f"Invalid transition from {current_state} to {new_state.value}"
            )

        # Enforce "time is over" logic for partial tasks (implemented later in Slice 4)


class HistoryService:
    """Handles activity history logging and state transitions."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def record_event(
        self,
        db: Session,
        user_id: int,
        activity: Activity,
        data: HistoryEventCreate,
    ) -> ActivityHistoryEvent:
        """Record an event, enforce state machine / policy, and update activity.

        Raises ``ValueError`` on invalid transition or policy violation.
        """
        current_state = activity.status

        if data.action_type == ActionType.status_change:
            ActivityStateMachine.validate_transition(current_state, data.new_state, activity.end_time)

            # --- Enforce policy for not_done status ---
            if data.new_state == ActivityStatus.not_done:
                policy = activity.policy
                if policy and policy.requires_reason and data.missed_reason is None:
                    raise ValueError(
                        "A reason is required when marking this activity as not done."
                    )
            # (If allows_alternate is false, we simply ignore any provided alternate)

            # --- Reschedule logic ---
            if data.new_state == ActivityStatus.rescheduled:
                if not data.target_date:
                    raise ValueError("target_date is required when rescheduling.")
                try:
                    target_date = datetime.date.fromisoformat(data.target_date)
                except ValueError:
                    raise ValueError("Invalid target_date format. Use YYYY-MM-DD.")
                
                # Prevent scheduling if time has conflict - for now we just create it on the target date.
                from backend.services.planner_service import PlannerService
                planner_svc = PlannerService()
                target_planner = planner_svc.get_or_create_planner_for_date(db, user_id, target_date)
                
                # Basic conflict check: same start/end time
                if activity.start_time and activity.end_time:
                    for exist_act in target_planner.activities:
                        if exist_act.start_time == activity.start_time and exist_act.end_time == activity.end_time and exist_act.status not in ("cancelled", "rescheduled"):
                            raise ValueError(f"Time conflict on {target_date.isoformat()} with activity: {exist_act.title}")

                # Create carryover activity
                carryover = Activity(
                    user_id=user_id,
                    planner_id=target_planner.id,
                    title=activity.title,
                    description=activity.description,
                    category=activity.category,
                    start_time=activity.start_time,
                    end_time=activity.end_time,
                    status="planned",
                    carried_over_from_id=activity.id
                )
                db.add(carryover)
                db.flush()
                # Carryover gets default policy
                db.add(ActivityPolicy(activity_id=carryover.id, requires_reason=True, allows_alternate=True))

        # --- Persist the event ---
        event = ActivityHistoryEvent(
            activity_id=activity.id,
            user_id=user_id,
            action_type=data.action_type.value,
            previous_state=current_state if data.action_type == ActionType.status_change else None,
            new_state=data.new_state.value,
            notes=data.notes,
        )
        db.add(event)
        db.flush()  # get event.id

        # --- Conditional child records ---
        if data.new_state == ActivityStatus.not_done:
            if data.missed_reason is not None:
                db.add(
                    MissedReason(
                        history_event_id=event.id,
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
                        history_event_id=event.id,
                        description=data.alternate_activity.description,
                        category=data.alternate_activity.category,
                    )
                )

        # --- Update the activity's status column if changed ---
        if data.action_type == ActionType.status_change:
            activity.status = data.new_state.value
            
        db.commit()
        db.refresh(event)

        return self._load_event(db, event.id)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_events_for_activity(
        self, db: Session, user_id: int, activity_id: int
    ) -> list[ActivityHistoryEvent]:
        """Return all history events for an activity, newest first."""
        return (
            db.query(ActivityHistoryEvent)
            .options(
                selectinload(ActivityHistoryEvent.missed_reason),
                selectinload(ActivityHistoryEvent.alternate_activity),
            )
            .filter(
                ActivityHistoryEvent.activity_id == activity_id,
                ActivityHistoryEvent.user_id == user_id,
            )
            .order_by(ActivityHistoryEvent.timestamp.desc())
            .all()
        )

    def get_event(
        self, db: Session, user_id: int, event_id: int
    ) -> ActivityHistoryEvent | None:
        """Return a single history event by id if it belongs to the user."""
        return self._load_event_for_user(db, user_id, event_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_event(db: Session, event_id: int) -> ActivityHistoryEvent:
        return (
            db.query(ActivityHistoryEvent)
            .options(
                selectinload(ActivityHistoryEvent.missed_reason),
                selectinload(ActivityHistoryEvent.alternate_activity),
            )
            .filter(ActivityHistoryEvent.id == event_id)
            .one()
        )

    @staticmethod
    def _load_event_for_user(
        db: Session, user_id: int, event_id: int
    ) -> ActivityHistoryEvent | None:
        return (
            db.query(ActivityHistoryEvent)
            .options(
                selectinload(ActivityHistoryEvent.missed_reason),
                selectinload(ActivityHistoryEvent.alternate_activity),
            )
            .filter(
                ActivityHistoryEvent.id == event_id,
                ActivityHistoryEvent.user_id == user_id,
            )
            .first()
        )
