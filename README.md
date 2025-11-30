# Whoop Scraper

A Python application that scrapes health data from the Whoop API and stores it in PostgreSQL. Designed for containerized deployments with database-backed token storage and optional encryption.

## Features

- OAuth2 authentication with automatic token refresh
- Database-backed token storage (persists across container restarts)
- Optional Fernet encryption for tokens at rest
- Scrapes all Whoop API endpoints:
  - User profile and body measurements
  - Physiological cycles (strain data)
  - Recovery scores
  - Sleep data (including naps)
  - Workouts
- Stores data in PostgreSQL with upsert support
- CLI interface for authorization and scraping
- Kubernetes CronJob ready

## Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/mischavandenburg/whoop-scraper.git
cd whoop-scraper

# Install dependencies with uv
uv sync

# Or with mise
mise install
mise exec -- uv sync
```

### Docker

```bash
docker pull ghcr.io/mischavandenburg/whoop-scraper:latest
```

## Configuration

Environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `WHOOP_CLIENT_ID` | Yes | OAuth2 client ID from Whoop Developer Portal |
| `WHOOP_CLIENT_SECRET` | Yes | OAuth2 client secret |
| `WHOOP_DB_HOST` | Yes | PostgreSQL host |
| `WHOOP_DB_PORT` | No | PostgreSQL port (default: 5432) |
| `WHOOP_DB_NAME` | Yes | Database name |
| `WHOOP_DB_USER` | Yes | Database user |
| `WHOOP_DB_PASSWORD` | Yes | Database password |
| `WHOOP_SCRAPE_DAYS` | No | Days of history to scrape (default: 7) |
| `WHOOP_ACCESS_TOKEN` | No | Initial access token for bootstrap |
| `WHOOP_REFRESH_TOKEN` | No | Initial refresh token for bootstrap |
| `WHOOP_ENCRYPTION_KEY` | No | Fernet key for encrypting tokens in database |

## Usage

### Initial Setup

1. Create an application at https://developer.whoop.com/
2. Set redirect URI to `http://localhost:8080/callback`
3. Copy your Client ID and Client Secret

### Authorization

```bash
# Set credentials
export WHOOP_CLIENT_ID='your-client-id'
export WHOOP_CLIENT_SECRET='your-client-secret'

# Run OAuth flow (opens browser)
whoop-scraper auth

# Check token status
whoop-scraper auth --status

# Test API connection
whoop-scraper test-api
```

### Database Setup

```bash
# Print SQL schema
whoop-scraper init-db --print-sql

# Initialize schema (requires DB connection)
whoop-scraper init-db
```

### Scraping

```bash
# Scrape last 7 days (default)
whoop-scraper scrape

# Scrape last 30 days
whoop-scraper scrape --days 30
```

## Token Refresh Behavior

The scraper automatically handles token refresh:

1. On startup, loads tokens from database (or env vars for initial bootstrap)
2. Before each API call, checks if access token is expired (with 5-min buffer)
3. If expired, uses refresh token to get new tokens from Whoop
4. New tokens (both access AND refresh) are saved to database
5. This ensures tokens persist across container restarts

## Token Security

For production deployments, enable encryption for tokens stored in the database:

```bash
# Generate a Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set the encryption key
export WHOOP_ENCRYPTION_KEY='your-generated-key'
```

When `WHOOP_ENCRYPTION_KEY` is set:
- Tokens are encrypted with Fernet (AES-128-CBC) before storing in PostgreSQL
- Tokens are decrypted when loaded from the database
- The encryption key should be stored securely (e.g., Azure Key Vault, AWS Secrets Manager)

## Kubernetes Deployment

### CronJob Example

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: whoop-scraper
spec:
  schedule: "0 6 * * *"  # Daily at 6 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: whoop-scraper
            image: ghcr.io/mischavandenburg/whoop-scraper:latest
            args: ["scrape", "--days", "7"]
            env:
            - name: WHOOP_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: whoop-secrets
                  key: client-id
            - name: WHOOP_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: whoop-secrets
                  key: client-secret
            - name: WHOOP_ENCRYPTION_KEY
              valueFrom:
                secretKeyRef:
                  name: whoop-secrets
                  key: encryption-key
            - name: WHOOP_DB_HOST
              value: "postgres.database.svc.cluster.local"
            - name: WHOOP_DB_NAME
              value: "whoop"
            - name: WHOOP_DB_USER
              valueFrom:
                secretKeyRef:
                  name: whoop-db-secrets
                  key: username
            - name: WHOOP_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: whoop-db-secrets
                  key: password
          restartPolicy: OnFailure
```

### Initial Token Bootstrap

For the first run in Kubernetes:

1. Run OAuth flow locally to get initial tokens
2. Store tokens in your secrets manager (e.g., Azure Key Vault)
3. Set `WHOOP_ACCESS_TOKEN` and `WHOOP_REFRESH_TOKEN` env vars for initial bootstrap
4. After first successful refresh, tokens are stored in database
5. Subsequent runs use database tokens (env vars only needed for bootstrap)

## Database Schema

The scraper creates these tables:

- `whoop_oauth_tokens` - OAuth tokens (single row, encrypted)
- `whoop_user_profile` - User profile information
- `whoop_body_measurement` - Height, weight, max heart rate
- `whoop_cycle` - Daily physiological cycles with strain scores
- `whoop_recovery` - Recovery scores, HRV, resting heart rate
- `whoop_sleep` - Sleep sessions with stage breakdowns
- `whoop_workout` - Workout activities with heart rate zones

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/

# Run tests
uv run pytest
```

## License

MIT
