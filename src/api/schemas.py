from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientRegister(BaseModel):
    email: str
    password: str
    company_name: str


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    company_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ScanRequest(BaseModel):
    target: str


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    severity: str
    title: str
    detail: str
    recommendation: str


class ScanRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target: str
    score: int
    created_at: datetime
    findings: list[FindingOut]


class ScanSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target: str
    score: int
    created_at: datetime
