from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    legal_name: str = Field(min_length=1)
    mobile: str = Field(min_length=10, max_length=15)
    pan: str = Field(pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    primary_role: str = Field(pattern=r"^(INDIVIDUAL|BUSINESS|CA|ADMIN)$")

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(
        min_length=12,
        description="Password must be at least 12 characters and contain at least one uppercase letter, one lowercase letter, one digit, and one special character."
    )

    @field_validator('password', mode='before')
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('password')
    def validate_password_complexity(cls, v):
        if isinstance(v, str):
            import re
            if not re.search(r"[A-Z]", v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not re.search(r"[a-z]", v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not re.search(r"\d", v):
                raise ValueError("Password must contain at least one digit")
            if not re.search(r"[@$!%*?&]", v):
                raise ValueError("Password must contain at least one special character")
        return v

# Properties to receive via API on login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Properties for password change
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(
        min_length=12,
        description="Password must be at least 12 characters and contain at least one uppercase letter, one lowercase letter, one digit, and one special character."
    )

    @field_validator('new_password', mode='before')
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('new_password')
    def validate_password_complexity(cls, v):
        if isinstance(v, str):
            import re
            if not re.search(r"[A-Z]", v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not re.search(r"[a-z]", v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not re.search(r"\d", v):
                raise ValueError("Password must contain at least one digit")
            if not re.search(r"[@$!%*?&]", v):
                raise ValueError("Password must contain at least one special character")
        return v

# Properties to return via API
class UserResponse(UserBase):
    id: UUID
    account_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
