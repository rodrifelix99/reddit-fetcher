"""Reddit authentication helpers."""

from __future__ import annotations

import os

import praw
from dotenv import load_dotenv

load_dotenv()


def create_reddit(*, read_only: bool = True) -> praw.Reddit:
    """Return an authenticated PRAW Reddit instance.

    Credentials are read from environment variables (or a ``.env`` file):

    * ``REDDIT_CLIENT_ID`` – OAuth2 app client id (required)
    * ``REDDIT_CLIENT_SECRET`` – OAuth2 app client secret (required)
    * ``REDDIT_USER_AGENT`` – user-agent string (required)
    * ``REDDIT_USERNAME`` – Reddit account username (required when *read_only* is ``False``)
    * ``REDDIT_PASSWORD`` – Reddit account password (required when *read_only* is ``False``)

    Parameters
    ----------
    read_only:
        When ``True`` (default) the instance is limited to public, unauthenticated
        endpoints.  Set to ``False`` to enable user-specific endpoints such as
        fetching saved posts.
    """
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "reddit-fetcher/1.0")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set. "
            "Copy .env.example to .env and fill in your credentials."
        )

    kwargs: dict = dict(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    if not read_only:
        username = os.environ.get("REDDIT_USERNAME")
        password = os.environ.get("REDDIT_PASSWORD")
        if not username or not password:
            raise EnvironmentError(
                "REDDIT_USERNAME and REDDIT_PASSWORD must be set for "
                "user-specific endpoints (e.g. saved posts)."
            )
        kwargs["username"] = username
        kwargs["password"] = password

    reddit = praw.Reddit(**kwargs)
    reddit.read_only = read_only
    return reddit
