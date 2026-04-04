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


# --- Roster Players ---

class RosterPlayerCreate(BaseModel):
    team_id: str
    jersey_number: str
    full_name: str
    position: Optional[str] = None
    height: Optional[str] = None
    dominant_hand: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class RosterPlayerUpdate(BaseModel):
    jersey_number: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    height: Optional[str] = None
    dominant_hand: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class RosterPlayerResponse(BaseModel):
    id: str
    team_id: str
    jersey_number: str
    full_name: str
    position: Optional[str]
    height: Optional[str]
    dominant_hand: Optional[str]
    role: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
