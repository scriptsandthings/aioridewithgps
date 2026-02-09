# aioridewithgps

Async Python client for the [Ride with GPS](https://ridewithgps.com) API v1.

Built for use with [Home Assistant](https://www.home-assistant.io/) but works great in any Python project.

## What is this?

This library lets you pull your cycling data from Ride with GPS into Python. You can access your rides, routes, stats, and more - all using modern async Python.

## Installation

```bash
pip install aioridewithgps
```

## Before you start

You'll need a **Ride with GPS API key**. Here's how to get one:

1. Log in to your Ride with GPS account at [ridewithgps.com](https://ridewithgps.com)
2. Go to your [API clients page](https://ridewithgps.com/api/api_clients)
3. Click **Create a new API client**
4. Give it a name (e.g., "My Home Assistant")
5. Copy the **API Key** that appears - you'll need it below

That's it! You now have an API key.

## Quick start

Here's a complete working example:

```python
import asyncio
import aiohttp
from aioridewithgps import RideWithGPSClient

async def main():
    async with aiohttp.ClientSession() as session:
        # Step 1: Log in with your API key + RWGPS email/password
        # This gets you a token - your password is NOT stored
        auth = await RideWithGPSClient.authenticate(
            session,
            api_key="your_api_key_here",      # From step 5 above
            email="your_rwgps@email.com",      # Your RWGPS login email
            password="your_rwgps_password",    # Your RWGPS login password
        )
        print(f"Logged in! Token: {auth.auth_token[:10]}...")

        # Step 2: Create a client using the token
        client = RideWithGPSClient(
            session,
            api_key="your_api_key_here",
            auth_token=auth.auth_token,  # Token from Step 1
        )

        # Step 3: Use it! Get your profile
        user = await client.get_user()
        print(f"Hello, {user.display_name}!")

        # Get your last 5 rides
        trips = await client.get_all_trips()
        print(f"\nYou have {len(trips)} total rides!\n")
        for trip in trips[:5]:
            km = trip.distance / 1000
            print(f"  {trip.name}: {km:.1f} km")

        # Get your planned routes
        routes = await client.get_all_routes()
        print(f"\nYou have {len(routes)} saved routes")

# Run it
asyncio.run(main())
```

Save this as `test.py`, replace the placeholder values with your real credentials, and run:

```bash
python3 test.py
```

## What can you do with it?

| What you want | Method to call | What it returns |
|---|---|---|
| Log in | `RideWithGPSClient.authenticate(...)` | Auth token + your profile |
| Get your profile | `client.get_user()` | Your name, email, account info |
| Get all your rides | `client.get_all_trips()` | Every ride you've recorded |
| Get one ride | `client.get_trip(trip_id)` | A single ride's details |
| Get a page of rides | `client.get_trips(page=1)` | One page of rides (up to 200) |
| Get all your routes | `client.get_all_routes()` | Every route you've planned |
| Get a page of routes | `client.get_routes(page=1)` | One page of routes (up to 200) |
| Check for new rides | `client.get_sync(since="2024-01-01T00:00:00Z")` | What changed since a date |

## What data do you get for each ride?

Every ride (`TripSummary`) includes these fields:

| Field | What it is | Example |
|---|---|---|
| `name` | Ride name | "Morning Ride" |
| `distance` | Distance in meters | 32186.9 (= 20 miles) |
| `duration` | Total time in seconds (including stops) | 5400 (= 1.5 hours) |
| `moving_time` | Time actually riding in seconds | 4800 (= 1h 20m) |
| `elevation_gain` | Total climbing in meters | 305 (= 1000 ft) |
| `avg_speed` | Average speed in km/h | 24.1 |
| `max_speed` | Top speed in km/h | 52.3 |
| `avg_hr` | Average heart rate (if HR monitor used) | 145 |
| `max_hr` | Max heart rate | 172 |
| `avg_watts` | Average power (if power meter used) | 180 |
| `calories` | Estimated calories burned | 850 |
| `departed_at` | When the ride started | "2024-06-15T08:00:00-07:00" |
| `activity_type` | Type of activity | "Cycling" |
| `locality` | City | "Portland" |
| `web_url` | Link to view on RWGPS | "https://ridewithgps.com/trips/123" |

Fields like heart rate, power, and cadence will be `None` if you don't have those sensors.

## How authentication works

1. You call `authenticate()` with your API key + email + password
2. Ride with GPS gives you back a **token** (a long random string)
3. You use that token for all future API calls
4. **Your password is never stored** - it's only used once to get the token

The token doesn't expire on its own, so you can save it and reuse it. If it ever stops working, just call `authenticate()` again.

## Units reference

All values match what the Ride with GPS API returns:

| What | Unit | To convert |
|---|---|---|
| Distance | meters | Divide by 1000 for km, or by 1609.34 for miles |
| Elevation | meters | Multiply by 3.281 for feet |
| Speed | km/h | Multiply by 0.621 for mph |
| Time | seconds | Divide by 60 for minutes, by 3600 for hours |
| Heart rate | bpm | - |
| Cadence | rpm | - |
| Power | watts | - |
| Calories | kcal | - |

## Need help?

- Ride with GPS API docs: https://ridewithgps.com/api/v1/doc
- File an issue: https://github.com/scriptsandthings/aioridewithgps/issues

## License

MIT - use it however you want.
