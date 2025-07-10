# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.db import MonsterModel, db
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session


@dataclass
class MenuMonsterConfig:
    max_elements: int = 15
    max_height_percentage: float = 0.8
    animation_duration: float = 0.2
    animation_start_size: float = 0.0
    animation_end_size: float = 1.0
    number_widgets: int = 3
    number_columns: int = 5
    scale_sprite: float = 0.4
    vertical_fill: int = 15


class ChoiceMonster(PygameMenuState):
    """
    Game state with a graphic box and monsters (images) + labels.
    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        config: Optional[MenuMonsterConfig] = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuMonsterConfig()
        theme = get_theme().copy()
        if len(menu) > self.config.max_elements:
            theme.scrollarea_position = POSITION_EAST

        rows = (
            math.ceil(len(menu) / self.config.number_columns)
            * self.config.number_widgets
        )
        super().__init__(
            columns=self.config.number_columns, rows=rows, **kwargs
        )

        for name, slug, callback in menu:
            self.add_monster_menu_item(name, slug, callback)

        self.animation_size = self.config.animation_start_size
        self.escape_key_exits = escape_key_exits

    def add_monster_menu_item(
        self,
        name: str,
        slug: str,
        callback: Callable[[], None],
    ) -> None:
        monster = MonsterModel.lookup(slug, db)
        path = f"gfx/sprites/battle/{monster.slug}-front.png"
        new_image = self._create_image(path)
        new_image.scale(
            prepare.SCALE * self.config.scale_sprite,
            prepare.SCALE * self.config.scale_sprite,
        )

        def open_journal() -> None:
            action = self.client.event_engine
            _set_tuxepedia = ["player", monster.slug, "caught"]
            action.execute_action("set_tuxepedia", _set_tuxepedia, True)
            self.client.push_state(
                "JournalInfoState",
                character=local_session.player,
                monster=monster,
                source=self.name,
            )
            action.execute_action("clear_tuxepedia", [monster.slug], True)

        self.menu.add.banner(
            new_image,
            open_journal,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )
        self.menu.add.button(
            name,
            callback,
            font_size=self.font_size_small,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )
        self.menu.add.vertical_fill(self.config.vertical_fill)

    def update_animation_size(self) -> None:
        width, height = prepare.SCREEN_SIZE
        widgets_size = self.menu.get_size(widget=True)

        _width = widgets_size[0]
        _height = widgets_size[1]

        if _width >= width:
            _width = width
        if _height >= height:
            _height = int(height * self.config.max_height_percentage)

        self.menu.resize(
            max(1, int(_width * self.animation_size)),
            max(1, int(_height * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.
        """
        ani = self.animate(
            self,
            animation_size=self.config.animation_end_size,
            duration=self.config.animation_duration,
        )
        ani.update_callback = self.update_animation_size

        return ani
