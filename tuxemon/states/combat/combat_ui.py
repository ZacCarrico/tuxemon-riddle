# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, MutableMapping, Sequence
from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING, Optional, Union

from pygame.rect import Rect

from tuxemon import prepare, tools
from tuxemon.animation import Animation
from tuxemon.menu.interface import ExpBar, HpBar
from tuxemon.sprite import Sprite
from tuxemon.state import State

if TYPE_CHECKING:
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


class CombatUI:
    """
    A class responsible for drawing the combat UI, including HP and EXP bars.
    """

    def __init__(self) -> None:
        self._hp_bars: MutableMapping[Monster, HpBar] = {}
        self._exp_bars: MutableMapping[Monster, ExpBar] = {}

    def draw_hp_bars(
        self,
        graphics: BattleGraphicsModel,
        hud: MutableMapping[Monster, Sprite],
    ) -> None:
        """
        Redraws the HP bars for each monster in the hud dictionary.

        Parameters:
            graphics: The graphics model for the battle.
            hud: A dictionary of monsters to sprites.
        """
        show_player_hp = graphics.hud.hp_bar_player
        show_opponent_hp = graphics.hud.hp_bar_opponent

        for monster, _sprite in hud.items():
            if _sprite.player and show_player_hp:
                rect = self.create_rect_for_bar(_sprite, 70, 8, 18)
            elif not _sprite.player and show_opponent_hp:
                rect = self.create_rect_for_bar(_sprite, 70, 8, 12)
            else:
                continue
            self._hp_bars[monster].draw(_sprite.image, rect)

    def draw_exp_bars(
        self,
        graphics: BattleGraphicsModel,
        hud: MutableMapping[Monster, Sprite],
    ) -> None:
        """
        Redraws the EXP bars for each player monster in the hud dictionary.

        Parameters:
            graphics: The graphics model for the battle.
            hud: A dictionary of monsters to sprites.
        """
        show_player_exp = graphics.hud.exp_bar_player

        for monster, _sprite in hud.items():
            if _sprite.player and show_player_exp:
                rect = self.create_rect_for_bar(_sprite, 70, 6, 31)
                self._exp_bars[monster].draw(_sprite.image, rect)

    def create_rect_for_bar(
        self, hud: Sprite, width: int, height: int, top_offset: int = 0
    ) -> Rect:
        """
        Creates a Rect object for a bar.

        Parameters:
            hud: The sprite for the monster.
            width: The width of the bar.
            height: The height of the bar.
            top_offset: The top offset of the bar. Defaults to 0.

        Returns:
            A Rect object representing the bar.
        """
        rect = Rect(0, 0, tools.scale(width), tools.scale(height))
        rect.right = hud.image.get_width() - tools.scale(8)
        rect.top += tools.scale(top_offset)
        return rect

    def draw_all_ui(
        self,
        graphics: BattleGraphicsModel,
        hud: MutableMapping[Monster, Sprite],
    ) -> None:
        """
        Redraws all the UI elements, including HP and EXP bars.

        Parameters:
            graphics: The graphics model for the battle.
            hud: A dictionary of monsters to sprites.
        """
        self.draw_hp_bars(graphics, hud)
        self.draw_exp_bars(graphics, hud)


class FieldMonsters:
    def __init__(self) -> None:
        self.monsters_in_play: defaultdict[NPC, list[Monster]] = defaultdict(
            list
        )

    @property
    def active_monsters(self) -> Sequence[Monster]:
        """List of all non-defeated monsters on the battlefield."""
        return list(chain.from_iterable(self.monsters_in_play.values()))

    def add_monster(self, npc: NPC, monster: Monster) -> None:
        """Adds a monster to the given NPC's active roster."""
        self.monsters_in_play[npc].append(monster)

    def remove_monster(self, npc: NPC, monster: Monster) -> None:
        """Removes a specific monster from the given NPC's roster if present."""
        if monster in self.monsters_in_play[npc]:
            self.monsters_in_play[npc].remove(monster)

    def remove_npc(self, npc: NPC) -> None:
        """Removes all monsters associated with the given NPC."""
        if npc in self.monsters_in_play:
            del self.monsters_in_play[npc]

    def get_monsters(self, npc: NPC) -> list[Monster]:
        """Returns the list of active monsters for the given NPC."""
        return self.monsters_in_play.get(npc, [])

    def get_all_monsters(self) -> dict[NPC, list[Monster]]:
        """Returns a dictionary containing all NPCs and their active monsters."""
        return self.monsters_in_play


