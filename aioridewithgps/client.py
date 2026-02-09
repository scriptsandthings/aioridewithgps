"""Async client for the Ride with GPS API.

This module provides the main client class for interacting with the
Ride with GPS REST API (v1). It handles authentication, pagination,
and parsing API responses into typed dataclass models.

Usage:
    async with aiohttp.ClientSession() as session:
        # First authenticate to get a token
        auth = await RideWithGPSClient.authenticate(
            session, api_key="...", email="...", password="..."
        )

        # Then create a client with the token
        client = RideWithGPSClient(session, api_key="...", auth_token=auth.auth_token)
        user = await client.get_user()
        trips = await client.get_all_trips()
"""

from __future__ import annotations

from typing import Any

import aiohttp

from .exceptions import ApiError, AuthenticationError, ForbiddenError, NotFoundError
from .models import (
    AuthToken,
    PaginatedResult,
    PaginationMeta,
    RouteSummary,
    SyncItem,
    SyncResult,
    TripSummary,
    User,
)

# Base URL for all RWGPS API v1 endpoints
API_BASE_URL = "https://ridewithgps.com/api/v1"


class RideWithGPSClient:
    """Async client for the Ride with GPS API v1.

    This client uses aiohttp for async HTTP requests and authenticates
    using the RWGPS custom header scheme (x-rwgps-api-key + x-rwgps-auth-token).

    The client does NOT manage its own aiohttp session - you must provide one.
    This allows the caller (e.g., Home Assistant) to manage session lifecycle.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        auth_token: str,
    ) -> None:
        """Initialize the client.

        Args:
            session: An aiohttp session to use for HTTP requests.
            api_key: Your RWGPS API key (identifies the application).
            auth_token: The user's auth token (obtained via authenticate()).
        """
        self._session = session
        self._api_key = api_key
        self._auth_token = auth_token

    @property
    def _headers(self) -> dict[str, str]:
        """Build the authentication headers for API requests.

        RWGPS uses a custom header scheme instead of standard Authorization:
        - x-rwgps-api-key: identifies the API client/application
        - x-rwgps-auth-token: identifies the authenticated user
        """
        return {
            "x-rwgps-api-key": self._api_key,
            "x-rwgps-auth-token": self._auth_token,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated API request and handle errors.

        All API methods go through this to get consistent error handling.
        Maps HTTP status codes to specific exception types.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API path (e.g., "/trips.json") - appended to API_BASE_URL.
            params: Optional query string parameters.
            json_data: Optional JSON request body.
            headers: Optional headers override (defaults to auth headers).

        Returns:
            Parsed JSON response as a dict.

        Raises:
            AuthenticationError: If the API returns 401.
            ForbiddenError: If the API returns 403.
            NotFoundError: If the API returns 404.
            ApiError: For any other HTTP error (4xx/5xx).
        """
        url = f"{API_BASE_URL}{path}"
        request_headers = headers or self._headers

        async with self._session.request(
            method, url, headers=request_headers, params=params, json=json_data
        ) as resp:
            if resp.status == 401:
                raise AuthenticationError("Authentication failed")
            if resp.status == 403:
                raise ForbiddenError("Access forbidden")
            if resp.status == 404:
                raise NotFoundError(f"Resource not found: {path}")
            if resp.status >= 400:
                body = await resp.text()
                raise ApiError(resp.status, body)
            # 204 No Content (e.g., after DELETE) - return empty dict
            if resp.status == 204:
                return {}
            return await resp.json()

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    @staticmethod
    async def authenticate(
        session: aiohttp.ClientSession,
        api_key: str,
        email: str,
        password: str,
    ) -> AuthToken:
        """Authenticate with email and password to obtain an auth token.

        This is a static method because you don't have a token yet -
        you're trying to get one. After calling this, create a
        RideWithGPSClient instance with the returned auth_token.

        The password is sent to RWGPS and is NOT stored anywhere.
        Only the returned auth token should be persisted.

        Args:
            session: An aiohttp session.
            api_key: Your RWGPS API key.
            email: User's RWGPS account email.
            password: User's RWGPS account password.

        Returns:
            An AuthToken containing the token string and user profile.

        Raises:
            AuthenticationError: If credentials are invalid.
            ApiError: For unexpected API errors.
        """
        url = f"{API_BASE_URL}/auth_tokens.json"
        headers = {
            "x-rwgps-api-key": api_key,
            "Content-Type": "application/json",
        }
        async with session.post(
            url,
            headers=headers,
            json={"user": {"email": email, "password": password}},
        ) as resp:
            if resp.status == 401:
                raise AuthenticationError("Invalid email or password")
            if resp.status == 400:
                raise AuthenticationError("Bad request - check credentials")
            if resp.status >= 400:
                body = await resp.text()
                raise ApiError(resp.status, body)

            data = await resp.json()

        # Response format: {"auth_token": {"auth_token": "...", "user": {...}}}
        # Note: the outer and inner keys are both named "auth_token"
        auth_data = data["auth_token"]
        user_data = auth_data["user"]

        return AuthToken(
            auth_token=auth_data["auth_token"],
            api_key=auth_data["api_key"],
            user=User(
                id=user_data["id"],
                email=user_data.get("email", ""),
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                display_name=user_data.get("display_name", ""),
                created_at=user_data.get("created_at", ""),
                updated_at=user_data.get("updated_at", ""),
            ),
            created_at=auth_data.get("created_at"),
            updated_at=auth_data.get("updated_at"),
        )

    # -------------------------------------------------------------------------
    # User
    # -------------------------------------------------------------------------

    async def get_user(self) -> User:
        """Get the current authenticated user's profile.

        Returns:
            A User object with the account details.
        """
        data = await self._request("GET", "/users/current.json")
        u = data["user"]
        return User(
            id=u["id"],
            email=u.get("email", ""),
            first_name=u.get("first_name", ""),
            last_name=u.get("last_name", ""),
            display_name=u.get("display_name", ""),
            created_at=u.get("created_at", ""),
            updated_at=u.get("updated_at", ""),
        )

    # -------------------------------------------------------------------------
    # Trips (recorded rides)
    # -------------------------------------------------------------------------

    def _parse_trip_summary(self, t: dict[str, Any]) -> TripSummary:
        """Parse a trip summary dict from the API into a TripSummary dataclass.

        Handles missing/null fields gracefully with .get() defaults.
        """
        return TripSummary(
            id=t["id"],
            user_id=t["user_id"],
            name=t.get("name", ""),
            distance=t.get("distance", 0),
            duration=t.get("duration", 0),
            moving_time=t.get("moving_time", 0),
            elevation_gain=t.get("elevation_gain", 0),
            elevation_loss=t.get("elevation_loss", 0),
            created_at=t.get("created_at", ""),
            updated_at=t.get("updated_at", ""),
            visibility=t.get("visibility", ""),
            stationary=t.get("stationary", False),
            description=t.get("description"),
            departed_at=t.get("departed_at"),
            time_zone=t.get("time_zone"),
            locality=t.get("locality"),
            administrative_area=t.get("administrative_area"),
            country_code=t.get("country_code"),
            activity_type=t.get("activity_type"),
            avg_speed=t.get("avg_speed"),
            max_speed=t.get("max_speed"),
            avg_hr=t.get("avg_hr"),
            min_hr=t.get("min_hr"),
            max_hr=t.get("max_hr"),
            avg_cad=t.get("avg_cad"),
            min_cad=t.get("min_cad"),
            max_cad=t.get("max_cad"),
            avg_watts=t.get("avg_watts"),
            min_watts=t.get("min_watts"),
            max_watts=t.get("max_watts"),
            calories=t.get("calories"),
            first_lat=t.get("first_lat"),
            first_lng=t.get("first_lng"),
            last_lat=t.get("last_lat"),
            last_lng=t.get("last_lng"),
            sw_lat=t.get("sw_lat"),
            sw_lng=t.get("sw_lng"),
            ne_lat=t.get("ne_lat"),
            ne_lng=t.get("ne_lng"),
            track_type=t.get("track_type"),
            terrain=t.get("terrain"),
            difficulty=t.get("difficulty"),
            device=t.get("device"),
            url=t.get("url"),
            web_url=t.get("web_url"),
            html_url=t.get("html_url"),
        )

    async def get_trips(
        self, page: int = 1, page_size: int = 200
    ) -> PaginatedResult[TripSummary]:
        """Get a single page of trips.

        Args:
            page: Page number (1-indexed).
            page_size: Number of trips per page (20-200, default 200 for efficiency).

        Returns:
            A PaginatedResult containing the trips and pagination metadata.
        """
        data = await self._request(
            "GET",
            "/trips.json",
            params={"page": page, "page_size": page_size},
        )
        trips = [self._parse_trip_summary(t) for t in data.get("trips", [])]
        pagination = self._parse_pagination(data.get("meta", {}))
        return PaginatedResult(items=trips, pagination=pagination)

    async def get_all_trips(self) -> list[TripSummary]:
        """Fetch ALL trips by paginating through every page.

        Uses max page size (200) to minimize API calls.
        For a user with 1000 trips, this makes ~5 API calls.

        Returns:
            Complete list of all user's trips.
        """
        all_trips: list[TripSummary] = []
        page = 1
        while True:
            result = await self.get_trips(page=page, page_size=200)
            all_trips.extend(result.items)
            # next_page_url is null when we've reached the last page
            if result.pagination.next_page_url is None:
                break
            page += 1
        return all_trips

    async def get_trip(self, trip_id: int) -> TripSummary:
        """Get a single trip by its ID.

        Returns summary data (no track points). Used for fetching
        updated trip data after a sync notification.

        Args:
            trip_id: The RWGPS trip ID.

        Returns:
            The trip summary.

        Raises:
            NotFoundError: If the trip doesn't exist.
        """
        data = await self._request("GET", f"/trips/{trip_id}.json")
        return self._parse_trip_summary(data["trip"])

    # -------------------------------------------------------------------------
    # Routes (planned routes)
    # -------------------------------------------------------------------------

    def _parse_route_summary(self, r: dict[str, Any]) -> RouteSummary:
        """Parse a route summary dict from the API into a RouteSummary dataclass."""
        return RouteSummary(
            id=r["id"],
            user_id=r["user_id"],
            name=r.get("name", ""),
            distance=r.get("distance", 0),
            elevation_gain=r.get("elevation_gain", 0),
            elevation_loss=r.get("elevation_loss", 0),
            created_at=r.get("created_at", ""),
            updated_at=r.get("updated_at", ""),
            visibility=r.get("visibility", ""),
            description=r.get("description"),
            locality=r.get("locality"),
            administrative_area=r.get("administrative_area"),
            country_code=r.get("country_code"),
            first_lat=r.get("first_lat"),
            first_lng=r.get("first_lng"),
            last_lat=r.get("last_lat"),
            last_lng=r.get("last_lng"),
            sw_lat=r.get("sw_lat"),
            sw_lng=r.get("sw_lng"),
            ne_lat=r.get("ne_lat"),
            ne_lng=r.get("ne_lng"),
            track_type=r.get("track_type"),
            terrain=r.get("terrain"),
            difficulty=r.get("difficulty"),
            unpaved_pct=r.get("unpaved_pct"),
            surface=r.get("surface"),
            archived=r.get("archived"),
            url=r.get("url"),
            html_url=r.get("html_url"),
        )

    async def get_routes(
        self, page: int = 1, page_size: int = 200
    ) -> PaginatedResult[RouteSummary]:
        """Get a single page of routes.

        Args:
            page: Page number (1-indexed).
            page_size: Number of routes per page (20-200).

        Returns:
            A PaginatedResult containing the routes and pagination metadata.
        """
        data = await self._request(
            "GET",
            "/routes.json",
            params={"page": page, "page_size": page_size},
        )
        routes = [self._parse_route_summary(r) for r in data.get("routes", [])]
        pagination = self._parse_pagination(data.get("meta", {}))
        return PaginatedResult(items=routes, pagination=pagination)

    async def get_all_routes(self) -> list[RouteSummary]:
        """Fetch ALL routes by paginating through every page.

        Returns:
            Complete list of all user's planned routes.
        """
        all_routes: list[RouteSummary] = []
        page = 1
        while True:
            result = await self.get_routes(page=page, page_size=200)
            all_routes.extend(result.items)
            if result.pagination.next_page_url is None:
                break
            page += 1
        return all_routes

    # -------------------------------------------------------------------------
    # Sync (incremental updates)
    # -------------------------------------------------------------------------

    async def get_sync(
        self, since: str, assets: str = "routes,trips"
    ) -> SyncResult:
        """Get changes since a given datetime using the sync endpoint.

        This is the most efficient way to detect new/updated/deleted
        trips and routes without re-fetching everything. The coordinator
        calls this on each update interval (e.g., every 30 minutes).

        Args:
            since: ISO 8601 datetime string. Use "1970-01-01T00:00:00Z"
                   for initial sync, or the rwgps_datetime from the
                   previous sync response for incremental updates.
            assets: Comma-separated list of asset types to sync.
                    Options: "routes", "trips", or "routes,trips".

        Returns:
            A SyncResult with the list of changes and the server timestamp
            to use for the next sync call.
        """
        data = await self._request(
            "GET",
            "/sync.json",
            params={"since": since, "assets": assets},
        )
        items = [
            SyncItem(
                item_type=i["item_type"],
                item_id=i["item_id"],
                item_user_id=i["item_user_id"],
                action=i["action"],
                datetime=i["datetime"],
                item_url=i.get("item_url"),
            )
            for i in data.get("items", [])
        ]
        meta = data.get("meta", {})
        return SyncResult(
            items=items,
            rwgps_datetime=meta.get("rwgps_datetime", ""),
            next_sync_url=meta.get("next_sync_url"),
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _parse_pagination(meta: dict[str, Any]) -> PaginationMeta:
        """Parse pagination metadata from an API list response."""
        p = meta.get("pagination", {})
        return PaginationMeta(
            record_count=p.get("record_count", 0),
            page_count=p.get("page_count", 0),
            page_size=p.get("page_size", 0),
            next_page_url=p.get("next_page_url"),
        )
