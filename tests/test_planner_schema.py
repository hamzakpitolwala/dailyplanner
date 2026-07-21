from backend.schemas.planner_schema import ActivityCreate


def test_activity_create_normalizes_empty_time_strings_to_none():
    payload = ActivityCreate(title="Write plan", start_time="", end_time="")

    assert payload.start_time is None
    assert payload.end_time is None
