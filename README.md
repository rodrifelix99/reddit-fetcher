# reddit-fetcher

Personal Reddit data fetcher for research and organization.
Read-only, low-volume, non-interactive.

---

## Features

- Fetch posts from any subreddit (hot / new / top / rising)
- Fetch a user's public submissions and comments
- Fetch your own saved posts (requires credentials)
- Persist results as structured JSON files for offline research

## Requirements

- Python 3.9+
- A Reddit OAuth2 application ([create one here](https://www.reddit.com/prefs/apps))

## Setup

```bash
# 1. Clone and install
pip install -e .

# 2. Configure credentials
cp .env.example .env
# Edit .env and fill in REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
```

## Usage

```bash
# Fetch top 50 hot posts from r/python
reddit-fetcher --limit 50 subreddit --name python --sort hot

# Fetch 25 newest posts from r/machinelearning
reddit-fetcher subreddit --name machinelearning --sort new

# Fetch 10 most recent posts by a user
reddit-fetcher --limit 10 user --name some_username --type posts

# Fetch a user's comments (sorted by top)
reddit-fetcher user --name some_username --type comments --sort top

# Fetch your 100 saved posts (requires REDDIT_USERNAME + REDDIT_PASSWORD in .env)
reddit-fetcher --limit 100 saved

# Write output to a custom directory
reddit-fetcher --output ./my_data subreddit --name python
```

Output JSON files are written to the `data/` directory by default.
Each file contains a `fetched_at` timestamp, a `count`, and a `records` list.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Project Structure

```
reddit_fetcher/
  auth.py       – Reddit OAuth2 authentication
  fetcher.py    – Data-fetching logic (Post / Comment models)
  storage.py    – JSON persistence
  cli.py        – Non-interactive command-line interface
tests/
  test_fetcher.py
  test_storage.py
  test_cli.py
```

## License

MIT
