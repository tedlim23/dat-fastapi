from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}


class PriceBase(MongoBaseModel):
    ticker: str
    content: str
    publication_date: datetime = Field(default_factory=datetime.now)


class PricePartialUpdate(BaseModel):
    ticker: Optional[str] = None
    content: Optional[str] = None


class PriceCreate(PriceBase):
    pass

class PriceDB(PriceBase):
    pass