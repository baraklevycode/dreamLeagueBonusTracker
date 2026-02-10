"""Tests for DreamTeamClient in Dream League Bonus Tracker."""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from dream_league_bonus_tracker.client import (
    AuthenticationError,
    DreamTeamClient,
    DreamTeamClientError,
)
from dream_league_bonus_tracker.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        email="test@example.com",
        password="testpassword",
        season_id=6,
        base_url="https://dreamteam.sport5.co.il",
    )


@pytest.fixture
def settings_no_credentials() -> Settings:
    """Create test settings without credentials."""
    return Settings(
        email="",
        password="",
        season_id=6,
        base_url="https://dreamteam.sport5.co.il",
    )


class TestLogin:
    """Tests for DreamTeamClient.login."""

    @pytest.mark.asyncio
    async def test_login_no_credentials_raises_error(
        self, settings_no_credentials: Settings
    ) -> None:
        """Verify login raises AuthenticationError when no credentials are provided."""
        async with DreamTeamClient(settings_no_credentials) as client:
            with pytest.raises(AuthenticationError, match="Email and password must be provided"):
                await client.login()

    @pytest.mark.asyncio
    async def test_login_success(self, settings: Settings) -> None:
        """Verify login succeeds when the auth endpoint returns success."""
        async with DreamTeamClient(settings) as client:
            mock_response = httpx.Response(
                status_code=200,
                json={"result": True, "error": None},
                request=httpx.Request("POST", "https://example.com"),
            )
            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.post = AsyncMock(return_value=mock_response)

            await client.login()

            assert client._authenticated is True
            client._client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_http_error_status(self, settings: Settings) -> None:
        """Verify login raises AuthenticationError on non-200 status."""
        async with DreamTeamClient(settings) as client:
            response_500 = httpx.Response(
                status_code=500,
                text="Server Error",
                request=httpx.Request("POST", "https://example.com"),
            )

            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.post = AsyncMock(return_value=response_500)

            with pytest.raises(AuthenticationError, match="returned HTTP 500"):
                await client.login()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, settings: Settings) -> None:
        """Verify login raises AuthenticationError on invalid credentials."""
        async with DreamTeamClient(settings) as client:
            response_fail = httpx.Response(
                status_code=200,
                json={"result": False, "error": "Invalid credentials"},
                request=httpx.Request("POST", "https://example.com"),
            )

            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.post = AsyncMock(return_value=response_fail)

            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await client.login()

    @pytest.mark.asyncio
    async def test_login_non_json_response(self, settings: Settings) -> None:
        """Verify login raises AuthenticationError on non-JSON response."""
        async with DreamTeamClient(settings) as client:
            mock_response = httpx.Response(
                status_code=200,
                html="<html>Login Page</html>",
                request=httpx.Request("POST", "https://example.com"),
            )

            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(AuthenticationError, match="non-JSON response"):
                await client.login()


class TestGetUserTeam:
    """Tests for DreamTeamClient.get_user_team."""

    @pytest.mark.asyncio
    async def test_get_user_team_success(
        self, settings: Settings, sample_user_team_response: dict
    ) -> None:
        """Verify get_user_team returns parsed response on success."""
        async with DreamTeamClient(settings) as client:
            mock_response = httpx.Response(
                status_code=200,
                json=sample_user_team_response,
                request=httpx.Request("GET", "https://example.com"),
            )

            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.get = AsyncMock(return_value=mock_response)

            result = await client.get_user_team(1001)

            assert result.result is True
            assert result.data is not None
            assert result.data.user_team.name == "Test FC"

    @pytest.mark.asyncio
    async def test_get_user_team_http_error(self, settings: Settings) -> None:
        """Verify get_user_team raises DreamTeamClientError on HTTP error."""
        async with DreamTeamClient(settings) as client:
            mock_response = httpx.Response(
                status_code=500,
                text="Internal Server Error",
                request=httpx.Request("GET", "https://example.com"),
            )

            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(DreamTeamClientError, match="failed with status 500"):
                await client.get_user_team(1001)


class TestGetLeagueData:
    """Tests for DreamTeamClient.get_league_data."""

    @pytest.mark.asyncio
    async def test_get_league_data_success(
        self, settings: Settings, sample_league_response: dict
    ) -> None:
        """Verify get_league_data returns parsed response on success."""
        async with DreamTeamClient(settings) as client:
            mock_response = httpx.Response(
                status_code=200,
                json=sample_league_response,
                request=httpx.Request("GET", "https://example.com"),
            )

            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.get = AsyncMock(return_value=mock_response)

            result = await client.get_league_data(25586)

            assert result.result is True
            assert result.data is not None
            assert result.data.league_name == "Fantasy 25/26"
            assert len(result.data.teams) == 2

    @pytest.mark.asyncio
    async def test_get_league_data_connection_error(self, settings: Settings) -> None:
        """Verify get_league_data raises DreamTeamClientError on connection error."""
        async with DreamTeamClient(settings) as client:
            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            with pytest.raises(DreamTeamClientError, match="HTTP error during request"):
                await client.get_league_data(25586)


class TestContextManager:
    """Tests for DreamTeamClient context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, settings: Settings) -> None:
        """Verify the async context manager properly opens and closes the client."""
        async with DreamTeamClient(settings) as client:
            assert client is not None
            assert client._client is not None
