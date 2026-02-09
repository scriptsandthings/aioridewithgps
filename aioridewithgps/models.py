"""Data models for the Ride with GPS API.

These dataclasses represent the JSON responses from the RWGPS API.
All measurement units match what the API returns:
  - Distance: meters
  - Elevation: meters
  - Speed: km/h
  - Duration/time: seconds
  - Heart rate: bpm
  - Cadence: rpm
  - Power: watts
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class User:
    """A Ride with GPS user account.

    Returned by GET /api/v1/users/current.json and
    nested in the auth token response.
    """

    id: int
    email: str
    first_name: str
    last_name: str
    display_name: str
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime


@dataclass
class TripSummary:
    """Summary of a recorded trip (ride).

    Trips are GPS-recorded activities that a user has completed.
    This contains the summary/stats without the full track point data.
    Returned by GET /api/v1/trips.json (list) and GET /api/v1/trips/{id}.json.
    """

    # Required fields - always present in API response
    id: int
    user_id: int
    name: str
    distance: float  # Total distance in meters
    duration: float  # Total elapsed time in seconds (includes stops)
    moving_time: float  # Time spent moving in seconds (excludes stops)
    elevation_gain: float  # Total climbing in meters
    elevation_loss: float  # Total descending in meters
    created_at: str  # When the trip record was created (ISO 8601)
    updated_at: str  # When the trip record was last modified (ISO 8601)
    visibility: str  # "public", "friends_only", or "private"

    # Optional fields - may be null depending on ride data/device
    stationary: bool = False  # True if this is a stationary/indoor activity
    description: str | None = None  # User-entered description
    departed_at: str | None = None  # When the ride actually started (ISO 8601)
    time_zone: str | None = None  # e.g., "America/Los_Angeles"
    locality: str | None = None  # City name
    administrative_area: str | None = None  # State/province abbreviation
    country_code: str | None = None  # e.g., "US"
    activity_type: str | None = None  # e.g., "Cycling", "Running"

    # Speed metrics (null if not recorded or calculable)
    avg_speed: float | None = None  # Average speed in km/h
    max_speed: float | None = None  # Maximum speed in km/h

    # Heart rate metrics (null if no HR monitor was used)
    avg_hr: float | None = None  # Average heart rate in bpm
    min_hr: float | None = None  # Minimum heart rate in bpm
    max_hr: float | None = None  # Maximum heart rate in bpm

    # Cadence metrics (null if no cadence sensor was used)
    avg_cad: float | None = None  # Average cadence in rpm
    min_cad: float | None = None  # Minimum cadence in rpm
    max_cad: float | None = None  # Maximum cadence in rpm

    # Power metrics (null if no power meter was used)
    avg_watts: float | None = None  # Average power in watts
    min_watts: float | None = None  # Minimum power in watts
    max_watts: float | None = None  # Maximum power in watts

    # Calorie estimate (null if not available)
    calories: float | None = None  # Estimated calories burned in kcal

    # GPS coordinates for start and end points
    first_lat: float | None = None  # Starting latitude
    first_lng: float | None = None  # Starting longitude
    last_lat: float | None = None  # Ending latitude
    last_lng: float | None = None  # Ending longitude

    # Bounding box for the ride (useful for map display)
    sw_lat: float | None = None  # Southwest corner latitude
    sw_lng: float | None = None  # Southwest corner longitude
    ne_lat: float | None = None  # Northeast corner latitude
    ne_lng: float | None = None  # Northeast corner longitude

    # Categorization
    track_type: str | None = None  # Type of track
    terrain: str | None = None  # Terrain description
    difficulty: str | None = None  # Difficulty rating
    device: str | None = None  # Recording device name

    # URLs
    url: str | None = None  # API URL for this trip
    web_url: str | None = None  # Browser-viewable URL on ridewithgps.com


@dataclass
class RouteSummary:
    """Summary of a planned route.

    Routes are user-created paths planned on the RWGPS route planner.
    Unlike trips, routes don't have time/speed data since they haven't
    been ridden yet.
    """

    # Required fields
    id: int
    user_id: int
    name: str
    distance: float  # Total route distance in meters
    elevation_gain: float  # Total climbing in meters
    elevation_loss: float  # Total descending in meters
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime
    visibility: str  # "public", "friends_only", or "private"

    # Optional metadata
    description: str | None = None
    locality: str | None = None  # City name
    administrative_area: str | None = None  # State/province
    country_code: str | None = None

    # Start and end coordinates
    first_lat: float | None = None
    first_lng: float | None = None
    last_lat: float | None = None
    last_lng: float | None = None

    # Bounding box
    sw_lat: float | None = None
    sw_lng: float | None = None
    ne_lat: float | None = None
    ne_lng: float | None = None

    # Route characteristics
    track_type: str | None = None
    terrain: str | None = None
    difficulty: str | None = None
    unpaved_pct: float | None = None  # Percentage of route that is unpaved
    surface: str | None = None  # Surface type description
    archived: bool | None = None  # Whether the route has been archived

    # URLs
    url: str | None = None  # API URL
    html_url: str | None = None  # Browser-viewable URL


@dataclass
class SyncItem:
    """A single change from the sync endpoint.

    The sync endpoint returns a list of these items describing what
    has changed since a given datetime. Used for efficient incremental
    updates instead of re-fetching everything.
    """

    item_type: str  # "route" or "trip"
    item_id: int  # ID of the changed item
    item_user_id: int  # User who owns the item
    action: str  # "created", "updated", "deleted", "added", or "removed"
    datetime: str  # When the change occurred (ISO 8601)
    item_url: str | None = None  # API URL for the changed item


@dataclass
class SyncResult:
    """Complete response from the sync endpoint (GET /api/v1/sync.json).

    Contains the list of changes and metadata needed for the next sync call.
    """

    items: list[SyncItem] = field(default_factory=list)
    rwgps_datetime: str = ""  # Server timestamp - use as 'since' for next sync
    next_sync_url: str | None = None  # Pre-built URL for the next sync call


@dataclass
class AuthToken:
    """Authentication token returned by POST /api/v1/auth_tokens.json.

    After authenticating with email/password, this token is used for
    all subsequent API requests via the x-rwgps-auth-token header.
    """

    auth_token: str  # The token string to use in API requests
    api_key: str  # The API key associated with this token
    user: User  # The authenticated user's profile
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class PaginationMeta:
    """Pagination metadata included in list responses.

    RWGPS API supports page sizes between 20 and 200.
    """

    record_count: int  # Total number of records across all pages
    page_count: int  # Total number of pages
    page_size: int  # Number of records per page
    next_page_url: str | None = None  # URL for next page, null if last page


@dataclass
class PaginatedResult[T]:
    """A paginated API response wrapping a list of items.

    Generic over T so it can hold TripSummary, RouteSummary, etc.
    """

    items: list[T]  # The items on this page
    pagination: PaginationMeta  # Pagination metadata
