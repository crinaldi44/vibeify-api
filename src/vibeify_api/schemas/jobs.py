from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: dict = {}

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )