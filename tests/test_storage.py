"""Tests for the Storage class."""

import json
import os

import pytest

from reddit_fetcher.fetcher import Comment, Post
from reddit_fetcher.storage import Storage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(output_dir=str(tmp_path))


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
        selftext="Hello world",
        created_utc=1700000000.0,
        is_self=True,
        flair="Discussion",
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


class TestStorage:
    def test_creates_output_dir(self, tmp_path):
        target = tmp_path / "new_subdir"
        assert not target.exists()
        Storage(output_dir=str(target))
        assert target.is_dir()

    def test_save_posts_returns_absolute_path(self, tmp_storage):
        path = tmp_storage.save([_sample_post()], "posts.json")
        assert os.path.isabs(path)
        assert path.endswith("posts.json")

    def test_save_writes_valid_json(self, tmp_storage):
        tmp_storage.save([_sample_post()], "posts.json")
        data = tmp_storage.load("posts.json")
        assert isinstance(data, dict)
        assert "records" in data
        assert "fetched_at" in data
        assert data["count"] == 1

    def test_save_post_fields(self, tmp_storage):
        tmp_storage.save([_sample_post()], "posts.json")
        data = tmp_storage.load("posts.json")
        record = data["records"][0]
        assert record["id"] == "abc123"
        assert record["title"] == "Test post"
        assert record["author"] == "test_user"
        assert record["score"] == 42

    def test_save_comment_fields(self, tmp_storage):
        tmp_storage.save([_sample_comment()], "comments.json")
        data = tmp_storage.load("comments.json")
        record = data["records"][0]
        assert record["id"] == "xyz789"
        assert record["body"] == "Nice post!"
        assert record["score"] == 10

    def test_save_multiple_records(self, tmp_storage):
        posts = [_sample_post(), _sample_post()]
        posts[1].id = "def456"
        tmp_storage.save(posts, "multi.json")
        data = tmp_storage.load("multi.json")
        assert data["count"] == 2
        assert len(data["records"]) == 2

    def test_save_overwrites_existing_file(self, tmp_storage):
        tmp_storage.save([_sample_post()], "posts.json")
        new_post = _sample_post()
        new_post.id = "new999"
        tmp_storage.save([new_post], "posts.json")
        data = tmp_storage.load("posts.json")
        assert data["count"] == 1
        assert data["records"][0]["id"] == "new999"

    def test_save_empty_list(self, tmp_storage):
        tmp_storage.save([], "empty.json")
        data = tmp_storage.load("empty.json")
        assert data["count"] == 0
        assert data["records"] == []

    def test_load_nonexistent_file_raises(self, tmp_storage):
        with pytest.raises(FileNotFoundError):
            tmp_storage.load("nonexistent.json")
