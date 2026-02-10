"""Tests for Pydantic models in Dream League Bonus Tracker."""

from __future__ import annotations

from datetime import datetime, timezone

from dream_league_bonus_tracker.models import (
    ALL_BONUS_IDS,
    BONUS_NAMES,
    BonusData,
    BonusType,
    GetLeagueDataResponse,
    GetUserAndTeamResponse,
    TeamInLeague,
    UserInfo,
    UserTeamRaw,
)


class TestBonusType:
    """Tests for BonusType enum and bonus mapping constants."""

    def test_bonus_type_values(self) -> None:
        """Verify all bonus type enum values match expected IDs."""
        assert BonusType.TRIPLE_CAPTAIN == 1
        assert BonusType.FIFTEEN_SUBS == 2
        assert BonusType.DOUBLE_CAPTAINS == 3
        assert BonusType.FULL_SQUAD_POINTS == 4

    def test_bonus_names_has_all_types(self) -> None:
        """Verify BONUS_NAMES dictionary contains all bonus types."""
        for bonus_type in BonusType:
            assert bonus_type.value in BONUS_NAMES

    def test_bonus_names_values(self) -> None:
        """Verify bonus name strings are correct."""
        assert BONUS_NAMES[1] == "Triple Captain"
        assert BONUS_NAMES[2] == "15 Subs"
        assert BONUS_NAMES[3] == "Double Captains"
        assert BONUS_NAMES[4] == "Full Squad Points"

    def test_all_bonus_ids(self) -> None:
        """Verify ALL_BONUS_IDS contains exactly {1, 2, 3, 4}."""
        assert ALL_BONUS_IDS == {1, 2, 3, 4}


class TestBonusData:
    """Tests for BonusData model."""

    def test_parse_from_alias(self) -> None:
        """Verify BonusData parses from API field names (camelCase)."""
        data = {
            "bonusId": 2,
            "usageRoundId": 125,
            "usageDate": "2025-12-19T14:04:09.7324083+02:00",
        }
        bonus = BonusData.model_validate(data)
        assert bonus.bonus_id == 2
        assert bonus.usage_round_id == 125
        assert isinstance(bonus.usage_date, datetime)

    def test_parse_from_field_name(self) -> None:
        """Verify BonusData parses from Python field names (snake_case)."""
        bonus = BonusData(
            bonus_id=3,
            usage_round_id=131,
            usage_date=datetime(2026, 1, 30, 14, 18, 3, tzinfo=timezone.utc),
        )
        assert bonus.bonus_id == 3
        assert bonus.usage_round_id == 131


class TestUserInfo:
    """Tests for UserInfo model."""

    def test_parse_user_info(self) -> None:
        """Verify UserInfo parses from API response."""
        data = {"id": 1001, "email": None, "fullName": None, "approvedTerms": False}
        user = UserInfo.model_validate(data)
        assert user.id == 1001
        assert user.email is None
        assert user.full_name is None

    def test_parse_user_info_with_values(self) -> None:
        """Verify UserInfo parses when fields have values."""
        data = {"id": 1, "email": "test@test.com", "fullName": "Test User"}
        user = UserInfo.model_validate(data)
        assert user.id == 1
        assert user.email == "test@test.com"
        assert user.full_name == "Test User"


class TestUserTeamRaw:
    """Tests for UserTeamRaw model."""

    def test_parse_with_bonuses(self) -> None:
        """Verify UserTeamRaw parses with bonus data."""
        data = {
            "id": 7524324,
            "userId": 1001,
            "name": "Test FC",
            "creatorName": "Test Creator",
            "points": 1074,
            "bonusesData": [
                {
                    "bonusId": 2,
                    "usageRoundId": 125,
                    "usageDate": "2025-12-19T14:04:09.7324083+02:00",
                },
            ],
        }
        team = UserTeamRaw.model_validate(data)
        assert team.user_id == 1001
        assert team.name == "Test FC"
        assert team.creator_name == "Test Creator"
        assert team.points == 1074
        assert len(team.bonuses_data) == 1
        assert team.bonuses_data[0].bonus_id == 2

    def test_parse_without_bonuses(self) -> None:
        """Verify UserTeamRaw parses with empty bonuses list."""
        data = {
            "id": 1234,
            "userId": 9999,
            "name": "Test Team",
            "creatorName": "Test Creator",
            "points": 0,
            "bonusesData": [],
        }
        team = UserTeamRaw.model_validate(data)
        assert len(team.bonuses_data) == 0


class TestGetUserAndTeamResponse:
    """Tests for GetUserAndTeamResponse model."""

    def test_parse_success_response(self, sample_user_team_response: dict) -> None:
        """Verify successful response parsing."""
        response = GetUserAndTeamResponse.model_validate(sample_user_team_response)
        assert response.result is True
        assert response.error is None
        assert response.data is not None
        assert response.data.user.id == 1001
        assert response.data.user_team.name == "Test FC"
        assert len(response.data.user_team.bonuses_data) == 2

    def test_parse_error_response(self, sample_error_response: dict) -> None:
        """Verify error response parsing."""
        response = GetUserAndTeamResponse.model_validate(sample_error_response)
        assert response.result is False
        assert response.error == "User not found"
        assert response.data is None


class TestTeamInLeague:
    """Tests for TeamInLeague model."""

    def test_parse_team_in_league(self) -> None:
        """Verify TeamInLeague parses from API response."""
        data = {
            "userId": 2001,
            "name": "Alpha FC",
            "userName": "Test User A",
            "totalScore": 1026,
            "roundScore": 49,
            "position": 1063,
        }
        team = TeamInLeague.model_validate(data)
        assert team.user_id == 2001
        assert team.name == "Alpha FC"
        assert team.user_name == "Test User A"
        assert team.total_score == 1026
        assert team.round_score == 49
        assert team.position == 1063


class TestGetLeagueDataResponse:
    """Tests for GetLeagueDataResponse model."""

    def test_parse_success_response(self, sample_league_response: dict) -> None:
        """Verify successful league response parsing."""
        response = GetLeagueDataResponse.model_validate(sample_league_response)
        assert response.result is True
        assert response.data is not None
        assert response.data.league_name == "Fantasy 25/26"
        assert response.data.custom_league.id == 25586
        assert len(response.data.teams) == 2
        assert response.data.teams[0].user_id == 2001
        assert response.data.teams[1].user_id == 1001

    def test_parse_error_response(self, sample_error_response: dict) -> None:
        """Verify error response parsing."""
        response = GetLeagueDataResponse.model_validate(sample_error_response)
        assert response.result is False
        assert response.data is None
