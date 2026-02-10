"""FastAPI application for Dream League Bonus Tracker."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query

from dream_league_bonus_tracker.client import DreamTeamClient
from dream_league_bonus_tracker.config import get_settings
from dream_league_bonus_tracker.models import LeagueBonusReport, TeamBonusStatus
from dream_league_bonus_tracker.service import BonusService, BonusServiceError

logger = logging.getLogger(__name__)

# Global references for app lifespan management
_client: DreamTeamClient | None = None
_service: BonusService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - create and close the HTTP client."""
    global _client, _service

    settings = get_settings()
    _client = DreamTeamClient(settings)

    # Attempt login if credentials are provided
    if settings.email and settings.password:
        try:
            await _client.login()
            logger.info("Successfully authenticated with Sport5 API.")
        except Exception as exc:
            logger.warning("Authentication failed: %s. Continuing without auth.", exc)

    _service = BonusService(_client)

    yield

    await _client.close()
    _client = None
    _service = None


app = FastAPI(
    title="Dream League Bonus Tracker",
    description="API to track bonus usage in Sport5 Dream League fantasy football.",
    version="0.1.0",
    lifespan=lifespan,
)


def _get_service() -> BonusService:
    """Get the BonusService instance, raising if not initialized."""
    if _service is None:
        raise HTTPException(status_code=503, detail="Service not initialized.")
    return _service


@app.get("/team/{user_id}/bonuses", response_model=TeamBonusStatus)
async def get_team_bonuses(user_id: int) -> TeamBonusStatus:
    """Get bonus usage status for a specific team.

    Args:
        user_id: The Sport5 user ID.

    Returns:
        TeamBonusStatus with used and remaining bonuses.
    """
    service = _get_service()
    try:
        return await service.get_team_bonuses(user_id)
    except BonusServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/league/{league_id}/bonuses", response_model=LeagueBonusReport)
async def get_league_bonuses(
    league_id: int,
    season_id: int = Query(default=6, description="Season ID"),
) -> LeagueBonusReport:
    """Get bonus usage status for all teams in a league.

    Args:
        league_id: The custom league ID.
        season_id: The season ID (default 6).

    Returns:
        LeagueBonusReport with bonus status for every team in the league.
    """
    service = _get_service()
    try:
        return await service.get_league_bonuses(league_id, season_id=season_id)
    except BonusServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