class HudManager:
    """
    Handles positioning and sprite assignment for HUD elements tied to monsters
    during battle.

    This class provides a visual mapping between each NPC and their assigned
    monster HUD components. It allows retrieval of screen rectangles for rendering
    UI elements, and handles lifecycle management of associated HUD sprites
    (e.g., health bars, names, status).

    The layout is decoupled from any battle logic and defined per NPC via a
    dictionary of position keys mapped to lists of Rects. This makes the system
    flexible and reusable across single and double battles with different formations.
    """

    def __init__(self, layout: dict[NPC, dict[str, list[Rect]]]) -> None:
        """Manages HUD positions and mappings for NPCs in combat."""
        self.layout = layout
        self.hud_map: MutableMapping[Monster, Sprite] = defaultdict(Sprite)

    def assign_hud(self, monster: Monster, hud_sprite: Sprite) -> None:
        """Assigns a HUD sprite to a monster."""
        self.hud_map[monster] = hud_sprite

    def delete_hud(self, monster: Monster) -> None:
        """Removes the HUD sprite associated with a monster, if it exists."""
        if monster in self.hud_map:
            self.hud_map[monster].kill()
            del self.hud_map[monster]

    def get_rect(self, npc: NPC, position_key: str) -> Rect:
        """Retrieves the Rect object for a given NPC and position key."""
        if npc not in self.layout:
            raise KeyError(f"NPC {npc.name} not found in layout.")

        rect_list = self.layout[npc].get(position_key)

        if not rect_list:
            raise ValueError(
                f"No Rect found for position key '{position_key}' in NPC {npc.name}."
            )

        return rect_list[0]

    def get_hud(self, monster: Monster) -> Optional[Sprite]:
        """
        Retrieves the HUD sprite for a given monster if it exists.
        """
        return self.hud_map.get(monster)


class Side(Enum):
    PLAYER = "player"
    OPPONENT = "opponent"


class BattleFieldLayout:
    """
    Represents the battlefield layout by tracking which monsters appear on
    each side and in which slot.

    This class assigns each monster a tuple of (Side, index), allowing the
    battle system to query position and orientation for rendering or logic
    purposes.
    """

    def __init__(
        self,
        monsters_left: Sequence[Monster],
        monsters_right: Sequence[Monster],
    ):
        self.monster_positions: dict[Monster, tuple[Side, int]] = {}

        for i, monster in enumerate(monsters_left):
            self.monster_positions[monster] = (Side.OPPONENT, i)
        for i, monster in enumerate(monsters_right):
            self.monster_positions[monster] = (Side.PLAYER, i)

    def get_side(self, monster: Monster) -> Side:
        """Returns the side (PLAYER or OPPONENT) that the given monster belongs to."""
        return self.monster_positions[monster][0]

    def get_index(self, monster: Monster) -> int:
        """Returns the slot index for the given monster on its side."""
        return self.monster_positions[monster][1]

    def is_single_battle(self) -> bool:
        """Determines whether the current layout represents a single battle (1v1)."""
        return (
            sum(
                1
                for side, _ in self.monster_positions.values()
                if side == Side.PLAYER
            )
            == 1
            and sum(
                1
                for side, _ in self.monster_positions.values()
                if side == Side.OPPONENT
            )
            == 1
        )


class FieldPositionTracker:
    """
    Tracks field slot assignments for monsters during battle.

    This class maintains a mapping between each (NPC, Monster) pair
    and their assigned field slot (e.g. 'home', 'home0', 'home1').
    It's useful for determining positioning during animations or swaps,
    especially in double battles where multiple slots are active.
    """

    def __init__(self) -> None:
        self._positions: dict[tuple[NPC, Monster], str] = {}

    def assign(
        self, npc: NPC, monster: Monster, slot_index: int, is_double: bool
    ) -> None:
        """Assigns a monster to a specific field slot key."""
        key = f"home{slot_index}" if is_double else "home"
        self._positions[(npc, monster)] = key

    def unassign(self, npc: NPC, monster: Monster) -> None:
        """Removes the field slot assignment of a monster."""
        self._positions.pop((npc, monster), None)

    def get_key(self, npc: NPC, monster: Monster) -> str:
        return self._positions.get((npc, monster), "home")

    def get_open_slot(self, npc: NPC) -> int:
        """Returns the lowest unused slot index for this NPC (0 or 1)."""
        used_slots = {
            int(pos[-1])
            for (n, _), pos in self._positions.items()
            if n == npc and pos.startswith("home") and pos[-1].isdigit()
        }
        return 0 if 0 not in used_slots else 1 if 1 not in used_slots else 0


