"""Shared functions for database connections."""

import pathlib
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Concatenate, Self

import numpy as np
import pandas as pd
from litestar.datastructures import State
from sqlalchemy.sql import text

from config import MODULE_DIR

SQL_DIR = pathlib.Path(MODULE_DIR, "dbcon/sql/")


class SQLLoader:
    """Auto-load SQL files based on attribute access."""

    def __init__(self: Self, sql_dir: pathlib.Path) -> None:
        """Initialize with the directory containing SQL files."""
        self.sql_dir = sql_dir
        self._cache: dict = {}

    def __getattr__(self: Self, name: str) -> text:
        """Load SQL from file on first access, then cache it."""
        if name.startswith("_"):
            msg = f"Attempt to access private attribute '{name}'"
            raise AttributeError(msg)

        if name not in self._cache:
            file_name = f"query_{name}.sql"
            file_path = self.sql_dir / file_name

            if not file_path.exists():
                msg = f"SQL file not found: {file_name}"
                raise FileNotFoundError(msg)

            with file_path.open() as file:
                self._cache[name] = text(file.read())

        return self._cache[name]


def clean_app_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply generic cleaning for a DF with app data from store_apps table.

    Required columns:
    - store
    - store_id
    - developer_id
    - installs
    - rating

    """
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df["rating"] = df["rating"].apply(lambda x: round(x, 2) if x else 0)
    ios_link = "https://apps.apple.com/us/app/-/id"
    play_link = "https://play.google.com/store/apps/details?id="
    play_dev_link = "play.google.com/store/apps/dev?id="
    play_dev_name_link = "play.google.com/store/apps/developer?id="
    ios_dev_link = "apps.apple.com/us/developer/-/id"
    df["store_link"] = (
        np.where(df["store"].str.contains("Google"), play_link, ios_link)
        + df["store_id"]
    )
    if "developer_id" in df.columns:
        is_dev_digits = df["developer_id"].astype(str).str.isdigit()
        is_store_google = df["store"].str.contains("Google")
        is_store_apple = df["store"].str.contains("Apple")

        df.loc[is_store_apple, "store_developer_link"] = (
            ios_dev_link + df["developer_id"]
        )
        df.loc[is_store_google, "store_developer_link"] = (
            play_dev_link + df["developer_id"]
        )
        df.loc[is_store_google & ~is_dev_digits, "store_developer_link"] = (
            play_dev_name_link + df["developer_id"]
        )

    date_cols = [
        "created_at",
        "store_last_updated",
        "updated_at",
        "adstxt_last_crawled",
        "sdk_last_crawled",
        "sdk_successful_last_crawled",
        "api_successful_last_crawled",
    ]
    for x in date_cols:
        if x not in df.columns:
            continue
        if df[x].notna().all():
            df[x] = df[x].dt.strftime("%Y-%m-%d")
    return df


def cache_by_params[**P, R](
    func: Callable[Concatenate[State, P], R],
) -> Callable[Concatenate[State, P], R]:
    """Cache function results based on parameters (excluding State).

    The State parameter is passed through but not used in the cache key.
    This works because State just holds references to the same database
    connections throughout the app lifetime.
    """
    cache = {}
    lock = Lock()

    @wraps(func)
    def wrapper(state: State, *args: P.args, **kwargs: P.kwargs) -> R:
        # Cache key only includes args/kwargs, NOT state
        cache_key = (args, tuple(sorted(kwargs.items())))

        if cache_key not in cache:
            with lock:
                # Double-check pattern for thread safety
                if cache_key not in cache:
                    cache[cache_key] = func(state, *args, **kwargs)

        return cache[cache_key]

    return wrapper


sql = SQLLoader(SQL_DIR)
