"""Tests for BonusService in Dream League Bonus Tracker."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from dream_league_bonus_tracker.client import DreamTeamClient, DreamTeamClientError
from dream_league_bonus_tracker.models import (
    GetLeagueDataResponse,
    GetUserAndTeamResponse,
)
from dream_league_bonus_tracker.service import BonusService, BonusServiceError


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mocked DreamTeamClient."""
    return AsyncMock(spec=DreamTeamClient)


@pytest.fixture
def service(mock_client: AsyncMock) -> BonusService:
    """Create a BonusService with a mocked client."""
    return BonusService(mock_client)


class TestGetTeamBonuses:
    """Tests for BonusService.get_team_bonuses."""

    @pytest.mark.asyncio
    async def test_returns_correct_used_bonuses(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_user_team_response: dict,
    ) -> None:
        """Verify that used bonuses are correctly identified and named."""
        mock_client.get_user_team.return_value = GetUserAndTeamResponse.model_validate(
            sample_user_team_response
        )

        result = await service.get_team_bonuses(1001)

        assert result.user_id == 1001
        assert result.team_name == "Test FC"
        assert result.creator_name == "Test Creator"
        assert result.total_points == 1074
        assert result.used_count == 2
        assert result.remaining_count == 2

        # Check used bonuses
        used_ids = {b.bonus_id for b in result.used_bonuses}
        assert used_ids == {2, 3}
        used_names = {b.bonus_name for b in result.used_bonuses}
        assert used_names == {"15 Subs", "Double Captains"}

    @pytest.mark.asyncio
    async def test_returns_correct_remaining_bonuses(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_user_team_response: dict,
    ) -> None:
        """Verify that remaining (unused) bonuses are correctly identified."""
        mock_client.get_user_team.return_value = GetUserAndTeamResponse.model_validate(
            sample_user_team_response
        )

        result = await service.get_team_bonuses(1001)

        # Bonuses 2 and 3 are used, so 1 and 4 remain
        assert set(result.remaining_bonuses) == {"Triple Captain", "Full Squad Points"}

    @pytest.mark.asyncio
    async def test_no_bonuses_used(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_user_team_no_bonuses_response: dict,
    ) -> None:
        """Verify correct output when no bonuses have been used."""
        mock_client.get_user_team.return_value = GetUserAndTeamResponse.model_validate(
            sample_user_team_no_bonuses_response
        )

        result = await service.get_team_bonuses(9999)

        assert result.used_count == 0
        assert result.remaining_count == 4
        assert len(result.used_bonuses) == 0
        assert len(result.remaining_bonuses) == 4

    @pytest.mark.asyncio
    async def test_all_bonuses_used(
        self,
        service: BonusService,
        mock_client: AsyncMock,
    ) -> None:
        """Verify correct output when all bonuses have been used."""
        response_data = {
            "result": True,
            "error": None,
            "data": {
                "user": {"id": 1, "email": None, "fullName": None},
                "userTeam": {
                    "id": 100,
                    "userId": 1,
                    "name": "All Bonus Team",
                    "creatorName": "Test",
                    "points": 999,
                    "bonusesData": [
                        {"bonusId": 1, "usageRoundId": 110, "usageDate": "2025-11-01T10:00:00+02:00"},
                        {"bonusId": 2, "usageRoundId": 115, "usageDate": "2025-11-15T10:00:00+02:00"},
                        {"bonusId": 3, "usageRoundId": 120, "usageDate": "2025-12-01T10:00:00+02:00"},
                        {"bonusId": 4, "usageRoundId": 125, "usageDate": "2025-12-15T10:00:00+02:00"},
                    ],
                },
            },
        }
        mock_client.get_user_team.return_value = GetUserAndTeamResponse.model_validate(response_data)

        result = await service.get_team_bonuses(1)

        assert result.used_count == 4
        assert result.remaining_count == 0
        assert len(result.remaining_bonuses) == 0

    @pytest.mark.asyncio
    async def test_api_error_raises_service_error(
        self,
        service: BonusService,
        mock_client: AsyncMock,
    ) -> None:
        """Verify that client errors are wrapped in BonusServiceError."""
        mock_client.get_user_team.side_effect = DreamTeamClientError("Connection timeout")

        with pytest.raises(BonusServiceError, match="Failed to fetch team data"):
            await service.get_team_bonuses(1001)

    @pytest.mark.asyncio
    async def test_api_returns_error_result(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_error_response: dict,
    ) -> None:
        """Verify that an error API response raises BonusServiceError."""
        mock_client.get_user_team.return_value = GetUserAndTeamResponse.model_validate(
            sample_error_response
        )

        with pytest.raises(BonusServiceError, match="User not found"):
            await service.get_team_bonuses(99999)


class TestGetLeagueBonuses:
    """Tests for BonusService.get_league_bonuses."""

    @pytest.mark.asyncio
    async def test_returns_report_for_all_teams(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_league_response: dict,
        sample_user_team_response: dict,
        sample_user_team_no_bonuses_response: dict,
    ) -> None:
        """Verify league bonus report includes data for all teams."""
        mock_client.get_league_data.return_value = GetLeagueDataResponse.model_validate(
            sample_league_response
        )

        # User 2001 has no bonuses, user 1001 has 2 bonuses
        no_bonus_response = dict(sample_user_team_no_bonuses_response)
        no_bonus_response["data"]["user"]["id"] = 2001
        no_bonus_response["data"]["userTeam"]["userId"] = 2001
        no_bonus_response["data"]["userTeam"]["name"] = "Alpha FC"
        no_bonus_response["data"]["userTeam"]["creatorName"] = "Test User A"

        mock_client.get_user_team.side_effect = [
            GetUserAndTeamResponse.model_validate(no_bonus_response),
            GetUserAndTeamResponse.model_validate(sample_user_team_response),
        ]

        report = await service.get_league_bonuses(25586)

        assert report.league_id == 25586
        assert report.league_name == "Fantasy 25/26"
        assert len(report.teams) == 2

    @pytest.mark.asyncio
    async def test_league_api_error_raises_service_error(
        self,
        service: BonusService,
        mock_client: AsyncMock,
    ) -> None:
        """Verify that league fetch errors are wrapped in BonusServiceError."""
        mock_client.get_league_data.side_effect = DreamTeamClientError("Timeout")

        with pytest.raises(BonusServiceError, match="Failed to fetch league data"):
            await service.get_league_bonuses(25586)

    @pytest.mark.asyncio
    async def test_individual_team_failure_does_not_break_report(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_league_response: dict,
        sample_user_team_response: dict,
    ) -> None:
        """Verify that a single team fetch failure doesn't break the entire report."""
        mock_client.get_league_data.return_value = GetLeagueDataResponse.model_validate(
            sample_league_response
        )

        # First team fails, second succeeds
        mock_client.get_user_team.side_effect = [
            DreamTeamClientError("Team not found"),
            GetUserAndTeamResponse.model_validate(sample_user_team_response),
        ]

        report = await service.get_league_bonuses(25586)

        # Only the successful team should be in the report
        assert len(report.teams) == 1
        assert report.teams[0].user_id == 1001

    @pytest.mark.asyncio
    async def test_league_error_result(
        self,
        service: BonusService,
        mock_client: AsyncMock,
        sample_error_response: dict,
    ) -> None:
        """Verify that an error league response raises BonusServiceError."""
        mock_client.get_league_data.return_value = GetLeagueDataResponse.model_validate(
            sample_error_response
        )

        with pytest.raises(BonusServiceError, match="API returned error for league"):
            await service.get_league_bonuses(99999)
