"""Shared test fixtures for Dream League Bonus Tracker tests."""

from __future__ import annotations

import pytest

from dream_league_bonus_tracker.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create a test Settings instance."""
    return Settings(
        email="test@example.com",
        password="testpassword",
        season_id=6,
        base_url="https://dreamteam.sport5.co.il",
    )


@pytest.fixture
def sample_user_team_response() -> dict:
    """Sample response from GetUserAndTeam API endpoint."""
    return {
        "result": True,
        "error": None,
        "data": {
            "user": {
                "id": 1001,
                "email": None,
                "fullName": None,
                "approvedTerms": False,
            },
            "userTeam": {
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
                    {
                        "bonusId": 3,
                        "usageRoundId": 131,
                        "usageDate": "2026-01-30T14:18:03.8782561+02:00",
                    },
                ],
            },
        },
    }


@pytest.fixture
def sample_user_team_no_bonuses_response() -> dict:
    """Sample response for a team with no bonuses used."""
    return {
        "result": True,
        "error": None,
        "data": {
            "user": {
                "id": 9999,
                "email": None,
                "fullName": None,
                "approvedTerms": False,
            },
            "userTeam": {
                "id": 1234,
                "userId": 9999,
                "name": "No Bonus Team",
                "creatorName": "Test User",
                "points": 500,
                "bonusesData": [],
            },
        },
    }


@pytest.fixture
def sample_league_response() -> dict:
    """Sample response from GetLeagueData API endpoint."""
    return {
        "result": True,
        "error": None,
        "data": {
            "leagueName": "Fantasy 25/26",
            "customLeague": {
                "id": 25586,
                "seasonId": 6,
                "name": "Fantasy 25/26",
            },
            "teams": [
                {
                    "userId": 2001,
                    "name": "Alpha FC",
                    "userName": "Test User A",
                    "totalScore": 1026,
                    "roundScore": 49,
                    "position": 1063,
                },
                {
                    "userId": 1001,
                    "name": "Test FC",
                    "userName": "Test Creator",
                    "totalScore": 1074,
                    "roundScore": 71,
                    "position": 252,
                },
            ],
        },
    }


@pytest.fixture
def sample_error_response() -> dict:
    """Sample error response from the API."""
    return {
        "result": False,
        "error": "User not found",
        "data": None,
    }
