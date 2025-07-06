# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
import uuid
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.animation import ScheduleType
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.state import State
from tuxemon.states.monster import MonsterMenuState
from tuxemon.tools import fix_measure, open_choice_dialog, open_dialog

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


MenuGameObj = Callable[[], object]


HIDDEN = "hidden_kennel"
HIDDEN_LIST = [HIDDEN]
MAX_BOX = prepare.MAX_KENNEL


class MonsterTakeState(PygameMenuState):
    """Menu for the Monster Take state.

    Shows all tuxemon currently in a storage kennel, and selecting one puts it
    into your current party."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Monster],
    ) -> None:
        self.monster_boxes = self.char.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)

        def kennel_options(instance_id: str) -> None:
            iid = uuid.UUID(instance_id)
            mon = self.monster_boxes.get_monsters_by_iid(iid)
            if mon is None:
                logger.error(f"Monster {iid} not found")
                return

            kennels = [
                key
                for key, value in self.monster_boxes.monster_boxes.items()
                if len(value) < MAX_BOX
                and key not in HIDDEN_LIST
                and key != self.box_name
            ]

            box_ids = [
                key
                for key, value in self.monster_boxes.monster_boxes.items()
                if len(value) < MAX_BOX and key not in HIDDEN_LIST
            ]

            actions = {
                "pick": lambda: pick(mon),
                "move": lambda: move(mon, kennels),
                "release": lambda: release(mon),
            }

            menu = []
            for action, func in actions.items():
                if action == "move" and len(box_ids) < 2:
                    continue
                menu.append((action, T.translate(action).upper(), func))

            open_choice_dialog(
                self.client,
                menu=menu,
                escape_key_exits=True,
            )

        def pick(monster: Monster) -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("MonsterTakeState")
            self.monster_boxes.remove_monster(monster)
            self.char.add_monster(monster, len(self.char.monsters))
            open_dialog(
                self.client,
                [
                    T.format(
                        "menu_storage_take_monster", {"name": monster.name}
                    )
                ],
            )

        def move(monster: Monster, box_ids: list[str]) -> None:
            if len(box_ids) == 1:
                move_monster(monster, box_ids[0], box_ids)
            else:
                var_menu = []
                for box in box_ids:
                    text = T.translate(box).upper()
                    var_menu.append(
                        (
                            text,
                            text,
                            partial(move_monster, monster, box, box_ids),
                        )
                    )
                open_choice_dialog(
                    self.client,
                    menu=(var_menu),
                    escape_key_exits=True,
                )

        def release(monster: Monster) -> None:
            var_menu = []
            var_menu.append(
                ("no", T.translate("no").upper(), partial(output, None))
            )
            var_menu.append(
                ("yes", T.translate("yes").upper(), partial(output, monster))
            )
            open_choice_dialog(
                self.client,
                menu=(var_menu),
                escape_key_exits=True,
            )

        def move_monster(
            monster: Monster, box: str, box_ids: list[str]
        ) -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("ChoiceState")
            if len(box_ids) >= 2:
                self.client.remove_state_by_name("MonsterTakeState")
            self.monster_boxes.move_monster(self.box_name, box, monster)

        def output(monster: Optional[Monster]) -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("MonsterTakeState")
            if monster is not None:
                self.monster_boxes.remove_monster_from(self.box_name, monster)
                open_dialog(
                    self.client,
                    [T.format("tuxemon_released", {"name": monster.name})],
                )

        def info(mon: Monster) -> None:
            self.client.remove_state_by_name("ChoiceState")
            params = {"monster": mon, "source": self.name}
            self.client.push_state("MonsterInfoState", kwargs=params)

        def tech(mon: Monster) -> None:
            self.client.remove_state_by_name("ChoiceState")
            params = {"monster": mon, "source": self.name}
            self.client.push_state("MonsterMovesState", kwargs=params)

        def item(mon: Monster) -> None:
            self.client.remove_state_by_name("ChoiceState")
            params = {"monster": mon, "source": self.name}
            self.client.push_state("MonsterItemState", kwargs=params)

        def description(mon: Monster) -> None:
            _info = T.translate("monster_menu_info").upper()
            _tech = T.translate("monster_menu_tech").upper()
            _item = T.translate("monster_menu_item").upper()
            var_menu = []
            var_menu.append((_info, _info, partial(info, mon)))
            var_menu.append((_tech, _tech, partial(tech, mon)))
            var_menu.append((_item, _item, partial(item, mon)))
            open_choice_dialog(
                self.client,
                menu=(var_menu),
                escape_key_exits=True,
            )

        # it prints monsters inside the screen: image + button
        _sorted = sorted(items, key=lambda x: x.slug)
        for monster in _sorted:
            label = T.translate(monster.name).upper()
            iid = monster.instance_id.hex
            new_image = self._create_image(monster.sprite_handler.front_path)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            menu.add.banner(
                new_image,
                partial(kennel_options, iid),
                selection_effect=HighlightSelection(),
            )
            diff = round((monster.hp_ratio) * 100, 1)
            level = f"Lv.{monster.level}"
            menu.add.progress_bar(
                level,
                default=diff,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
            )
            menu.add.button(
                label,
                partial(description, monster),
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )

        # menu
        box_label = T.translate(self.box_name).upper()
        menu.set_title(
            T.format(f"{box_label}: {len(self.box)}/{MAX_BOX}")
        ).center_content()

    def __init__(self, box_name: str, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PC_KENNEL)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        columns = 3

        self.box_name = box_name
        self.char = character
        self.monster_boxes = self.char.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)

        # Widgets are like a pygame_menu label, image, etc.
        num_widgets = 3
        rows = math.ceil(len(self.box) / columns) * num_widgets

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        column_width = fix_measure(self.menu._width, 0.33)
        self.menu._column_max_width = [
            column_width,
            column_width,
            column_width,
        ]

        menu_items_map = []
        for monster in self.box:
            menu_items_map.append(monster)

        self.add_menu_items(self.menu, menu_items_map)
        self.reset_theme()


class MonsterBoxState(PygameMenuState):
    """Menu to choose a tuxemon box."""

    def __init__(self, character: NPC) -> None:
        _, height = prepare.SCREEN_SIZE

        super().__init__(height=height)

        self.animation_offset = 0
        self.char = character

        menu_items_map = self.get_menu_items_map()
        self.add_menu_items(self.menu, menu_items_map)

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[tuple[str, MenuGameObj]],
    ) -> None:
        menu.add.vertical_fill()
        for key, callback in items:
            player = self.char
            num_mons = player.monster_boxes.get_box_size(key, "monster")
            label = T.format(
                f"{T.translate(key).upper()}: {num_mons}/{MAX_BOX}"
            )
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

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        """
        Return a list of menu options and callbacks, to be overridden by
        class descendants.
        """
        return []

    def change_state(self, state: str, **kwargs: Any) -> partial[State]:
        return partial(self.client.replace_state, state, **kwargs)

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        """
        Animate the menu sliding in.

        Returns:
            Sliding in animation.

        """

        width = self.menu.get_width(border=True)
        self.animation_offset = 0

        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)

        return ani

    def animate_close(self) -> Animation:
        """
        Animate the menu sliding out.

        Returns:
            Sliding out animation.

        """
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)

        return ani


class MonsterStorageState(MonsterBoxState):
    """Menu to choose a box, which you can then take a tuxemon from."""

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        menu_items_map = []
        monster_boxes = self.char.monster_boxes
        for box_name, monsters in monster_boxes.monster_boxes.items():
            if box_name not in HIDDEN_LIST:
                if not monsters:
                    menu_callback = partial(
                        open_dialog,
                        self.client,
                        [T.translate("menu_storage_empty_kennel")],
                    )
                else:
                    menu_callback = self.change_state(
                        "MonsterTakeState",
                        box_name=box_name,
                        character=self.char,
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOffState(MonsterBoxState):
    """Menu to choose a box, which you can then drop off a tuxemon into."""

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        menu_items_map = []
        monster_boxes = self.char.monster_boxes
        for box_name, monsters in monster_boxes.monster_boxes.items():
            if box_name not in HIDDEN_LIST:
                if len(monsters) < MAX_BOX:
                    menu_callback = self.change_state(
                        "MonsterDropOff",
                        box_name=box_name,
                        character=self.char,
                    )
                else:
                    menu_callback = partial(
                        open_dialog,
                        self.client,
                        [T.translate("menu_storage_full_kennel")],
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOff(MonsterMenuState):
    """Shows all Tuxemon in player's party, puts it into box if selected."""

    def __init__(self, box_name: str, character: NPC) -> None:
        super().__init__(character=character)

        self.box_name = box_name
        self.char = character

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        alive_monsters = [
            mon for mon in self.char.monsters if not mon.is_fainted
        ]
        if monster is not None:
            return len(alive_monsters) != 1 or monster not in alive_monsters
        return True

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
    ) -> None:
        monster = menu_item.game_object
        assert monster
        if monster.plague.is_infected():
            open_dialog(
                self.client,
                [T.translate("menu_storage_infected_monster")],
            )
        else:
            self.char.monster_boxes.add_monster(self.box_name, monster)
            self.char.remove_monster(monster)
            self.client.pop_state(self)
