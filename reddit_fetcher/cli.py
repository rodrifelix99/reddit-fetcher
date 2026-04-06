"""Non-interactive command-line interface for reddit-fetcher."""

from __future__ import annotations

import argparse
import sys

from .auth import create_reddit
from .fetcher import Fetcher
from .storage import Storage


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reddit-fetcher",
        description=(
            "Personal Reddit data fetcher for research and organization. "
            "Read-only, low-volume, non-interactive."
        ),
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        default="data",
        help="Directory to write JSON output files (default: %(default)s).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of items to fetch (default: %(default)s, max: 100).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- subreddit ----------------------------------------------------------
    sub_p = subparsers.add_parser(
        "subreddit",
        help="Fetch posts from a subreddit.",
    )
    sub_p.add_argument(
        "--name",
        required=True,
        metavar="SUBREDDIT",
        help="Subreddit name (without r/).",
    )
    sub_p.add_argument(
        "--sort",
        choices=["hot", "new", "top", "rising"],
        default="hot",
        help="Post feed to fetch (default: %(default)s).",
    )

    # ---- user ---------------------------------------------------------------
    user_p = subparsers.add_parser(
        "user",
        help="Fetch public posts or comments by a Reddit user.",
    )
    user_p.add_argument(
        "--name",
        required=True,
        metavar="USERNAME",
        help="Reddit username (without u/).",
    )
    user_p.add_argument(
        "--type",
        dest="content_type",
        choices=["posts", "comments"],
        default="posts",
        help="Whether to fetch posts or comments (default: %(default)s).",
    )
    user_p.add_argument(
        "--sort",
        choices=["new", "hot", "top"],
        default="new",
        help="Sort order (default: %(default)s).",
    )

    # ---- saved --------------------------------------------------------------
    saved_p = subparsers.add_parser(
        "saved",
        help=(
            "Fetch saved posts for the authenticated user. "
            "Requires REDDIT_USERNAME and REDDIT_PASSWORD in .env."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point.  Returns an exit code (0 = success)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    limit: int = args.limit
    output: str = args.output

    # Determine whether we need authenticated (non-read-only) access
    need_auth = args.command == "saved"

    try:
        reddit = create_reddit(read_only=not need_auth)
    except EnvironmentError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    fetcher = Fetcher(reddit)
    storage = Storage(output_dir=output)

    try:
        if args.command == "subreddit":
            print(
                f"Fetching {limit} '{args.sort}' posts from r/{args.name} …",
                flush=True,
            )
            records = fetcher.fetch_subreddit_posts(
                subreddit=args.name, sort=args.sort, limit=limit
            )
            filename = f"subreddit_{args.name}_{args.sort}.json"

        elif args.command == "user":
            if args.content_type == "posts":
                print(
                    f"Fetching {limit} '{args.sort}' posts by u/{args.name} …",
                    flush=True,
                )
                records = fetcher.fetch_user_posts(
                    username=args.name, sort=args.sort, limit=limit
                )
                filename = f"user_{args.name}_posts_{args.sort}.json"
            else:
                print(
                    f"Fetching {limit} '{args.sort}' comments by u/{args.name} …",
                    flush=True,
                )
                records = fetcher.fetch_user_comments(
                    username=args.name, sort=args.sort, limit=limit
                )
                filename = f"user_{args.name}_comments_{args.sort}.json"

        else:  # saved
            print(f"Fetching {limit} saved posts …", flush=True)
            records = fetcher.fetch_saved_posts(limit=limit)
            filename = "saved_posts.json"

    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    path = storage.save(records, filename)
    print(f"Saved {len(records)} record(s) → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
