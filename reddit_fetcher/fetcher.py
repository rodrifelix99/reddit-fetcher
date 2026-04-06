"""Core data-fetching logic."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Optional, Union

import praw
import praw.models


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Post:
    """Represents a Reddit submission (link or self-post)."""

    id: str
    title: str
    author: Optional[str]
    subreddit: str
    url: str
    permalink: str
    score: int
    num_comments: int
    selftext: str
    created_utc: float
    is_self: bool
    flair: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_submission(cls, submission: praw.models.Submission) -> "Post":
        return cls(
            id=submission.id,
            title=submission.title,
            author=str(submission.author) if submission.author else None,
            subreddit=str(submission.subreddit),
            url=submission.url,
            permalink=f"https://www.reddit.com{submission.permalink}",
            score=submission.score,
            num_comments=submission.num_comments,
            selftext=submission.selftext or "",
            created_utc=submission.created_utc,
            is_self=submission.is_self,
            flair=getattr(submission, "link_flair_text", None),
        )


@dataclass
class Comment:
    """Represents a Reddit comment."""

    id: str
    author: Optional[str]
    subreddit: str
    body: str
    score: int
    permalink: str
    created_utc: float
    link_id: str
    parent_id: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_comment(cls, comment: praw.models.Comment) -> "Comment":
        return cls(
            id=comment.id,
            author=str(comment.author) if comment.author else None,
            subreddit=str(comment.subreddit),
            body=comment.body,
            score=comment.score,
            permalink=f"https://www.reddit.com{comment.permalink}",
            created_utc=comment.created_utc,
            link_id=comment.link_id,
            parent_id=comment.parent_id,
        )


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

_SORT_FUNCS_SUB = ("hot", "new", "top", "rising")
_SORT_FUNCS_USER = ("new", "hot", "top")


class Fetcher:
    """High-level wrapper around PRAW for read-only, low-volume data fetching."""

    def __init__(self, reddit: praw.Reddit) -> None:
        self.reddit = reddit

    # ------------------------------------------------------------------
    # Subreddit
    # ------------------------------------------------------------------

    def fetch_subreddit_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 25,
    ) -> List[Post]:
        """Return *limit* posts from *subreddit* ordered by *sort*.

        Parameters
        ----------
        subreddit:
            Subreddit name (without the ``r/`` prefix).
        sort:
            One of ``hot``, ``new``, ``top``, ``rising``.
        limit:
            Number of posts to retrieve (max 100 per Reddit's API).
        """
        if sort not in _SORT_FUNCS_SUB:
            raise ValueError(f"sort must be one of {_SORT_FUNCS_SUB}, got {sort!r}")
        sub = self.reddit.subreddit(subreddit)
        feed = getattr(sub, sort)
        return [Post.from_submission(s) for s in feed(limit=limit)]

    # ------------------------------------------------------------------
    # User submissions / comments
    # ------------------------------------------------------------------

    def fetch_user_posts(
        self,
        username: str,
        sort: str = "new",
        limit: int = 25,
    ) -> List[Post]:
        """Return *limit* submissions by *username*."""
        if sort not in _SORT_FUNCS_USER:
            raise ValueError(f"sort must be one of {_SORT_FUNCS_USER}, got {sort!r}")
        redditor = self.reddit.redditor(username)
        feed = getattr(redditor.submissions, sort)
        return [Post.from_submission(s) for s in feed(limit=limit)]

    def fetch_user_comments(
        self,
        username: str,
        sort: str = "new",
        limit: int = 25,
    ) -> List[Comment]:
        """Return *limit* comments by *username*."""
        if sort not in _SORT_FUNCS_USER:
            raise ValueError(f"sort must be one of {_SORT_FUNCS_USER}, got {sort!r}")
        redditor = self.reddit.redditor(username)
        feed = getattr(redditor.comments, sort)
        return [Comment.from_comment(c) for c in feed(limit=limit)]

    # ------------------------------------------------------------------
    # Authenticated-user saved posts
    # ------------------------------------------------------------------

    def fetch_saved_posts(self, limit: int = 25) -> List[Post]:
        """Return *limit* saved submissions for the authenticated user.

        Requires the Reddit instance to have been created with
        ``read_only=False`` and valid username/password credentials.
        """
        if self.reddit.read_only:
            raise RuntimeError(
                "fetch_saved_posts requires an authenticated (non-read-only) "
                "Reddit instance.  Re-create with read_only=False."
            )
        me = self.reddit.user.me()
        posts: List[Post] = []
        for item in me.saved(limit=limit):
            if isinstance(item, praw.models.Submission):
                posts.append(Post.from_submission(item))
        return posts
