# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

from pygame.rect import Rect

from tuxemon.db import ItemCategory
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.monster import Monster
from tuxemon.states.items.item_menu import ItemMenuState

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState


MenuGameObj = Callable[[], None]

from dataclasses import dataclass, field

from tuxemon.monster import Monster


@dataclass
class ParkTracker:
    """Tracks unique monsters, sightings, failed captures, and successful captures in the park."""

    seen_monsters: set[Monster] = field(default_factory=set)
    unique_count: int = 0
    failed_attempts: int = 0
    seen_counts: dict[Monster, int] = field(default_factory=dict)
    successful_captures: int = 0

    def track_monster(self, monster: Monster) -> None:
        """Increases count only if a new monster appears and tracks sighting frequency."""
        if monster not in self.seen_monsters:
            self.seen_monsters.add(monster)
            self.unique_count += 1
        self.seen_counts[monster] = self.seen_counts.get(monster, 0) + 1

    def record_failed_attempt(self) -> None:
        """Records a failed capture attempt (generic for all monsters)."""
        self.failed_attempts += 1

    def record_successful_capture(self) -> None:
        """Records a successful capture in the park session."""
        self.successful_captures += 1

    def clear_all(self) -> None:
        """Resets all tracking data, including seen monsters, failures, and successes."""
        self.seen_monsters.clear()
        self.seen_counts.clear()
        self.failed_attempts = 0
        self.successful_captures = 0
        self.unique_count = 0


# self.park_tracker = ParkTracker()
# self.park_tracker.track_monster(self.monster)  # Track sighting
# self.park_tracker.record_failed_attempt()  # On failed capture
# self.park_tracker.record_successful_capture()  # On successful capture


class ParkMenuKeys(Enum):
    BALL = auto()
    FOOD = auto()
    DOLL = auto()
    RUN = auto()


class MainParkMenuState(PopUpMenu[MenuGameObj]):
    """Main menu Park: ball, food, doll and run"""

    escape_key_exits = False
    columns = 2

    def __init__(
        self, session: Session, cmb: CombatState, monster: Monster
    ) -> None:
        super().__init__()
        self.rect = self.calculate_menu_rectangle()
        self.session = session
        self.combat = cmb
        self.player = cmb.players[0]  # human
        self.enemy = cmb.players[1]  # ai
        self.monster = monster
        self.opponents = cmb.field_monsters.get_monsters(self.enemy)
        self.itm_description: Optional[str] = None
        params = {"player": monster.get_owner().name}
        message = T.format("combat_player_choice", params)
        self.combat.alert(message)

    def calculate_menu_rectangle(self) -> Rect:
        rect_screen = self.client.screen.get_rect()
        menu_width = rect_screen.w // 2.5
        menu_height = rect_screen.h // 4
        rect = Rect(0, 0, menu_width, menu_height)
        rect.bottomright = rect_screen.w, rect_screen.h
        return rect

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        self.combat.hud_manager.delete_hud(self.monster)
        self.combat.update_hud(self.player, False)

        menu_items_map = (
            (ParkMenuKeys.BALL, "menu_ball", self.throw_tuxeball),
            (ParkMenuKeys.FOOD, "menu_food", self.open_item_menu),
            (ParkMenuKeys.DOLL, "menu_doll", self.open_item_menu),
            (ParkMenuKeys.RUN, "menu_run", self.run),
        )

        for menu_key_enum, translation_key, callback in menu_items_map:
            label_base = T.translate(translation_key).upper()
            item_count = 1

            if menu_key_enum == ParkMenuKeys.FOOD:
                item_count = self.check_category("food")
            elif menu_key_enum == ParkMenuKeys.DOLL:
                item_count = self.check_category("doll")

            label = (
                f"{label_base}x{item_count}"
                if item_count > 0
                and menu_key_enum in {ParkMenuKeys.FOOD, ParkMenuKeys.DOLL}
                else label_base
            )
            is_enabled = item_count > 0 or menu_key_enum not in {
                ParkMenuKeys.FOOD,
                ParkMenuKeys.DOLL,
            }

            image = (
                self.shadow_text(label)
                if is_enabled
                else self.shadow_text(label, fg=self.unavailable_color)
            )

            menu = MenuItem(image, label, translation_key, callback)
            menu.enabled = is_enabled
            yield menu

    def run(self) -> None:
        self.combat.clean_combat()
        self.combat.field_monsters.clear_all()
        self.combat.players.clear()

    def check_category(self, cat_slug: str) -> int:
        category = sum(
            [
                itm.quantity
                for itm in self.player.items.get_items()
                if itm.category == cat_slug
            ]
        )
        return category

    def throw_tuxeball(self) -> None:
        tuxeball = self.player.items.find_item("tuxeball_park")
        if tuxeball:
            self.deliver_action(tuxeball)

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""
        choice = self.get_selected_item()
        if choice:
            self.itm_description = choice.description

        def choose_item() -> None:
            menu = self.client.push_state(
                ItemMenuState(self.player, self.name)
            )
            menu.is_valid_entry = validate  # type: ignore[method-assign]
            menu.on_menu_selection = choose_target  # type: ignore[method-assign]

        def validate(item: Optional[Item]) -> bool:
            """Validates if the selected item from the sub-menu is allowed."""
            ret = False
            if item:
                if self.itm_description == T.translate(
                    ParkMenuKeys.DOLL.name.lower()
                ):
                    if item.category == ItemCategory.potion:
                        ret = True
                elif self.itm_description == T.translate(
                    ParkMenuKeys.FOOD.name.lower()
                ):
                    if item.category == ItemCategory.potion:
                        ret = True
            return ret

        def choose_target(menu_item: MenuItem[Item]) -> None:
            item = menu_item.game_object
            self.deliver_action(item)
            self.client.pop_state()

        choose_item()

    def deliver_action(self, item: Item) -> None:
        enemy = self.opponents[0]
        self.combat.enqueue_action(self.player, item, enemy)
        self.client.pop_state()
