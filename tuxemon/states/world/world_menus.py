# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

import pygame_menu

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.states.monster import MonsterMenuHandler

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.client import LocalPygameClient
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


WorldMenuGameObj = Callable[[], object]


def add_menu_items_to_pygame_menu(
    menu: pygame_menu.Menu,
    items: list[tuple[str, WorldMenuGameObj]],
) -> None:
    """Helper function to add items to a pygame_menu.Menu instance."""
    menu.clear()
    menu.add.vertical_fill()
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)
        menu.add.vertical_fill()

    width, height = prepare.SCREEN_SIZE
    widgets_size = menu.get_size(widget=True)
    b_width, b_height = menu.get_scrollarea().get_border_size()
    menu.resize(
        widgets_size[0],
        height - 2 * b_height,
        position=(width + b_width, b_height, False),
    )


class WorldMenuManager:
    """Manages persistent menu items and builds the dynamic world menu."""

    def __init__(self, client: LocalPygameClient) -> None:
        self.menu_items: list[tuple[str, WorldMenuGameObj]] = []
        self.menu_state: Optional[WorldMenuState] = None
        self.client = client

    def set_menu_state(self, menu_state: WorldMenuState) -> None:
        """Links the menu manager to a WorldMenuState instance."""
        self.menu_state = menu_state

    def item_exists(self, key: str) -> bool:
        """Checks if an item already exists in the manager's persistent menu items."""
        label = T.translate(key).upper()
        return any(item[0] == label for item in self.menu_items)

    def add_item(
        self, key: str, callback: WorldMenuGameObj, position: int = -1
    ) -> None:
        """Adds or updates a menu item to the manager's persistent list."""
        if self.item_exists(key):
            return

        label = T.translate(key).upper()
        new_item = (label, callback)

        if position == -1 or position >= len(self.menu_items):
            self.menu_items.append(new_item)
        else:
            self.menu_items.insert(position, new_item)

        self.update_menu_display()

    def remove_item(self, key: str) -> None:
        """Removes a menu item by its label key from the manager's persistent list."""
        initial_len = len(self.menu_items)
        self.menu_items = [
            item
            for item in self.menu_items
            if item[0] != T.translate(key).upper()
        ]
        if len(self.menu_items) < initial_len:
            self.update_menu_display()

    def update_menu_display(self) -> None:
        """Notifies the linked WorldMenuState to refresh its display."""
        if self.menu_state:
            self.menu_state.update_menu_from_manager()

    def _get_change_state_callback(
        self, state: str, **kwargs: Any
    ) -> Callable[[], object]:
        """Helper to create state change callbacks."""
        return partial(self.client.push_state, state, **kwargs)

    def _get_exit_game_callback(self) -> Callable[[], None]:
        """Helper to create exit game callback."""
        return lambda: self.client.event_engine.execute_action("quit")

    def build_current_menu_items(
        self, player: NPC
    ) -> list[tuple[str, WorldMenuGameObj]]:
        """
        Builds the complete list of menu items based on the player's state
        and any globally managed items.
        """
        assert self.menu_state
        param = {"character": player}
        change = self._get_change_state_callback
        exit_game = self._get_exit_game_callback()

        current_menu: list[tuple[str, WorldMenuGameObj]] = []

        if player.monsters and player.menu_monsters:
            current_menu.append(
                ("menu_monster", self.menu_state.open_monster_menu)
            )
        if player.items and player.menu_bag:
            current_menu.append(
                (
                    "menu_bag",
                    change(
                        "ItemMenuState", character=player, source=self.name
                    ),
                )
            )
        if player.menu_player:
            current_menu.append(
                ("menu_player", change("CharacterState", kwargs=param))
            )
        mission = (
            player.mission_controller.get_missions_with_met_prerequisites()
        )
        if mission:
            current_menu.append(
                ("menu_missions", change("MissionState", kwargs=param))
            )
        if player.menu_save:
            current_menu.append(("menu_save", change("SaveMenuState")))
        if player.menu_load:
            current_menu.append(("menu_load", change("LoadMenuState")))

        current_menu.append(("menu_options", change("ControlState")))
        current_menu.append(("exit", exit_game))

        for itm in player.items:
            if hasattr(itm, "world_menu") and itm.world_menu:
                if all(
                    hasattr(itm.world_menu, attr)
                    for attr in ["position", "label_key", "state"]
                ):
                    item_label = T.translate(itm.world_menu.label_key).upper()
                    if not any(
                        entry[0] == item_label for entry in current_menu
                    ):
                        current_menu.insert(
                            itm.world_menu.position,
                            (
                                itm.world_menu.label_key,
                                change(itm.world_menu.state, character=player),
                            ),
                        )

        current_menu.extend(self.menu_items)
        return current_menu


class WorldMenuState(PygameMenuState):
    """Menu for the world state."""

    def __init__(self, menu_manager: WorldMenuManager, character: NPC) -> None:
        """Initialize menu state and build menu separately."""
        self.char = character
        super().__init__(height=prepare.SCREEN_SIZE[1])
        self.menu_manager = menu_manager
        self.menu_manager.set_menu_state(self)
        self.update_menu_from_manager()
        self.handler = MonsterMenuHandler(self.client, self.char)

    def update_menu_from_manager(self) -> None:
        """Refreshes the menu display using items provided by the manager."""
        display = self.menu_manager.build_current_menu_items(self.char)
        add_menu_items_to_pygame_menu(self.menu, display)

    def open_monster_menu(self) -> None:
        self.handler.open_monster_menu()

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        width = self.menu.get_width(border=True)
        self.animation_offset = 0
        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.update_callback = self.update_animation_position
        return ani

    def animate_close(self) -> Animation:
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.update_callback = self.update_animation_position
        return ani