class StatusIconManager:
    """Handles creation, caching, and updating of status icons."""

    def __init__(self, state: State, layer: int = 200) -> None:
        self._layout: Optional[BattleFieldLayout] = None
        self.state = state
        self.layer = layer
        self._status_icon_cache: dict[
            tuple[str, tuple[float, float]], Sprite
        ] = {}
        self._status_icons: dict[Monster, list[Sprite]] = {}

    def determine_icon_position(
        self,
        monster: Monster,
        monsters_left: Sequence[Monster],
        monsters_right: Sequence[Monster],
    ) -> tuple[float, float]:
        """Determine the position of the icon based on the monster's status."""
        layout = BattleFieldLayout(monsters_left, monsters_right)
        is_single = layout.is_single_battle()
        is_opponent = layout.get_side(monster) == Side.OPPONENT
        index = layout.get_index(monster)
        return self.get_icon_position(is_opponent, index, is_single)

    def create_icon_cache(self, active_monsters: Sequence[Monster]) -> None:
        """Create and fill the icon cache and status icons dictionaries."""
        if not self._layout:
            raise ValueError(
                "Layout must be initialized before creating icons."
            )
        is_single = self._layout.is_single_battle()

        self._status_icons.clear()
        for monster in active_monsters:
            self._status_icons[monster] = []
            is_opponent = self._layout.get_side(monster) == Side.OPPONENT
            index = self._layout.get_index(monster)
            for status in monster.status.get_statuses():
                if status.icon:
                    icon_position = self.get_icon_position(
                        is_opponent, index, is_single
                    )
                    cache_key = (status.icon, icon_position)
                    if cache_key not in self._status_icon_cache:
                        self._status_icon_cache[cache_key] = (
                            self.state.load_sprite(
                                status.icon,
                                layer=self.layer,
                                center=icon_position,
                            )
                        )
                    self._status_icons[monster].append(
                        self._status_icon_cache[cache_key]
                    )

    def update_icons_for_monsters(
        self,
        active_monsters: Sequence[Monster],
        monsters_left: Sequence[Monster],
        monsters_right: Sequence[Monster],
    ) -> None:
        """Reset status icons for monsters."""
        self._layout = BattleFieldLayout(monsters_left, monsters_right)
        self.state.sprites.remove(
            *[icon for icons in self._status_icons.values() for icon in icons]
        )
        self.create_icon_cache(active_monsters)
        self.add_all_icons()

    def add_all_icons(self) -> None:
        """Add all status icons to the sprite layer."""
        for icons in self._status_icons.values():
            for icon in icons:
                self.add_icon(icon)

    def add_icon(self, icon: Sprite) -> None:
        """Add a status icon to the sprite layer."""
        if icon.image.get_alpha() == 0:
            icon.image.set_alpha(255)
        self.state.sprites.add(icon, layer=self.layer)

    def remove_monster_icons(self, monster: Monster) -> None:
        """Remove all icons associated with a specific monster."""
        if monster in self._status_icons:
            for icon in self._status_icons[monster]:
                icon.kill()
            del self._status_icons[monster]

    def get_icons_for_monster(self, monster: Monster) -> list[Sprite]:
        """Retrieve the list of icons for a specific monster."""
        return self._status_icons.get(monster, [])

    def animate_icons(
        self, monster: Monster, animate_func: Callable[..., Animation]
    ) -> None:
        for icon in self.get_icons_for_monster(monster):
            if icon.image.get_alpha() == 255:
                animate_func(icon.image, initial=255, set_alpha=0, duration=2)
            elif icon.image.get_alpha() == 0:
                animate_func(icon.image, initial=0, set_alpha=255, duration=2)
            else:
                icon.image.set_alpha(255)

    def get_icon_position(
        self, is_opponent: bool, index: int, single_battle: bool
    ) -> tuple[float, float]:
        if single_battle:
            return {
                (True, 0): prepare.ICON_OPPONENT_DEFAULT,
                (True, 1): prepare.ICON_OPPONENT_SLOT,
                (False, 0): prepare.ICON_PLAYER_DEFAULT,
                (False, 1): prepare.ICON_PLAYER_SLOT,
            }[(is_opponent, index)]
        else:
            return {
                (True, 0): prepare.ICON_OPPONENT_DEFAULT,
                (True, 1): prepare.ICON_OPPONENT_SLOT,
                (False, 1): prepare.ICON_PLAYER_DEFAULT,
                (False, 0): prepare.ICON_PLAYER_SLOT,
            }[(is_opponent, index)]

    def recalculate_icon_positions(self) -> None:
        if not self._layout:
            raise ValueError(
                "Layout must be initialized before recalculating positions."
            )
        is_single = self._layout.is_single_battle()

        for monster, icons in self._status_icons.items():
            is_opponent = self._layout.get_side(monster) == Side.OPPONENT
            index = self._layout.get_index(monster)
            icon_position = self.get_icon_position(
                is_opponent, index, is_single
            )
            for icon in icons:
                icon.rect.center = icon_position


class MonsterSpriteMap:
    def __init__(self) -> None:
        self.sprite_map: MutableMapping[Union[NPC, Monster], Sprite] = {}

    def get_sprite(self, entity: Union[NPC, Monster]) -> Optional[Sprite]:
        """Retrieves the sprite for the given entity, raising an error if not found."""
        if entity not in self.sprite_map:
            return None
        return self.sprite_map[entity]

    def add_sprite(self, entity: Union[NPC, Monster], sprite: Sprite) -> None:
        """Associates a sprite with the given entity."""
        self.sprite_map[entity] = sprite

    def remove_sprite(self, entity: Union[NPC, Monster]) -> None:
        """Removes and cleans up the sprite associated with the given entity."""
        if entity in self.sprite_map:
            self.sprite_map[entity].kill()
            del self.sprite_map[entity]

    def update_sprite_position(
        self, entity: Union[NPC, Monster], new_feet: tuple[int, int]
    ) -> None:
        """Updates the position of the given entity's sprite to match the new feet position."""
        if entity not in self.sprite_map:
            raise KeyError(
                f"Cannot update position: No sprite found for entity {entity.name}"
            )
        self.sprite_map[entity].rect.midbottom = new_feet
