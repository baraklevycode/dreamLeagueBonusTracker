"""Business logic for Dream League Bonus Tracker.

Provides BonusService which orchestrates data fetching from the DreamTeamClient
and transforms raw API responses into clean bonus status reports.
"""

from __future__ import annotations

import asyncio
import logging

from dream_league_bonus_tracker.client import DreamTeamClient, DreamTeamClientError
from dream_league_bonus_tracker.models import (
    ALL_BONUS_IDS,
    BONUS_NAMES,
    DEFAULT_GAME_MODE,
    GAME_MODE_NAMES,
    BonusUsage,
    LeagueBonusReport,
    TeamBonusStatus,
)

logger = logging.getLogger(__name__)


class BonusServiceError(Exception):
    """Raised when the bonus service encounters an error."""


class BonusService:
    """Service layer for fetching and processing bonus usage data.

    Coordinates between the DreamTeamClient and the output models to produce
    clean bonus status reports for individual teams and entire leagues.
    """

    def __init__(self, client: DreamTeamClient) -> None:
        self._client = client

    async def get_team_bonuses(self, user_id: int, season_id: int | None = None) -> TeamBonusStatus:
        """Get bonus usage status for a specific team.

        Args:
            user_id: The Sport5 user ID.
            season_id: Override the season ID. If None, uses the client default.

        Returns:
            TeamBonusStatus with used and remaining bonuses.

        Raises:
            BonusServiceError: If fetching or parsing team data fails.
        """
        try:
            response = await self._client.get_user_team(user_id, season_id=season_id)
        except DreamTeamClientError as exc:
            raise BonusServiceError(f"Failed to fetch team data for user {user_id}: {exc}") from exc

        if not response.result or response.data is None:
            raise BonusServiceError(
                f"API returned error for user {user_id}: {response.error or 'No data returned'}"
            )

        team = response.data.user_team
        return self._build_team_bonus_status(
            user_id=user_id,
            team_name=team.name,
            creator_name=team.creator_name,
            total_points=team.points,
            bonuses_data=team.bonuses_data,
        )

    async def get_league_bonuses(
        self, league_id: int | None = None, season_id: int = DEFAULT_GAME_MODE.value
    ) -> LeagueBonusReport:
        """Get bonus usage status for all teams in a league.

        Fetches the league data first, then fetches team bonus data for each team
        concurrently to build a complete report.

        Args:
            league_id: The custom league ID. Pass None for the main global league table.
            season_id: The season ID (default: Dream League = 6, Champions League = 8).

        Returns:
            LeagueBonusReport with bonus status for all teams in the league.

        Raises:
            BonusServiceError: If fetching or parsing league data fails.
        """
        league_label = f"league {league_id}" if league_id is not None else "main league"
        game_mode_name = GAME_MODE_NAMES.get(season_id, f"Season {season_id}")
        try:
            league_response = await self._client.get_league_data(
                league_id, season_id=season_id
            )
        except DreamTeamClientError as exc:
            raise BonusServiceError(f"Failed to fetch league data for {league_label}: {exc}") from exc

        if not league_response.result or league_response.data is None:
            raise BonusServiceError(
                f"API returned error for {league_label}: {league_response.error or 'No data returned'}"
            )

        league_data = league_response.data

        # Limit to first 100 teams for large leagues (e.g. main league has 1000+ per page)
        MAX_TEAMS = 100
        teams_to_fetch = league_data.teams[:MAX_TEAMS]

        # Fetch bonus data for each team concurrently
        tasks = [
            self._get_team_bonuses_safe(team.user_id, season_id=season_id)
            for team in teams_to_fetch
        ]
        team_statuses = await asyncio.gather(*tasks)

        # Filter out None results (teams that failed to fetch)
        valid_statuses = [status for status in team_statuses if status is not None]

        return LeagueBonusReport(
            league_id=league_id,
            league_name=league_data.league_name or "Main League Table",
            season_id=season_id,
            game_mode=game_mode_name,
            teams=valid_statuses,
        )

    async def _get_team_bonuses_safe(
        self, user_id: int, season_id: int | None = None
    ) -> TeamBonusStatus | None:
        """Fetch team bonuses with error handling - returns None on failure.

        This allows concurrent league fetching to continue even if individual
        team requests fail.

        Args:
            user_id: The Sport5 user ID.
            season_id: Override the season ID. If None, uses the client default.

        Returns:
            TeamBonusStatus or None if fetching failed.
        """
        try:
            return await self.get_team_bonuses(user_id, season_id=season_id)
        except BonusServiceError as exc:
            logger.warning("Failed to fetch bonuses for user %d: %s", user_id, exc)
            return None

    @staticmethod
    def _build_team_bonus_status(
        user_id: int,
        team_name: str,
        creator_name: str,
        total_points: int,
        bonuses_data: list,
    ) -> TeamBonusStatus:
        """Build a TeamBonusStatus from raw bonus data.

        Args:
            user_id: The Sport5 user ID.
            team_name: Name of the team.
            creator_name: Name of the team creator/owner.
            total_points: Total points accumulated.
            bonuses_data: List of BonusData objects from the API.

        Returns:
            Fully populated TeamBonusStatus.
        """
        used_bonuses = [
            BonusUsage(
                bonus_id=bonus.bonus_id,
                bonus_name=BONUS_NAMES.get(bonus.bonus_id, f"Unknown Bonus ({bonus.bonus_id})"),
                usage_round_id=bonus.usage_round_id,
                usage_date=bonus.usage_date,
            )
            for bonus in bonuses_data
        ]

        used_bonus_ids = {bonus.bonus_id for bonus in bonuses_data}
        remaining_bonus_ids = ALL_BONUS_IDS - used_bonus_ids
        remaining_bonuses = [
            BONUS_NAMES.get(bonus_id, f"Unknown Bonus ({bonus_id})")
            for bonus_id in sorted(remaining_bonus_ids)
        ]

        return TeamBonusStatus(
            user_id=user_id,
            team_name=team_name,
            creator_name=creator_name,
            total_points=total_points,
            used_bonuses=used_bonuses,
            remaining_bonuses=remaining_bonuses,
            used_count=len(used_bonuses),
            remaining_count=len(remaining_bonuses),
        )
