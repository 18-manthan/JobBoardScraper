from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    description: Optional[str] = ""
    url: str
    source: Optional[str] = "Unknown"
    liked: Optional[bool] = False
    applied: Optional[bool] = False
    
    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class JobStatusUpdate(BaseModel):
    title: Optional[str] = None
    liked: Optional[bool] = None
    applied: Optional[bool] = None
