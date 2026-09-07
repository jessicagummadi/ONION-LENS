from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    inspector_id: str = Field(..., description="Inspector ID or Mobile Number")
    pin: str = Field(..., min_length=4, max_length=16, description="Security PIN / Password")
    yard: Optional[str] = Field("Nashik APMC Main Yard #4", description="Procurement yard name")

class RegisterRequest(BaseModel):
    inspector_id: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=2, max_length=128)
    pin: str = Field(..., min_length=4, max_length=16)
    yard: Optional[str] = "Nashik APMC Main Yard #4"
    role: Optional[str] = "Inspector"

class UserResponse(BaseModel):
    id: int
    inspector_id: str
    name: str
    yard: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
