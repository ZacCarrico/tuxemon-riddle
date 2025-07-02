# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import DialogueModel, db

logger = logging.getLogger(__name__)


class DialogueStyleCache:
    """
    Handles lookup and caching of DialogueModel styles.

    Usage:
        style_cache = DialogueStyleCache()
        style = style_cache.get("default")
    """

    def __init__(self) -> None:
        self._cache: dict[str, DialogueModel] = {}

    def get(self, style_key: str) -> DialogueModel:
        """
        Retrieves a DialogueModel by key, caching the result.

        Raises:
            RuntimeError if style is not found in the DB.
        """
        if style_key in self._cache:
            return self._cache[style_key]

        try:
            style = DialogueModel.lookup(style_key, db)
            self._cache[style_key] = style
            return style
        except KeyError:
            logger.warning(f"Dialogue style '{style_key}' not found in DB.")
            raise RuntimeError(f"Dialogue style '{style_key}' not found")

    def clear(self) -> None:
        """Clears the internal style cache."""
        self._cache.clear()

    def preload(self, keys: list[str]) -> None:
        """Preloads multiple styles into cache, useful during scene setup."""
        for key in keys:
            if key not in self._cache:
                try:
                    self._cache[key] = DialogueModel.lookup(key, db)
                except KeyError:
                    logger.warning(f"Failed to preload dialogue style '{key}'")
