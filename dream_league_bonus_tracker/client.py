"""HTTP client for communicating with the Sport5 Dream Team API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from dream_league_bonus_tracker.config import Settings
from dream_league_bonus_tracker.models import (
    GetLeagueDataResponse,
    GetUserAndTeamResponse,
)

logger = logging.getLogger(__name__)


class DreamTeamClientError(Exception):
    """Raised when the Dream Team API client encounters an error."""


class AuthenticationError(DreamTeamClientError):
    """Raised when authentication with the Sport5 API fails."""


class DreamTeamClient:
    """Async HTTP client for the Sport5 Dream Team API.

    Handles authentication and provides methods to fetch team and league data.
    Uses httpx.AsyncClient with cookie persistence for session management.
    """

    # Auth endpoint for Sport5 Dream Team (ASP.NET Core cookie auth)
    AUTH_ENDPOINT = "/api/Account/Login"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.base_url
        self._season_id = settings.season_id
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            follow_redirects=True,
        )
        self._authenticated = False

    async def login(self) -> None:
        """Authenticate with the Sport5 Dream Team API.

        Tries known auth endpoints in sequence until one succeeds.
        The session cookies are stored in the httpx client for subsequent requests.

        Raises:
            AuthenticationError: If all authentication attempts fail.
        """
        if not self._settings.email or not self._settings.password:
            raise AuthenticationError(
                "Email and password must be provided. "
                "Set DREAMTEAM_EMAIL and DREAMTEAM_PASSWORD environment variables or pass via CLI."
            )

        payload = {
            "email": self._settings.email,
            "password": self._settings.password,
        }

        try:
            logger.info("Attempting authentication via %s", self.AUTH_ENDPOINT)
            response = await self._client.post(self.AUTH_ENDPOINT, json=payload)

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Auth endpoint returned HTTP {response.status_code}"
                )

            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                raise AuthenticationError(
                    f"Auth endpoint returned non-JSON response (content-type: {content_type})"
                )

            data = response.json()

            # Sport5 API returns {"result": true/false, ...}
            if data.get("result") is True:
                self._authenticated = True
                logger.info("Authentication successful. Session cookie stored.")
                return
            else:
                error_msg = data.get("error", "Unknown error")
                raise AuthenticationError(f"Login failed: {error_msg}")

        except httpx.HTTPError as exc:
            raise AuthenticationError(f"HTTP error during authentication: {exc}") from exc

    async def get_user_team(self, user_id: int) -> GetUserAndTeamResponse:
        """Fetch team data for a specific user.

        Args:
            user_id: The Sport5 user ID to fetch team data for.

        Returns:
            Parsed GetUserAndTeamResponse containing user and team data.

        Raises:
            DreamTeamClientError: If the API request fails.
        """
        params = {
            "seasonId": self._season_id,
            "userId": user_id,
        }
        data = await self._get("/api/UserTeam/GetUserAndTeam", params=params)
        return GetUserAndTeamResponse.model_validate(data)

    async def get_league_data(
        self,
        league_id: int | None = None,
        page_index: int = 0,
        search_text: str = "",
    ) -> GetLeagueDataResponse:
        """Fetch league data including all teams.

        Args:
            league_id: The custom league ID. Pass None for the main global league table.
            page_index: Page index for pagination (default 0).
            search_text: Optional search text to filter teams.

        Returns:
            Parsed GetLeagueDataResponse containing league and team data.

        Raises:
            DreamTeamClientError: If the API request fails.
        """
        params: dict[str, Any] = {
            "seasonId": self._season_id,
            "leagueId": league_id if league_id is not None else "null",
            "teamId": "null",
            "isPerRound": "false",
            "pageIndex": page_index,
            "searchText": search_text,
        }
        data = await self._get("/api/CustomLeagues/GetLeagueData", params=params)
        return GetLeagueDataResponse.model_validate(data)

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform a GET request to the Sport5 API.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as a dictionary.

        Raises:
            DreamTeamClientError: If the request fails or returns non-200 status.
        """
        try:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise DreamTeamClientError(
                f"API request to {endpoint} failed with status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise DreamTeamClientError(f"HTTP error during request to {endpoint}: {exc}") from exc

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "DreamTeamClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
