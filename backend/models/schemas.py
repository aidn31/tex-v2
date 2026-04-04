from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Teams ---

class TeamCreate(BaseModel):
    name: str
    level: str = "unknown"


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None


class TeamResponse(BaseModel):
    id: str
    name: str
    level: str
    created_at: datetime
    updated_at: datetime
