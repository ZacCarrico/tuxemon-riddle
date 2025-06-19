# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tuxemon.db import AttributesModel, ShapeModel, db
from tuxemon.formula import calculate_base_stats

if TYPE_CHECKING:
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


class Shape:
    """A shape holds all the values (speed, ranged, etc.)."""

    _shapes: dict[str, Shape] = {}

    # def __init__(self, slug: str) -> None:
    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug = slug
        self.attributes = AttributesModel(
            armour=1, dodge=1, hp=1, melee=1, ranged=1, speed=1
        )
        if self.slug:
            self.load(self.slug)
        # self.load(slug)

    def load(self, slug: str) -> None:
        """Loads shape."""

        if slug in Shape._shapes:
            cached_shape = Shape._shapes[slug]
            self.slug = slug
            self.attributes = cached_shape.attributes
            return

        results = ShapeModel.lookup(slug, db)
        self.attributes = results.attributes

        Shape._shapes[slug] = self

    @classmethod
    def get_shape(cls, slug: str) -> Optional[Shape]:
        """
        Retrieves a Shape object by its slug.

        Parameters:
            slug: The unique identifier for the shape.

        Returns:
            The Shape object if found, otherwise None.
        """
        return cls._shapes.get(slug)

    @classmethod
    def load_all_shapes(cls) -> None:
        """Loads all shapes from the database into the cache."""
        try:
            all_shape_slugs = list(db.database["shape"])
            for slug in all_shape_slugs:
                cls(slug)
        except Exception as e:
            logger.error(f"Failed to load all shapes: {e}")

    @classmethod
    def get_all_shapes(cls) -> dict[str, Shape]:
        """
        Returns all loaded shapes.

        Returns:
            A dictionary of all loaded Shape objects.
        """
        if not cls._shapes:
            cls.load_all_shapes()
        return cls._shapes

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the shape cache."""
        cls._shapes.clear()

    def __repr__(self) -> str:
        return f"Shape(slug={self.slug}, attributes={self.attributes})"


# self.shape: Optional[ShapeHandler] = None
# self.shape = ShapeHandler(slug)


class ShapeHandler:
    """
    Handles the shape-related attributes and calculations.
    """

    def __init__(self, shape_slug: str):
        self._shape = Shape(shape_slug)

    @property
    def slug(self) -> str:
        return self._shape.slug

    @property
    def attributes(self) -> AttributesModel:
        return self._shape.attributes

    def apply_base_stat_calculation(
        self, monster: Monster, multiplier: int
    ) -> None:
        """
        Applies base stat calculations to the monster based on its shape.
        """
        calculate_base_stats(monster, self.attributes, multiplier)

    def update_shape_attributes(self, new_attributes: AttributesModel) -> None:
        """Updates the shape attributes."""
        self._shape.attributes = new_attributes
