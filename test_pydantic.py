from backend.schemas.template_schema import TemplateTaskCreate
import datetime

payload = {
    "title": "Test Task",
    "target_time": "10:00:00"
}
obj = TemplateTaskCreate(**payload)
print(repr(obj.target_time))
print(type(obj.target_time))
dumped = obj.model_dump()
print(repr(dumped['target_time']))
print(type(dumped['target_time']))
