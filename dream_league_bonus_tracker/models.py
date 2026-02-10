"""Pydantic models for Dream League Bonus Tracker API responses and data."""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, Field

# -- Bonus mapping --

class BonusType(IntEnum):
    """Enum mapping bonus IDs to their names."""

    TRIPLE_CAPTAIN = 1
    FIFTEEN_SUBS = 2
    DOUBLE_CAPTAINS = 3
    FULL_SQUAD_POINTS = 4


BONUS_NAMES: dict[int, str] = {
    BonusType.TRIPLE_CAPTAIN: "Triple Captain",
    BonusType.FIFTEEN_SUBS: "15 Subs",
    BonusType.DOUBLE_CAPTAINS: "Double Captains",
    BonusType.FULL_SQUAD_POINTS: "Full Squad Points",
}

ALL_BONUS_IDS: set[int] = {bonus.value for bonus in BonusType}


# -- Raw API response models (from Sport5) --

class BonusData(BaseModel):
    """A single bonus usage record from the Sport5 API."""

    bonus_id: int = Field(alias="bonusId")
    usage_round_id: int = Field(alias="usageRoundId")
    usage_date: datetime = Field(alias="usageDate")

    model_config = {"populate_by_name": True}


class UserInfo(BaseModel):
    """User info from GetUserAndTeam response."""

    id: int
    email: Optional[str] = None
    full_name: Optional[str] = Field(default=None, alias="fullName")

    model_config = {"populate_by_name": True}


class UserTeamRaw(BaseModel):
    """Raw user team data from GetUserAndTeam response."""

    id: int
    user_id: int = Field(alias="userId")
    name: str
    creator_name: str = Field(alias="creatorName")
    points: int
    bonuses_data: list[BonusData] = Field(default_factory=list, alias="bonusesData")

    model_config = {"populate_by_name": True}


class GetUserAndTeamResponse(BaseModel):
    """Full response from GetUserAndTeam API endpoint."""

    result: bool
    error: Optional[str] = None
    data: Optional[UserAndTeamData] = None


class UserAndTeamData(BaseModel):
    """Data payload from GetUserAndTeam response."""

    user: UserInfo
    user_team: UserTeamRaw = Field(alias="userTeam")

    model_config = {"populate_by_name": True}


# -- League API response models --

class TeamInLeague(BaseModel):
    """A team entry in the league data response."""

    user_id: int = Field(alias="userId")
    name: str
    user_name: str = Field(alias="userName")
    total_score: int = Field(alias="totalScore")
    round_score: int = Field(alias="roundScore")
    position: int

    model_config = {"populate_by_name": True}


class CustomLeague(BaseModel):
    """Custom league metadata."""

    id: int
    season_id: int = Field(alias="seasonId")
    name: str

    model_config = {"populate_by_name": True}


class LeagueResponseData(BaseModel):
    """Data payload from GetLeagueData response."""

    league_name: str = Field(alias="leagueName")
    custom_league: CustomLeague = Field(alias="customLeague")
    teams: list[TeamInLeague]

    model_config = {"populate_by_name": True}


class GetLeagueDataResponse(BaseModel):
    """Full response from GetLeagueData API endpoint."""

    result: bool
    error: Optional[str] = None
    data: Optional[LeagueResponseData] = None


# -- Output models (what our API returns) --

class BonusUsage(BaseModel):
    """A single bonus usage detail for output."""

    bonus_id: int
    bonus_name: str
    usage_round_id: int
    usage_date: datetime


class TeamBonusStatus(BaseModel):
    """Bonus usage status for a single team."""

    user_id: int
    team_name: str
    creator_name: str
    total_points: int
    used_bonuses: list[BonusUsage]
    remaining_bonuses: list[str]
    used_count: int
    remaining_count: int


class LeagueBonusReport(BaseModel):
    """Bonus usage report for an entire league."""

    league_id: int
    league_name: str
    season_id: int
    teams: list[TeamBonusStatus]


# Resolve forward references
GetUserAndTeamResponse.model_rebuild()
