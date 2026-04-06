"""Tests for the Fetcher class."""

from unittest.mock import MagicMock, patch

import pytest
import praw.models

from reddit_fetcher.fetcher import Comment, Fetcher, Post


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_submission(**kwargs) -> MagicMock:
    defaults = dict(
        id="abc123",
        title="Test post",
        author=MagicMock(__str__=lambda s: "test_user"),
        subreddit=MagicMock(__str__=lambda s: "python"),
        url="https://example.com",
        permalink="/r/python/comments/abc123/test_post/",
        score=42,
        num_comments=7,
        selftext="Hello world",
        created_utc=1700000000.0,
        is_self=True,
        link_flair_text="Discussion",
    )
    defaults.update(kwargs)
    mock = MagicMock(spec=praw.models.Submission)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_comment(**kwargs) -> MagicMock:
    defaults = dict(
        id="xyz789",
        author=MagicMock(__str__=lambda s: "test_user"),
        subreddit=MagicMock(__str__=lambda s: "python"),
        body="Nice post!",
        score=10,
        permalink="/r/python/comments/abc123/test_post/xyz789/",
        created_utc=1700000100.0,
        link_id="t3_abc123",
        parent_id="t3_abc123",
    )
    defaults.update(kwargs)
    mock = MagicMock(spec=praw.models.Comment)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


# ---------------------------------------------------------------------------
# Post.from_submission
# ---------------------------------------------------------------------------


class TestPostFromSubmission:
    def test_basic_fields(self):
        sub = _make_submission()
        post = Post.from_submission(sub)

        assert post.id == "abc123"
        assert post.title == "Test post"
        assert post.author == "test_user"
        assert post.subreddit == "python"
        assert post.url == "https://example.com"
        assert post.permalink == "https://www.reddit.com/r/python/comments/abc123/test_post/"
        assert post.score == 42
        assert post.num_comments == 7
        assert post.selftext == "Hello world"
        assert post.created_utc == 1700000000.0
        assert post.is_self is True
        assert post.flair == "Discussion"

    def test_none_author(self):
        sub = _make_submission(author=None)
        post = Post.from_submission(sub)
        assert post.author is None

    def test_to_dict_contains_all_fields(self):
        sub = _make_submission()
        d = Post.from_submission(sub).to_dict()
        assert set(d.keys()) == {
            "id", "title", "author", "subreddit", "url", "permalink",
            "score", "num_comments", "selftext", "created_utc", "is_self", "flair",
        }


# ---------------------------------------------------------------------------
# Comment.from_comment
# ---------------------------------------------------------------------------


class TestCommentFromComment:
    def test_basic_fields(self):
        c = _make_comment()
        comment = Comment.from_comment(c)

        assert comment.id == "xyz789"
        assert comment.author == "test_user"
        assert comment.subreddit == "python"
        assert comment.body == "Nice post!"
        assert comment.score == 10
        assert comment.permalink == "https://www.reddit.com/r/python/comments/abc123/test_post/xyz789/"
        assert comment.created_utc == 1700000100.0
        assert comment.link_id == "t3_abc123"
        assert comment.parent_id == "t3_abc123"

    def test_none_author(self):
        c = _make_comment(author=None)
        comment = Comment.from_comment(c)
        assert comment.author is None

    def test_to_dict_contains_all_fields(self):
        c = _make_comment()
        d = Comment.from_comment(c).to_dict()
        assert set(d.keys()) == {
            "id", "author", "subreddit", "body", "score", "permalink",
            "created_utc", "link_id", "parent_id",
        }


# ---------------------------------------------------------------------------
# Fetcher methods
# ---------------------------------------------------------------------------


def _make_reddit(*, read_only: bool = True) -> MagicMock:
    reddit = MagicMock()
    reddit.read_only = read_only
    return reddit


class TestFetcherSubreddit:
    def test_fetch_subreddit_posts_hot(self):
        sub1 = _make_submission(id="s1", title="Post 1")
        sub2 = _make_submission(id="s2", title="Post 2")

        reddit = _make_reddit()
        reddit.subreddit.return_value.hot.return_value = iter([sub1, sub2])

        fetcher = Fetcher(reddit)
        posts = fetcher.fetch_subreddit_posts("python", sort="hot", limit=2)

        reddit.subreddit.assert_called_once_with("python")
        assert len(posts) == 2
        assert posts[0].id == "s1"
        assert posts[1].id == "s2"

    def test_fetch_subreddit_posts_new(self):
        sub = _make_submission(id="s1")
        reddit = _make_reddit()
        reddit.subreddit.return_value.new.return_value = iter([sub])

        fetcher = Fetcher(reddit)
        posts = fetcher.fetch_subreddit_posts("worldnews", sort="new", limit=1)
        assert len(posts) == 1

    def test_fetch_subreddit_posts_invalid_sort(self):
        fetcher = Fetcher(_make_reddit())
        with pytest.raises(ValueError, match="sort must be one of"):
            fetcher.fetch_subreddit_posts("python", sort="best")


class TestFetcherUser:
    def test_fetch_user_posts(self):
        sub = _make_submission(id="u1", title="My post")
        reddit = _make_reddit()
        reddit.redditor.return_value.submissions.new.return_value = iter([sub])

        fetcher = Fetcher(reddit)
        posts = fetcher.fetch_user_posts("test_user", sort="new", limit=1)

        reddit.redditor.assert_called_once_with("test_user")
        assert len(posts) == 1
        assert posts[0].id == "u1"

    def test_fetch_user_comments(self):
        c = _make_comment(id="c1")
        reddit = _make_reddit()
        reddit.redditor.return_value.comments.new.return_value = iter([c])

        fetcher = Fetcher(reddit)
        comments = fetcher.fetch_user_comments("test_user", sort="new", limit=1)
        assert len(comments) == 1
        assert comments[0].id == "c1"

    def test_fetch_user_posts_invalid_sort(self):
        fetcher = Fetcher(_make_reddit())
        with pytest.raises(ValueError, match="sort must be one of"):
            fetcher.fetch_user_posts("test_user", sort="rising")

    def test_fetch_user_comments_invalid_sort(self):
        fetcher = Fetcher(_make_reddit())
        with pytest.raises(ValueError, match="sort must be one of"):
            fetcher.fetch_user_comments("test_user", sort="rising")


class TestFetcherSaved:
    def test_fetch_saved_posts_requires_auth(self):
        fetcher = Fetcher(_make_reddit(read_only=True))
        with pytest.raises(RuntimeError, match="read_only"):
            fetcher.fetch_saved_posts()

    def test_fetch_saved_posts(self):
        sub = _make_submission(id="saved1")
        reddit = _make_reddit(read_only=False)
        reddit.user.me.return_value.saved.return_value = iter([sub])

        fetcher = Fetcher(reddit)
        posts = fetcher.fetch_saved_posts(limit=1)
        assert len(posts) == 1
        assert posts[0].id == "saved1"

    def test_fetch_saved_posts_skips_comments(self):
        """Comments in the saved list should be ignored."""
        sub = _make_submission(id="saved1")
        comment = _make_comment(id="c1")
        reddit = _make_reddit(read_only=False)
        reddit.user.me.return_value.saved.return_value = iter([comment, sub])

        fetcher = Fetcher(reddit)
        posts = fetcher.fetch_saved_posts(limit=2)
        # only the submission should be included
        assert len(posts) == 1
        assert posts[0].id == "saved1"
