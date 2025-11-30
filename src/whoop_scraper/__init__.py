"""Whoop API scraper - collects health metrics and stores them in PostgreSQL."""

import argparse
import logging
import sys

import httpx
import psycopg

from whoop_scraper.auth import WhoopAuth
from whoop_scraper.config import get_settings
from whoop_scraper.db.schema import get_schema_sql, init_schema

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_init_db(args: argparse.Namespace) -> int:
    """Initialize the database schema."""
    settings = get_settings()

    if args.print_sql:
        print(get_schema_sql())
        return 0

    logger.info(
        "Connecting to database at %s:%d/%s", settings.db_host, settings.db_port, settings.db_name
    )

    try:
        with psycopg.connect(settings.database_url) as conn:
            init_schema(conn)
        logger.info("Schema initialization complete")
        return 0
    except psycopg.Error as e:
        logger.error("Database error: %s", e)
        return 1


def cmd_auth(args: argparse.Namespace) -> int:
    """Run OAuth2 authorization flow."""
    settings = get_settings()

    if not settings.client_id or not settings.client_secret:
        logger.error("WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET must be set")
        print("\nTo get OAuth credentials:")
        print("1. Go to https://developer.whoop.com/")
        print("2. Create a new application")
        print("3. Set redirect URI to: http://localhost:8080/callback")
        print("4. Copy Client ID and Client Secret")
        print("5. Set environment variables:")
        print("   export WHOOP_CLIENT_ID='your-client-id'")
        print("   export WHOOP_CLIENT_SECRET='your-client-secret'")
        return 1

    auth = WhoopAuth()

    if args.status:
        tokens = auth.storage.load()
        if tokens is None:
            print("No tokens stored. Run 'whoop-scraper auth' to authorize.")
            return 1
        print(f"Access token: {tokens.access_token[:20]}...")
        print(f"Expires at: {tokens.expires_at}")
        print(f"Expired: {tokens.is_expired()}")
        return 0

    if args.refresh:
        try:
            tokens = auth.refresh_tokens()
            print("Tokens refreshed successfully!")
            print(f"New access token: {tokens.access_token[:20]}...")
            print(f"Expires at: {tokens.expires_at}")
            return 0
        except (ValueError, httpx.HTTPError) as e:
            logger.error("Failed to refresh tokens: %s", e)
            return 1

    # Interactive authorization flow
    print("Starting OAuth2 authorization flow...")
    print(f"Using client ID: {settings.client_id[:10]}...")
    print("\nA browser window will open for you to authorize the application.")
    print("After authorization, you'll be redirected to localhost.\n")

    try:
        tokens = auth.authorize_interactive(port=args.port)
        print("\nAuthorization successful!")
        print(f"Access token: {tokens.access_token[:20]}...")
        if hasattr(auth.storage, "path"):
            print(f"Tokens saved to: {auth.storage.path}")
        else:
            print("Tokens saved to storage")
        return 0
    except ValueError as e:
        logger.error("Authorization failed: %s", e)
        return 1
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return 1


def cmd_test_api(args: argparse.Namespace) -> int:
    """Test API connection with current tokens."""
    auth = WhoopAuth()

    try:
        token = auth.get_valid_token()
    except ValueError as e:
        logger.error("No valid token: %s", e)
        print("Run 'whoop-scraper auth' first to authorize.")
        return 1

    # Test with user profile endpoint
    url = "https://api.prod.whoop.com/developer/v2/user/profile/basic"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print("API connection successful!")
        print(f"User ID: {data.get('user_id', 'N/A')}")
        print(f"Email: {data.get('email', 'N/A')}")
        print(f"First name: {data.get('first_name', 'N/A')}")
        return 0
    except httpx.HTTPError as e:
        logger.error("API request failed: %s", e)
        return 1


def cmd_scrape(args: argparse.Namespace) -> int:
    """Run the scraper."""
    from whoop_scraper.scraper import WhoopScraper

    settings = get_settings()
    days = args.days if args.days else settings.scrape_days

    try:
        scraper = WhoopScraper(
            days=days,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        stats = scraper.scrape_all()

        print(f"\nScrape completed ({scraper.start_date} to {scraper.end_date})")
        print("Results:")
        total_records = 0
        for endpoint, result in stats.items():
            if result.get("success"):
                count = result.get("records", 0)
                total_records += count
                print(f"  {endpoint}: {count} records")
            else:
                print(f"  {endpoint}: FAILED - {result.get('error', 'unknown')}")
        print(f"\nTotal: {total_records} records")
        return 0
    except Exception as e:
        logger.error("Scrape failed: %s", e)
        return 1


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="whoop-scraper",
        description="Scrape Whoop API health metrics and store in PostgreSQL",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # auth command
    auth_parser = subparsers.add_parser("auth", help="OAuth2 authorization")
    auth_parser.add_argument(
        "--status",
        action="store_true",
        help="Show current token status",
    )
    auth_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh tokens",
    )
    auth_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Local port for OAuth callback (default: 8080)",
    )
    auth_parser.set_defaults(func=cmd_auth)

    # test-api command
    test_parser = subparsers.add_parser("test-api", help="Test API connection")
    test_parser.set_defaults(func=cmd_test_api)

    # init-db command
    init_parser = subparsers.add_parser("init-db", help="Initialize database schema")
    init_parser.add_argument(
        "--print-sql",
        action="store_true",
        help="Print SQL schema without executing",
    )
    init_parser.set_defaults(func=cmd_init_db)

    # scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Run the scraper")
    scrape_parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days to scrape (default: WHOOP_SCRAPE_DAYS or 7)",
    )
    scrape_parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD) - overrides --days",
    )
    scrape_parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD) - overrides --days",
    )
    scrape_parser.set_defaults(func=cmd_scrape)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    sys.exit(args.func(args))
