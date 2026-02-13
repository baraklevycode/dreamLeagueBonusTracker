"""FastAPI application for Dream League Bonus Tracker."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dream_league_bonus_tracker.client import AuthenticationError, DreamTeamClient
from dream_league_bonus_tracker.config import Settings, get_settings
from dream_league_bonus_tracker.models import (
    DEFAULT_GAME_MODE,
    GAME_MODE_NAMES,
    GameMode,
    LeagueBonusReport,
    TeamBonusStatus,
)
from dream_league_bonus_tracker.service import BonusService, BonusServiceError

def _get_static_dir() -> Path:
    """Resolve the static directory path (works both in dev and packaged .exe)."""
    import sys

    if getattr(sys, "frozen", False):
        # Running as PyInstaller .exe
        return Path(sys._MEIPASS) / "static"
    return Path(__file__).resolve().parent.parent / "static"


STATIC_DIR = _get_static_dir()

logger = logging.getLogger(__name__)

# Global references for app lifespan management
_client: DreamTeamClient | None = None
_service: BonusService | None = None
_current_email: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - create and close the HTTP client."""
    global _client, _service, _current_email

    settings = get_settings()
    _client = DreamTeamClient(settings)
    _current_email = settings.email

    # Attempt login if credentials are provided
    if settings.email and settings.password:
        try:
            await _client.login()
            logger.info("Successfully authenticated with Sport5 API as %s.", settings.email)
        except Exception as exc:
            logger.warning("Authentication failed: %s. Continuing without auth.", exc)
            _current_email = ""

    _service = BonusService(_client)

    yield

    await _client.close()
    _client = None
    _service = None
    _current_email = ""


app = FastAPI(
    title="Dream League Bonus Tracker",
    description="API to track bonus usage in Sport5 Dream League fantasy football.",
    version="0.1.0",
    lifespan=lifespan,
)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    """Serve the web UI."""
    return FileResponse(str(STATIC_DIR / "index.html"))


# -- Auth endpoints --

class LoginRequest(BaseModel):
    """Request body for the login endpoint."""

    email: str
    password: str


class AuthStatus(BaseModel):
    """Response for auth status check."""

    authenticated: bool
    email: str


@app.get("/auth/status", response_model=AuthStatus)
async def get_auth_status() -> AuthStatus:
    """Check the current authentication status."""
    return AuthStatus(
        authenticated=bool(_current_email),
        email=_current_email,
    )


@app.post("/auth/login", response_model=AuthStatus)
async def login(request: LoginRequest) -> AuthStatus:
    """Re-authenticate with Sport5 using new credentials.

    This replaces the current session with a new one using the provided credentials.
    """
    global _client, _service, _current_email

    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    # Create a fresh client with the new credentials
    settings = get_settings()
    new_settings = Settings(
        email=request.email,
        password=request.password,
        season_id=settings.season_id,
        base_url=settings.base_url,
    )

    new_client = DreamTeamClient(new_settings)
    try:
        await new_client.login()
    except AuthenticationError as exc:
        await new_client.close()
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    # Close the old client and replace with the new one
    if _client is not None:
        await _client.close()

    _client = new_client
    _service = BonusService(_client)
    _current_email = request.email

    logger.info("Re-authenticated with Sport5 API as %s.", request.email)
    return AuthStatus(authenticated=True, email=_current_email)


@app.post("/auth/logout", response_model=AuthStatus)
async def logout() -> AuthStatus:
    """Log out and re-authenticate with the default .env credentials."""
    global _client, _service, _current_email

    # Close current client
    if _client is not None:
        await _client.close()

    # Re-create with default settings
    settings = get_settings()
    _client = DreamTeamClient(settings)
    _current_email = ""

    if settings.email and settings.password:
        try:
            await _client.login()
            _current_email = settings.email
            logger.info("Reverted to default credentials: %s.", settings.email)
        except Exception as exc:
            logger.warning("Default re-authentication failed: %s.", exc)

    _service = BonusService(_client)

    return AuthStatus(authenticated=bool(_current_email), email=_current_email)


# -- Data endpoints --

def _get_service() -> BonusService:
    """Get the BonusService instance, raising if not initialized."""
    if _service is None:
        raise HTTPException(status_code=503, detail="Service not initialized.")
    return _service


class GameModeInfo(BaseModel):
    """Information about a game mode."""

    season_id: int
    name: str


@app.get("/game-modes", response_model=list[GameModeInfo])
async def get_game_modes() -> list[GameModeInfo]:
    """List all available game modes."""
    return [
        GameModeInfo(season_id=mode.value, name=name)
        for mode, name in GAME_MODE_NAMES.items()
    ]


@app.get("/team/{user_id}/bonuses", response_model=TeamBonusStatus)
async def get_team_bonuses(
    user_id: int,
    season_id: int = Query(default=DEFAULT_GAME_MODE.value, description="Season ID (6=Dream League, 8=Champions League)"),
) -> TeamBonusStatus:
    """Get bonus usage status for a specific team.

    Args:
        user_id: The Sport5 user ID.
        season_id: Season ID - 6 for Dream League, 8 for Champions League Fantasy.

    Returns:
        TeamBonusStatus with used and remaining bonuses.
    """
    service = _get_service()
    try:
        return await service.get_team_bonuses(user_id, season_id=season_id)
    except BonusServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/league/main/bonuses", response_model=LeagueBonusReport)
async def get_main_league_bonuses(
    season_id: int = Query(default=DEFAULT_GAME_MODE.value, description="Season ID (6=Dream League, 8=Champions League)"),
) -> LeagueBonusReport:
    """Get bonus usage status for all teams in the main global league table."""
    service = _get_service()
    try:
        return await service.get_league_bonuses(league_id=None, season_id=season_id)
    except BonusServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/league/{league_id}/bonuses", response_model=LeagueBonusReport)
async def get_league_bonuses(
    league_id: int,
    season_id: int = Query(default=DEFAULT_GAME_MODE.value, description="Season ID (6=Dream League, 8=Champions League)"),
) -> LeagueBonusReport:
    """Get bonus usage status for all teams in a custom league.

    Args:
        league_id: The custom league ID.
        season_id: Season ID - 6 for Dream League, 8 for Champions League Fantasy.

    Returns:
        LeagueBonusReport with bonus status for every team in the league.
    """
    service = _get_service()
    try:
        return await service.get_league_bonuses(league_id, season_id=season_id)
    except BonusServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
