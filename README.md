# aioridewithgps

Async Python client for the [Ride with GPS](https://ridewithgps.com) API v1.

Built for use with [Home Assistant](https://www.home-assistant.io/) but can be used independently in any async Python project.

## Installation

```bash
pip install aioridewithgps
```

## Quick Start

```python
import aiohttp
from aioridewithgps import RideWithGPSClient

async def main():
    async with aiohttp.ClientSession() as session:
        # Authenticate with email/password to get a token
        auth = await RideWithGPSClient.authenticate(
            session,
            api_key="your_api_key",
            email="your@email.com",
            password="your_password",
        )

        # Create a client with the token
        client = RideWithGPSClient(
            session,
            api_key="your_api_key",
            auth_token=auth.auth_token,
        )

        # Get your profile
        user = await client.get_user()
        print(f"Hello, {user.display_name}!")

        # Get all your recorded rides
        trips = await client.get_all_trips()
        for trip in trips[:5]:
            print(f"  {trip.name}: {trip.distance/1000:.1f} km")

        # Get all your planned routes
        routes = await client.get_all_routes()
        print(f"You have {len(routes)} saved routes")

        # Use the sync endpoint for efficient incremental updates
        sync = await client.get_sync(since="2024-01-01T00:00:00Z")
        print(f"{len(sync.items)} changes since Jan 1")
```

## API Coverage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `authenticate()` | `POST /auth_tokens` | Get auth token with email/password |
| `get_user()` | `GET /users/current` | Current user profile |
| `get_trips()` | `GET /trips` | Paginated trip list |
| `get_all_trips()` | `GET /trips` | All trips (auto-paginates) |
| `get_trip(id)` | `GET /trips/{id}` | Single trip details |
| `get_routes()` | `GET /routes` | Paginated route list |
| `get_all_routes()` | `GET /routes` | All routes (auto-paginates) |
| `get_sync(since)` | `GET /sync` | Changes since datetime |

## Data Models

All API responses are parsed into typed dataclasses:

- `User` - Account profile (id, email, display_name)
- `TripSummary` - Ride stats (distance, duration, speed, HR, power, elevation, etc.)
- `RouteSummary` - Planned route info (distance, elevation, terrain)
- `SyncItem` - A single change event (created/updated/deleted)
- `SyncResult` - Sync response with items and server timestamp
- `AuthToken` - Auth token with embedded user profile

## Units

All values use the units returned by the RWGPS API:

| Metric | Unit |
|--------|------|
| Distance | meters |
| Elevation | meters |
| Speed | km/h |
| Duration | seconds |
| Heart rate | bpm |
| Cadence | rpm |
| Power | watts |
| Calories | kcal |

## Authentication

Ride with GPS uses a custom header scheme:

1. **Get a token**: POST to `/auth_tokens` with your API key + email/password
2. **Use the token**: Include `x-rwgps-api-key` and `x-rwgps-auth-token` headers

The password is only used once to obtain the token. Store the token for subsequent requests.

## License

MIT
