# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from pygame_menu.locals import POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.db import ItemModel, db
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

ChoiceItemGameObj = Callable[[], None]


@dataclass
class MenuItemConfig:
    max_elements: int = 7
    max_height_percentage: float = 0.8
    length_name_item: int = 10
    scale_sprite: float = 0.5
    window_width_percentage_long: float = 0.4
    window_width_percentage_short: float = 0.3
    translate_percentage_long: float = 0.4
    translate_percentage_short: float = 0.3
    translate_percentage_vertical_offset: float = 0.05


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class ChoiceItem(PygameMenuState):
    """
    Game state with a graphic box and items (images) + labels.
    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, ChoiceItemGameObj]] = (),
        escape_key_exits: bool = False,
        config: Optional[MenuItemConfig] = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuItemConfig()
        theme = get_theme().copy()
        theme.scrollarea_position = POSITION_EAST

        self.width, self.height, self.translate_percentage = (
            self.calculate_window_size(menu)
        )
        super().__init__(width=self.width, height=self.height, **kwargs)

        for name, slug, callback in menu:
            self.add_item_menu_item(name, slug, callback)

        self.escape_key_exits = escape_key_exits

    def calculate_window_size(
        self, menu: Sequence[tuple[str, str, ChoiceItemGameObj]]
    ) -> tuple[int, int, float]:
        _width, _height = prepare.SCREEN_SIZE

        if len(menu) >= self.config.max_elements:
            height = _height * self.config.max_height_percentage
        else:
            height = (
                _height
                * (len(menu) / self.config.max_elements)
                * self.config.max_height_percentage
            )

        name_item = max(len(element[0]) for element in menu)
        if name_item > self.config.length_name_item:
            width = _width * self.config.window_width_percentage_long
            translate_percentage = self.config.translate_percentage_short
        else:
            width = _width * self.config.window_width_percentage_short
            translate_percentage = self.config.translate_percentage_long

        return int(width), int(height), translate_percentage

    def add_item_menu_item(
        self,
        name: str,
        slug: str,
        callback: ChoiceItemGameObj,
    ) -> None:
        item = ItemModel.lookup(slug, db)
        new_image = self._create_image(item.sprite)
        new_image.scale(
            prepare.SCALE * self.config.scale_sprite,
            prepare.SCALE * self.config.scale_sprite,
        )
        self.menu.add.image(new_image)
        self.menu.add.button(
            name,
            callback,
            font_size=self.font_size_smaller,
            float=True,
            selection_effect=HighlightSelection(),
        ).translate(
            fix_measure(self.width, self.translate_percentage),
            fix_measure(
                self.height, self.config.translate_percentage_vertical_offset
            ),
        )
