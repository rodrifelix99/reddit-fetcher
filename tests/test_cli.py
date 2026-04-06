"""Tests for the CLI entry point."""

from unittest.mock import MagicMock, patch

import pytest

from reddit_fetcher.cli import main
from reddit_fetcher.fetcher import Comment, Post


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _sample_post() -> Post:
    return Post(
        id="abc123",
        title="Test post",
        author="test_user",
        subreddit="python",
        url="https://example.com",
        permalink="https://www.reddit.com/r/python/comments/abc123/",
        score=42,
        num_comments=7,
        selftext="",
        created_utc=1700000000.0,
        is_self=True,
        flair=None,
    )


def _sample_comment() -> Comment:
    return Comment(
        id="xyz789",
        author="test_user",
        subreddit="python",
        body="Nice post!",
        score=10,
        permalink="https://www.reddit.com/r/python/comments/abc123/xyz789/",
        created_utc=1700000100.0,
        link_id="t3_abc123",
        parent_id="t3_abc123",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCLISubreddit:
    def test_subreddit_command(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit") as mock_create,
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_subreddit_posts.return_value = [_sample_post()]
            MockFetcher.return_value = mock_fetcher

            mock_storage = MagicMock()
            mock_storage.save.return_value = str(tmp_path / "subreddit_python_hot.json")
            MockStorage.return_value = mock_storage

            rc = main(["--output", str(tmp_path), "--limit", "5", "subreddit", "--name", "python", "--sort", "hot"])

        assert rc == 0
        mock_fetcher.fetch_subreddit_posts.assert_called_once_with(
            subreddit="python", sort="hot", limit=5
        )
        mock_storage.save.assert_called_once()
        args, _ = mock_storage.save.call_args
        assert args[1] == "subreddit_python_hot.json"

    def test_subreddit_default_sort_is_hot(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit"),
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_subreddit_posts.return_value = []
            MockFetcher.return_value = mock_fetcher
            MockStorage.return_value.save.return_value = str(tmp_path / "out.json")

            main(["subreddit", "--name", "python"])

        _, kwargs = mock_fetcher.fetch_subreddit_posts.call_args
        assert kwargs["sort"] == "hot"


class TestCLIUser:
    def test_user_posts_command(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit"),
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_user_posts.return_value = [_sample_post()]
            MockFetcher.return_value = mock_fetcher
            MockStorage.return_value.save.return_value = str(tmp_path / "out.json")

            rc = main(["user", "--name", "test_user", "--type", "posts"])

        assert rc == 0
        mock_fetcher.fetch_user_posts.assert_called_once_with(
            username="test_user", sort="new", limit=25
        )

    def test_user_comments_command(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit"),
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_user_comments.return_value = [_sample_comment()]
            MockFetcher.return_value = mock_fetcher
            MockStorage.return_value.save.return_value = str(tmp_path / "out.json")

            rc = main(["user", "--name", "test_user", "--type", "comments"])

        assert rc == 0
        mock_fetcher.fetch_user_comments.assert_called_once_with(
            username="test_user", sort="new", limit=25
        )

    def test_filename_includes_content_type(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit"),
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_user_comments.return_value = []
            MockFetcher.return_value = mock_fetcher
            mock_storage = MagicMock()
            mock_storage.save.return_value = str(tmp_path / "out.json")
            MockStorage.return_value = mock_storage

            main(["user", "--name", "alice", "--type", "comments"])

        args, _ = mock_storage.save.call_args
        assert "comments" in args[1]
        assert "alice" in args[1]


class TestCLISaved:
    def test_saved_command(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit") as mock_create,
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_saved_posts.return_value = [_sample_post()]
            MockFetcher.return_value = mock_fetcher
            MockStorage.return_value.save.return_value = str(tmp_path / "saved_posts.json")

            rc = main(["saved"])

        assert rc == 0
        # saved command must use authenticated reddit
        mock_create.assert_called_once_with(read_only=False)
        mock_fetcher.fetch_saved_posts.assert_called_once_with(limit=25)

    def test_saved_filename_is_saved_posts(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit"),
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage") as MockStorage,
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_saved_posts.return_value = []
            MockFetcher.return_value = mock_fetcher
            mock_storage = MagicMock()
            mock_storage.save.return_value = str(tmp_path / "saved_posts.json")
            MockStorage.return_value = mock_storage

            main(["saved"])

        args, _ = mock_storage.save.call_args
        assert args[1] == "saved_posts.json"


class TestCLIErrors:
    def test_missing_credentials_returns_1(self):
        with patch("reddit_fetcher.cli.create_reddit", side_effect=EnvironmentError("missing creds")):
            rc = main(["subreddit", "--name", "python"])
        assert rc == 1

    def test_runtime_error_returns_1(self, tmp_path):
        with (
            patch("reddit_fetcher.cli.create_reddit"),
            patch("reddit_fetcher.cli.Fetcher") as MockFetcher,
            patch("reddit_fetcher.cli.Storage"),
        ):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_subreddit_posts.side_effect = RuntimeError("boom")
            MockFetcher.return_value = mock_fetcher

            rc = main(["subreddit", "--name", "python"])

        assert rc == 1
