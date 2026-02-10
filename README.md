# Dream League Bonus Tracker

A Python API and CLI tool that tracks bonus usage in the [Sport5 Dream League](https://dreamteam.sport5.co.il) (ליגת החלומות) fantasy football game.

## What It Does

Each team in Dream League has **4 bonuses** they can use throughout the season:

| Bonus ID | Name              | Description                  |
|----------|-------------------|------------------------------|
| 1        | Triple Captain    | Captain scores triple points |
| 2        | 15 Subs           | 15 substitutions allowed     |
| 3        | Double Captains   | Two captains for the round   |
| 4        | Full Squad Points  | All squad players score      |

This tool lets you check which bonuses a team (or all teams in a league) have already used and which ones remain.

## Architecture

```
dream_league_bonus_tracker/
    config.py          # Settings via pydantic-settings (.env + CLI args)
    models.py          # Pydantic models for API responses
    client.py          # DreamTeamClient - HTTP client with auth
    service.py         # BonusService - business logic
    api.py             # FastAPI app + endpoints
    cli.py             # Click CLI
    main.py            # Entrypoint
tests/
    conftest.py        # Shared fixtures
    test_models.py     # Model parsing tests
    test_service.py    # Business logic tests
    test_client.py     # HTTP client tests
```

## Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)

### Installation

```bash
# Clone the repo
git clone https://github.com/baraklevycode/dreamLeagueBonusTracker.git
cd dreamLeagueBonusTracker

# Install dependencies
poetry install
```

### Configuration

Copy the example env file and fill in your Sport5 credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
DREAMTEAM_EMAIL=your_email@example.com
DREAMTEAM_PASSWORD=your_password
DREAMTEAM_SEASON_ID=6
DREAMTEAM_BASE_URL=https://dreamteam.sport5.co.il
```

## Usage

### REST API (FastAPI)

Start the server:

```bash
poetry run tracker serve --host 127.0.0.1 --port 8000
```

Then open your browser:

| Endpoint                              | Description                              |
|---------------------------------------|------------------------------------------|
| `GET /team/{user_id}/bonuses`         | Bonus status for a specific team         |
| `GET /league/{league_id}/bonuses`     | Bonus status for all teams in a league   |
| `GET /docs`                           | Interactive Swagger UI                   |

**Examples:**

```bash
# Get bonuses for a specific user
curl http://127.0.0.1:8000/team/12345/bonuses

# Get bonuses for all teams in a league
curl http://127.0.0.1:8000/league/99999/bonuses
```

### CLI

```bash
# Team bonuses
poetry run tracker team-bonuses --user-id 12345

# League bonuses
poetry run tracker league-bonuses --league-id 99999

# With explicit credentials (overrides .env)
poetry run tracker team-bonuses --user-id 12345 --email you@example.com --password yourpass
```

### Example Response

```json
{
  "user_id": 12345,
  "team_name": "My Fantasy FC",
  "creator_name": "John Doe",
  "total_points": 950,
  "used_bonuses": [
    {
      "bonus_id": 1,
      "bonus_name": "Triple Captain",
      "usage_round_id": 118,
      "usage_date": "2025-11-10T12:00:00+02:00"
    },
    {
      "bonus_id": 4,
      "bonus_name": "Full Squad Points",
      "usage_round_id": 126,
      "usage_date": "2026-01-05T10:30:00+02:00"
    }
  ],
  "remaining_bonuses": ["15 Subs", "Double Captains"],
  "used_count": 2,
  "remaining_count": 2
}
```

## Running Tests

```bash
poetry run pytest --cov=dream_league_bonus_tracker/ --cov-branch --cov-report term tests/ -v
```

## Sport5 API Endpoints Used

- `POST /api/Account/Login` - Authentication (ASP.NET Core cookie auth)
- `GET /api/UserTeam/GetUserAndTeam?seasonId={sid}&userId={uid}` - Team data with bonus usage
- `GET /api/CustomLeagues/GetLeagueData?seasonId={sid}&leagueId={lid}&teamId=null&isPerRound=false&pageIndex=0&searchText=` - League data with all teams
