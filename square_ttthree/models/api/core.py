"""
pydantic models for the core router endpoints.
"""

from pydantic import BaseModel


class DummyRequestModelV0(BaseModel):
    dummy: int


class DummyResponseModelV0(BaseModel):
    dummy: int


