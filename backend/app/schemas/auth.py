from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    company_name: str = Field(min_length=2, max_length=255)
    inn: str | None = Field(default=None, max_length=12)
    consent: bool
    website: str | None = None

    @field_validator("consent")
    @classmethod
    def _consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Необходимо согласие на обработку персональных данных")
        return v

    @field_validator("inn")
    @classmethod
    def _inn(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        if v and (not v.isdigit() or len(v) not in (10, 12)):
            raise ValueError("ИНН должен содержать 10 или 12 цифр")
        return v or None


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailIn(BaseModel):
    email: EmailStr


class TokenIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ResetConfirmIn(TokenIn):
    password: str = Field(min_length=8, max_length=128)


class OrganizationOut(BaseModel):
    id: int
    name: str
    inn: str | None = None
    kpp: str | None = None
    legal_address: str | None = None
    phone: str | None = None
    email: str | None = None


class MeOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    patronymic: str | None = None
    phone: str | None = None
    position: str | None = None
    role: str
    organization: OrganizationOut | None = None
    csrf_token: str | None = None
