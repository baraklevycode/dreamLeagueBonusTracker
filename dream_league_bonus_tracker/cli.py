"""Click CLI for Dream League Bonus Tracker."""

from __future__ import annotations

import asyncio
import json
import logging
import sys

import click

from dream_league_bonus_tracker.client import DreamTeamClient
from dream_league_bonus_tracker.config import Settings
from dream_league_bonus_tracker.service import BonusService, BonusServiceError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine in a new event loop."""
    if sys.version_info >= (3, 11):
        return asyncio.run(coro)
    else:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@click.group()
def cli() -> None:
    """Dream League Bonus Tracker - Track bonus usage in Sport5 fantasy football."""


@cli.command("team-bonuses")
@click.option("--user-id", required=True, type=int, help="Sport5 user ID of the team owner.")
@click.option("--email", default=None, help="Sport5 account email (overrides .env).")
@click.option("--password", default=None, help="Sport5 account password (overrides .env).")
@click.option("--season-id", default=6, type=int, help="Season ID: 6=Dream League, 8=Champions League (default: 6).")
def team_bonuses(user_id: int, email: str | None, password: str | None, season_id: int) -> None:
    """Get bonus usage status for a specific team."""
    _run_async(_team_bonuses_async(user_id, email, password, season_id))


async def _team_bonuses_async(
    user_id: int,
    email: str | None,
    password: str | None,
    season_id: int,
) -> None:
    """Async implementation of team-bonuses command."""
    settings = _build_settings(email, password, season_id)

    async with DreamTeamClient(settings) as client:
        await _try_login(client, settings)
        service = BonusService(client)

        try:
            status = await service.get_team_bonuses(user_id)
        except BonusServiceError as exc:
            click.echo(f"Error: {exc}", err=True)
            raise SystemExit(1) from exc

        click.echo(json.dumps(status.model_dump(mode="json"), indent=2, ensure_ascii=False))


@cli.command("league-bonuses")
@click.option("--league-id", default=None, type=int, help="Custom league ID. Omit for main league table.")
@click.option("--email", default=None, help="Sport5 account email (overrides .env).")
@click.option("--password", default=None, help="Sport5 account password (overrides .env).")
@click.option("--season-id", default=6, type=int, help="Season ID: 6=Dream League, 8=Champions League (default: 6).")
def league_bonuses(league_id: int | None, email: str | None, password: str | None, season_id: int) -> None:
    """Get bonus usage status for all teams in a league. Omit --league-id for main league."""
    _run_async(_league_bonuses_async(league_id, email, password, season_id))


async def _league_bonuses_async(
    league_id: int | None,
    email: str | None,
    password: str | None,
    season_id: int,
) -> None:
    """Async implementation of league-bonuses command."""
    settings = _build_settings(email, password, season_id)

    async with DreamTeamClient(settings) as client:
        await _try_login(client, settings)
        service = BonusService(client)

        try:
            report = await service.get_league_bonuses(league_id, season_id=season_id)
        except BonusServiceError as exc:
            click.echo(f"Error: {exc}", err=True)
            raise SystemExit(1) from exc

        click.echo(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))


@cli.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind to.")
@click.option("--port", default=8000, type=int, help="Port to bind to.")
def serve(host: str, port: int) -> None:
    """Start the FastAPI server."""
    import uvicorn

    click.echo(f"Starting server on {host}:{port}...")
    uvicorn.run("dream_league_bonus_tracker.api:app", host=host, port=port, reload=True)


def _build_settings(email: str | None, password: str | None, season_id: int) -> Settings:
    """Build Settings, optionally overriding email/password from CLI args.

    Args:
        email: Optional email override.
        password: Optional password override.
        season_id: Season ID.

    Returns:
        Settings instance with applied overrides.
    """
    settings = Settings()
    if email:
        settings.email = email
    if password:
        settings.password = password
    settings.season_id = season_id
    return settings


async def _try_login(client: DreamTeamClient, settings: Settings) -> None:
    """Attempt to login if credentials are available.

    Args:
        client: The DreamTeamClient instance.
        settings: Settings with potential credentials.
    """
    if settings.email and settings.password:
        try:
            await client.login()
            click.echo("Successfully authenticated.")
        except Exception as exc:
            click.echo(f"Warning: Authentication failed: {exc}. Continuing without auth.", err=True)
    else:
        click.echo("No credentials provided. Proceeding without authentication.")


if __name__ == "__main__":
    cli()
