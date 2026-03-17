from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import re


class RegisterSchema(BaseModel):

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Enter full name (First and Last name)"
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Password must contain uppercase, lowercase, number and special character"
    )

    confirm_password: str

    # -------- Name Validation --------
    @field_validator("name")
    @classmethod
    def validate_name(cls, value):

        value = value.strip()

        # Check if full name entered
        if len(value.split()) < 2:
            raise ValueError("Please enter your full name (first and last name)")

        # Only allow alphabets and spaces
        if not re.match(r"^[A-Za-z ]+$", value):
            raise ValueError("Name must contain only letters and spaces")

        return value

    # -------- Password Strength --------
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character")

        return value

    # -------- Password Match --------
    @model_validator(mode="after")
    def check_password_match(self):

        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str