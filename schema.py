from typing import Literal, Optional
from pydantic import BaseModel, Field

class JobPosting(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    remote: Optional[Literal["onsite", "hybrid", "remote"]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    years_experience: Optional[int] = None