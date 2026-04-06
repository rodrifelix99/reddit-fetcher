"""JSON-based storage for fetched Reddit data."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Union

from .fetcher import Comment, Post


class Storage:
    """Persist fetched posts and comments to JSON files.

    Each :py:meth:`save` call writes (or appends to) a JSON file inside
    *output_dir*.  Files are named after the fetch operation and contain
    a list of records, making them easy to parse with any JSON tool.

    Parameters
    ----------
    output_dir:
        Directory where JSON files are stored.  Created automatically if it
        does not exist.
    """

    def __init__(self, output_dir: str = "data") -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save(
        self,
        records: List[Union[Post, Comment]],
        filename: str,
    ) -> str:
        """Write *records* to ``<output_dir>/<filename>``.

        Existing file content is **replaced** on each call so that the file
        always reflects the most recent fetch result.

        Parameters
        ----------
        records:
            List of :class:`~reddit_fetcher.fetcher.Post` or
            :class:`~reddit_fetcher.fetcher.Comment` objects to persist.
        filename:
            Target filename (e.g. ``subreddit_python_hot.json``).

        Returns
        -------
        str
            Absolute path of the written file.
        """
        payload = {
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
            "count": len(records),
            "records": [r.to_dict() for r in records],
        }
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return os.path.abspath(path)

    def load(self, filename: str) -> dict:
        """Load and return the raw JSON payload from *filename*."""
        path = os.path.join(self.output_dir, filename)
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
