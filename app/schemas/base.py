# app/schemas/base.py
from pydantic import ConfigDict, BaseModel


# Base configuration that can be used across all models
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
