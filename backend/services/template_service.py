"""Service layer for planner and activity templates."""

from sqlalchemy.orm import Session, selectinload

from backend.db.models.template_table import PlannerTemplate, ActivityTemplate
from backend.schemas.template_schema import (
    PlannerTemplateCreate,
    PlannerTemplateUpdate,
    ActivityTemplateCreate,
    ActivityTemplateUpdate,
)


class TemplateService:
    # ------------------------------------------------------------------
    # Planner Templates
    # ------------------------------------------------------------------

    def list_templates(self, db: Session, user_id: int) -> list[PlannerTemplate]:
        return (
            db.query(PlannerTemplate)
            .options(selectinload(PlannerTemplate.activity_templates))
            .filter(PlannerTemplate.user_id == user_id)
            .order_by(PlannerTemplate.created_at.desc())
            .all()
        )

    def get_template(self, db: Session, user_id: int, template_id: int) -> PlannerTemplate | None:
        return (
            db.query(PlannerTemplate)
            .options(selectinload(PlannerTemplate.activity_templates))
            .filter(PlannerTemplate.id == template_id, PlannerTemplate.user_id == user_id)
            .first()
        )
        
    def get_in_use_template(self, db: Session, user_id: int) -> PlannerTemplate | None:
        return (
            db.query(PlannerTemplate)
            .options(selectinload(PlannerTemplate.activity_templates))
            .filter(PlannerTemplate.user_id == user_id, PlannerTemplate.in_use == True)
            .first()
        )

    def create_template(
        self, db: Session, user_id: int, data: PlannerTemplateCreate
    ) -> PlannerTemplate:
        # If this is set to in_use, unset others
        if data.in_use:
            self._unset_in_use(db, user_id)

        template = PlannerTemplate(user_id=user_id, **data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def update_template(
        self, db: Session, user_id: int, template: PlannerTemplate, data: PlannerTemplateUpdate
    ) -> PlannerTemplate:
        if data.in_use and not template.in_use:
            self._unset_in_use(db, user_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)
        return template

    def delete_template(self, db: Session, template: PlannerTemplate) -> None:
        db.delete(template)
        db.commit()

    def _unset_in_use(self, db: Session, user_id: int) -> None:
        db.query(PlannerTemplate).filter(
            PlannerTemplate.user_id == user_id, PlannerTemplate.in_use == True
        ).update({"in_use": False})
        db.flush()

    # ------------------------------------------------------------------
    # Activity Templates
    # ------------------------------------------------------------------

    def create_activity_template(
        self, db: Session, template: PlannerTemplate, data: ActivityTemplateCreate
    ) -> ActivityTemplate:
        activity = ActivityTemplate(planner_template_id=template.id, **data.model_dump())
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity

    def get_activity_template(self, db: Session, template_id: int, activity_id: int) -> ActivityTemplate | None:
        return (
            db.query(ActivityTemplate)
            .filter(
                ActivityTemplate.id == activity_id,
                ActivityTemplate.planner_template_id == template_id,
            )
            .first()
        )

    def update_activity_template(
        self, db: Session, activity: ActivityTemplate, data: ActivityTemplateUpdate
    ) -> ActivityTemplate:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(activity, field, value)
        db.commit()
        db.refresh(activity)
        return activity

    def delete_activity_template(self, db: Session, activity: ActivityTemplate) -> None:
        db.delete(activity)
        db.commit()
