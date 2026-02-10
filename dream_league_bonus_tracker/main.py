"""Entrypoint for running the FastAPI server."""

import uvicorn


def main() -> None:
    """Run the FastAPI application with uvicorn."""
    uvicorn.run(
        "dream_league_bonus_tracker.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
