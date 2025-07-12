# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
There are quite a few hacks in here to get this working for single player only
notably, the use of self.game
"""

from __future__ import annotations

import logging
from abc import ABC
from functools import partial
from typing import TYPE_CHECKING, Optional, Union

from pygame.rect import Rect
from pygame.transform import flip as pg_flip

from tuxemon import graphics, prepare
from tuxemon.combat import alive_party, build_hud_text
from tuxemon.formula import config_combat
from tuxemon.locale import T
from tuxemon.menu.menu import Menu
from tuxemon.sprite import CaptureDeviceSprite, Sprite
from tuxemon.tools import scale
from tuxemon.ui.combat_bars import CombatBars
from tuxemon.ui.combat_hud import CombatLayoutManager
from tuxemon.ui.combat_layout import (
    LayoutManager,
    layout_groups,
    prepare_layout,
    scaled_layouts,
)
from tuxemon.ui.combat_monsters import FieldMonsters, MonsterSpriteMap
from tuxemon.ui.combat_status import StatusIconManager
from tuxemon.ui.combat_zone import CombatZone
from tuxemon.ui.text import HorizontalAlignment

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

    from .combat_context import CombatContext

logger = logging.getLogger(__name__)

sprite_layer = 0
hud_layer = 100


def toggle_visible(sprite: Sprite) -> None:
    sprite.toggle_visible()


class CombatAnimations(Menu[None], ABC):
    """
    Collection of combat animations.

    Mixin-ish thing until things are sorted out.
    Mostly just a collections of methods to animate the sprites

    These methods should not, without [many] exception[s], manipulate
    game/combat state.  These should just move sprites around
    the screen, with the occasional creation/removal of sprites....
    but never game objects.
    """

    def __init__(self, context: CombatContext) -> None:
        super().__init__()
        self.session = context.session
        self.players = context.teams
        self.graphics = context.graphics
        self.is_double = context.battle_mode == "double"
        self.field_monsters = FieldMonsters()
        self.sprite_map = MonsterSpriteMap()
        self.is_trainer_battle = False
        self.capdevs: list[CaptureDeviceSprite] = []
        self.bars = CombatBars(self.graphics)
        layout_manager = LayoutManager(scaled_layouts, layout_groups)
        _layout = prepare_layout(self.players, layout_manager)
        self.hud_manager = CombatLayoutManager(_layout)
        self.status_icons = StatusIconManager(self, _layout, self.hud_manager)
        self.combat_zone = CombatZone(prepare.SCREEN_RECT)

    def animate_open(self) -> None:
        self.transition_none_normal()

    def transition_none_normal(self) -> None:
        """From newly opened to normal."""
        self.animate_parties_in()

        for player, layout in self.hud_manager.layout.items():
            self.animate_party_hud_in(player, layout["party"][0])

        for player in self.players[: 2 if self.is_trainer_battle else 1]:
            self.task(partial(self.animate_trainer_leave, player), interval=3)

    def blink(self, sprite: Sprite) -> None:
        self.task(partial(toggle_visible, sprite), interval=0.20, times=8)

    def animate_trainer_leave(self, trainer: Union[NPC, Monster]) -> None:
        """Animate the trainer leaving the screen."""
        sprite = self.sprite_map.get_sprite(trainer)
        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {trainer.name}")

        x_offset = self.combat_zone.get_horizontal_offset(
            sprite.rect, scale(-150)
        )
        self.animate(sprite.rect, x=x_offset, relative=True, duration=0.8)

    def animate_monster_release(
        self,
        npc: NPC,
        monster: Monster,
        sprite: Sprite,
    ) -> None:
        """
        Animates the release of a monster from a capture device.

        This function coordinates the animation of the capture device falling, the
        monster sprite moving into position, and the capture device opening animation.
        It also plays the combat call sound.
        """
        self.hud_manager.assign(npc, monster, self.is_double)
        feet = self.hud_manager.get_feet_position(npc, monster)

        # Load and scale capture device sprite
        capdev = self.load_sprite(f"gfx/items/{monster.capture_device}.png")
        graphics.scale_sprite(capdev, 0.4)
        capdev.rect.center = (feet[0], feet[1] - scale(60))

        # Animate capture device falling
        fall_time = 0.7
        animate_fall = partial(
            self.animate,
            duration=fall_time,
            transition="out_quad",
        )
        animate_fall(capdev.rect, bottom=feet[1], transition="in_back")
        animate_fall(capdev, rotation=720, initial=0)

        # Animate capture device fading away
        delay = fall_time + 0.6
        fade_duration = 0.9
        h = capdev.rect.height
        animate_fade = partial(
            self.animate, duration=fade_duration, delay=delay
        )
        animate_fade(capdev, width=1, height=h * 1.5)
        animate_fade(capdev.rect, y=-scale(14), relative=True)

        # Convert capture device sprite for easy fading
        def convert_sprite() -> None:
            capdev.image = graphics.convert_alpha_to_colorkey(capdev.image)
            self.animate(
                capdev.image,
                set_alpha=0,
                initial=255,
                duration=fade_duration,
            )

        self.task(convert_sprite, interval=delay)
        self.task(capdev.kill, interval=fall_time + delay + fade_duration)

        # Load monster sprite and set final position
        monster_sprite = monster.get_sprite(
            "back" if npc == self.players[0] else "front"
        )
        monster_sprite.rect.midbottom = feet
        self.sprites.add(monster_sprite)
        self.sprite_map.add_sprite(monster, monster_sprite)

        # Position monster sprite off screen and animate it to final spot
        monster_sprite.rect.top = self.client.screen.get_height()
        self.animate(
            monster_sprite.rect,
            bottom=feet[1],
            transition="out_quad",
            duration=0.9,
            delay=fall_time + 0.5,
        )

        # Play capture device opening animation
        assert sprite.animation
        sprite.rect.midbottom = feet
        self.task(sprite.animation.play, interval=1.3)
        self.task(partial(self.sprites.add, sprite), interval=1.3)

        # Load and play combat call sound
        self.play_sound_effect(monster.combat_call, 1.3)

    def animate_sprite_spin(self, sprite: Sprite) -> None:
        self.animate(
            sprite,
            rotation=360,
            initial=0,
            duration=0.8,
            transition="in_out_quint",
        )

    def animate_sprite_tackle(self, sprite: Sprite) -> None:
        duration = 0.3
        original_x = sprite.rect.x
        delta = 0

        _, horizontal = self.combat_zone.get_zone(sprite.rect)

        if horizontal is HorizontalAlignment.LEFT:
            delta = scale(14)
        elif horizontal is HorizontalAlignment.RIGHT:
            delta = -scale(14)

        self.animate(
            sprite.rect,
            x=original_x + delta,
            duration=duration,
            transition="out_circ",
        )
        self.animate(
            sprite.rect,
            x=original_x,
            duration=duration,
            transition="in_out_circ",
            delay=0.35,
        )

    def animate_monster_faint(self, monster: Monster) -> None:
        """Animate a monster fainting and remove it."""

        def kill_monster() -> None:
            """Remove the monster's sprite and HUD elements."""
            self.sprite_map.remove_sprite(monster)
            self.status_icons.remove_monster_icons(monster)
            self.hud_manager.delete_hud(monster)

        self.animate_monster_leave(monster)
        self.task(kill_monster, interval=2)

        for monsters in self.field_monsters.get_all_monsters().values():
            if monster in monsters:
                monsters.remove(monster)

        # Update the party HUD to reflect the fainted tuxemon
        self.animate_update_party_hud()

    def animate_sprite_take_damage(self, sprite: Sprite) -> None:
        original_x, original_y = sprite.rect.topleft
        animate = partial(
            self.animate,
            sprite.rect,
            duration=1,
            transition="in_out_elastic",
        )
        ani = animate(x=original_x, initial=original_x + scale(400))
        # just want the end of the animation, not the entire thing
        ani._elapsed = 0.735
        ani = animate(y=original_y, initial=original_y - scale(400))
        # just want the end of the animation, not the entire thing
        ani._elapsed = 0.735

    def animate_hp(self, monster: Monster) -> None:
        hp_bar = self.bars.get_hp_bar(monster)
        self.animate(
            hp_bar,
            value=monster.hp_ratio,
            duration=0.7,
            transition="out_quint",
        )

    def animate_exp(self, monster: Monster) -> None:
        target_previous = monster.experience_required()
        target_next = monster.experience_required(1)
        diff_value = monster.total_experience - target_previous
        diff_target = target_next - target_previous
        value = max(0, min(1, (diff_value) / (diff_target)))
        if monster.levelling_up:
            value = 1.0
        exp_bar = self.bars.get_exp_bar(monster)
        self.animate(
            exp_bar,
            value=value,
            duration=0.7,
            transition="out_quint",
        )

    def animate_monster_leave(self, monster: Monster) -> None:
        sprite = self.sprite_map.get_sprite(monster)
        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")

        x_offset = self.combat_zone.get_horizontal_offset(
            sprite.rect, scale(-150)
        )

        cry = (
            monster.combat_call
            if monster.current_hp > 0
            else monster.faint_call
        )
        self.play_sound_effect(cry)
        self.animate(sprite.rect, x=x_offset, relative=True, duration=2)
        self.status_icons.animate_icons(monster, self.animate)

    def check_hud(self, monster: Monster, filename: str) -> Sprite:
        """
        Checks whether exists or not a hud, it returns a sprite.
        To avoid building over an existing one.

        Parameters:
            monster: Monster who needs to update the hud.
            filename: Filename of the hud.
        """
        sprite = self.hud_manager.get_hud(monster)
        if sprite is None:
            sprite = self.load_sprite(filename, layer=hud_layer)

        return sprite

    def split_label(self, owner: NPC, hud: Sprite, label: str) -> None:
        """
        Automatically draws label lines on the HUD using layout based
        on NPC ownership.
        """
        hud_line1 = self.hud_manager.get_rect(owner, "hud_line1")
        hud_line2 = self.hud_manager.get_rect(owner, "hud_line2")

        labels = label.splitlines()
        if len(labels) > 1:
            hud.image.blit(self.shadow_text(labels[0]), hud_line1)
            hud.image.blit(self.shadow_text(labels[1]), hud_line2)
        else:
            hud.image.blit(self.shadow_text(labels[0]), hud_line1)

    def build_hud(
        self, monster: Monster, hud_position: str, animate: bool = True
    ) -> None:
        """
        Builds the HUD for a monster.

        Parameters:
            monster: The monster that needs to update the HUD.
            hud_position: The part of the layout where the HUD will be
                displayed (e.g. "hud0", etc.).
            animate: Whether the HUD should be animated (slide in) or not.
        """
        trainer_battle = self.is_trainer_battle
        menu = self.graphics.menu
        owner = monster.get_owner()
        hud_rect = self.hud_manager.get_rect(owner, hud_position)

        def build_hud_sprite(hud: Sprite, is_player: bool) -> Sprite:
            """
            Builds a HUD sprite for a monster.

            Parameters:
                hud: The HUD sprite to build.
                is_player: Whether the HUD is for the player or not.

            Returns:
                The built HUD sprite.
            """
            symbol = False
            if not is_player and self.players[0].tuxepedia.is_caught(
                monster.slug
            ):
                symbol = True
            label = build_hud_text(
                menu, monster, is_player, trainer_battle, symbol
            )
            self.split_label(owner, hud, label)
            if is_player:
                hud.rect.bottomleft = hud_rect.right, hud_rect.bottom
                hud.player = True
                if animate:
                    animate_func(hud.rect, left=hud_rect.left)
                else:
                    hud.rect.left = hud_rect.left
            else:
                hud.rect.bottomright = 0, hud_rect.bottom
                hud.player = False
                if animate:
                    animate_func(hud.rect, right=hud_rect.right)
                else:
                    hud.rect.right = hud_rect.right
            return hud

        if animate:
            animate_func = partial(self.animate, duration=2.0, delay=1.3)

        _, h_align = self.combat_zone.get_zone(hud_rect)

        if h_align is HorizontalAlignment.RIGHT:
            hud_graphics = self.graphics.hud.hud_player
            flipped = True
        else:
            hud_graphics = self.graphics.hud.hud_opponent
            flipped = False

        hud = build_hud_sprite(self.check_hud(monster, hud_graphics), flipped)

        self.hud_manager.assign_hud(monster, hud)

        if animate:
            self.animate_hp(monster)
            if hud.player:
                self.animate_exp(monster)

    def _load_sprite(
        self, sprite_type: str, position: dict[str, int]
    ) -> Sprite:
        return self.load_sprite(sprite_type, **position)

    def animate_party_hud_left(
        self, home: Rect
    ) -> tuple[Optional[Sprite], int, int]:
        if self.is_trainer_battle and not self.is_double:
            tray = self._load_sprite(
                self.graphics.hud.tray_opponent,
                {"bottom": home.bottom, "right": 0, "layer": hud_layer},
            )
            self.animate(tray.rect, right=home.right, duration=2, delay=1.5)
        else:
            tray = None
        centerx = home.right - scale(13)
        offset = scale(8)
        return tray, centerx, offset

    def animate_party_hud_right(self, home: Rect) -> tuple[Sprite, int, int]:
        tray = self._load_sprite(
            self.graphics.hud.tray_player,
            {"bottom": home.bottom, "left": home.right, "layer": hud_layer},
        )
        self.animate(tray.rect, left=home.left, duration=2, delay=1.5)
        centerx = home.left + scale(13)
        offset = -scale(8)
        return tray, centerx, offset

    def animate_party_hud_in(self, player: NPC, home: Rect) -> None:
        """
        Animates the party HUD (the arrow thing with balls).

        Parameters:
            player: The player whose HUD is being animated.
            home: Location and size of the HUD.
        """
        _, h_align = self.combat_zone.get_zone(home)

        if h_align is HorizontalAlignment.LEFT:
            tray, centerx, offset = self.animate_party_hud_left(home)
        else:
            tray, centerx, offset = self.animate_party_hud_right(home)

        if tray is None or any(t.wild for t in player.monsters):
            return

        monster_count = player.party.party_size
        positions = (
            [monster_count - i - 1 for i in range(prepare.PARTY_LIMIT)]
            if h_align is HorizontalAlignment.LEFT
            else list(range(prepare.PARTY_LIMIT))
        )

        scaled_top = scale(1)

        for index, pos in enumerate(positions):
            monster = player.monsters[index] if index < monster_count else None
            centerx_pos = centerx - (pos if monster else index) * offset

            sprite = self._load_sprite(
                self.graphics.icons.icon_empty,
                {
                    "top": tray.rect.top + scaled_top,
                    "centerx": centerx_pos,
                    "layer": hud_layer,
                },
            )

            capdev = CaptureDeviceSprite(
                sprite=sprite,
                tray=tray,
                monster=monster,
                icon=self.graphics.icons,
            )
            self.capdevs.append(capdev)
            animate = partial(
                self.animate, duration=1.5, delay=2.2 + index * 0.2
            )
            capdev.animate_capture(animate)

    def animate_update_party_hud(self) -> None:
        """
        Update the balls in the party HUD to reflect fainted Tuxemon.

        Note:
            Party HUD is the arrow thing with balls.  Yes, that one.
        """
        for dev in self.capdevs:
            prev = dev.state
            if prev != dev.update_state():
                animate = partial(self.animate, duration=0.1, delay=0.1)
                dev.animate_capture(animate)

    def animate_parties_in(self) -> None:
        """Animate the parties entering the battle scene."""
        x, y, w, h = prepare.SCREEN_RECT

        # Load background image
        self.update_background(self.graphics.background)

        # Get player and opponent
        player, opponent = self.players
        opp_mon = opponent.monsters[0]
        player_home = self.hud_manager.get_rect(player, "home")
        opp_home = self.hud_manager.get_rect(opponent, "home")

        # Define animation constants
        y_mod = scale(50)

        # Load island backgrounds
        back_island = self.load_sprite(
            self.graphics.island_back,
            bottom=opp_home.bottom + y_mod,
            right=0,
        )
        front_island = self.load_sprite(
            self.graphics.island_front,
            bottom=player_home.bottom - y_mod,
            left=w,
        )

        # Load and animate opponent
        if self.is_trainer_battle:
            combat_front = opponent.template.combat_front
            enemy = self.load_sprite(
                f"gfx/sprites/player/{combat_front}.png",
                bottom=back_island.rect.bottom - scale(12),
                centerx=back_island.rect.centerx,
            )
            self.sprite_map.add_sprite(opponent, enemy)
        else:
            enemy = opp_mon.get_sprite("front")
            enemy.rect.bottom = back_island.rect.bottom - scale(24)
            enemy.rect.centerx = back_island.rect.centerx
            self.sprite_map.add_sprite(opp_mon, enemy)
            self.field_monsters.add_monster(opponent, opp_mon)
            self.update_hud(opponent, True, True)

        self.sprites.add(enemy)

        # Load and animate player
        combat_back = player.template.combat_front
        filename = f"gfx/sprites/player/{combat_back}_back.png"
        try:
            player_back = self.load_sprite(
                filename,
                bottom=front_island.rect.centery + scale(6),
                centerx=front_island.rect.centerx,
            )
        except:
            logger.warning(f"(File) {filename} cannot be found.")
            player_back = self.load_sprite(
                f"gfx/sprites/player/{combat_back}.png",
                bottom=front_island.rect.centery + scale(6),
                centerx=front_island.rect.centerx,
            )

        self.sprite_map.add_sprite(player, player_back)
        self.flip_sprites(enemy, player_back)
        self.animate_sprites(enemy, back_island, front_island, player_back)
        if not self.is_trainer_battle:
            sound = self.players[1].monsters[0].combat_call
            self.play_sound_effect(sound, 1.5)
        self.display_alert_message()

    def flip_sprites(self, enemy: Sprite, player_back: Sprite) -> None:
        """Flip the sprites horizontally."""

        def flip() -> None:
            enemy.image = pg_flip(enemy.image, True, False)
            player_back.image = pg_flip(player_back.image, True, False)

        flip()
        self.task(flip, interval=1.5)

    def animate_sprites(
        self,
        enemy: Sprite,
        back_island: Sprite,
        front_island: Sprite,
        player_back: Sprite,
    ) -> None:
        """Animate the sprites."""
        y_mod = scale(50)
        duration = 3
        animate = partial(
            self.animate, transition="out_quad", duration=duration
        )
        position1 = self.hud_manager.get_rect(self.players[1], "home")
        animate(
            enemy.rect,
            back_island.rect,
            centerx=position1.centerx,
        )
        animate(
            enemy.rect,
            back_island.rect,
            y=-y_mod,
            transition="out_back",
            relative=True,
        )
        position2 = self.hud_manager.get_rect(self.players[0], "home")
        animate(
            player_back.rect,
            front_island.rect,
            centerx=position2.centerx,
        )
        animate(
            player_back.rect,
            front_island.rect,
            y=y_mod,
            transition="out_back",
            relative=True,
        )

    def play_sound_effect(
        self, sound: str, value: float = prepare.CONFIG.sound_volume
    ) -> None:
        """Play the sound effect."""
        self.client.sound_manager.play_sound(sound, value)

    def display_alert_message(self) -> None:
        """Display the alert message."""
        if self.is_trainer_battle:
            params = {"name": self.players[1].name.upper()}
            self.alert(T.format("combat_trainer_appeared", params))
        else:
            params = {"name": self.players[1].monsters[0].name.upper()}
            self.alert(T.format("combat_wild_appeared", params))

    def animate_throwing(
        self,
        monster: Monster,
        item: Item,
    ) -> Sprite:
        """
        Animation for throwing the item.

        Parameters:
            monster: The monster being targeted.
            item: The item thrown at the monster.

        Returns:
            The animated item sprite.
        """
        monster_sprite = self.sprite_map.get_sprite(monster)
        if monster_sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")
        sprite = self.load_sprite(item.sprite)
        animate = partial(
            self.animate, sprite.rect, transition="in_quad", duration=1.0
        )
        graphics.scale_sprite(sprite, 0.4)
        sprite.rect.center = scale(0), scale(0)
        animate(x=monster_sprite.rect.centerx)
        animate(y=monster_sprite.rect.centery)
        return sprite

    def animate_capture_monster(
        self,
        is_captured: bool,
        num_shakes: int,
        monster: Monster,
        item: Item,
        sprite: Sprite,
    ) -> None:
        """
        Animation for capturing monsters.

        Parameters:
            is_captured: Whether the monster will be successfully captured.
            num_shakes: The number of times the capture device will shake.
            monster: The monster being captured.
            item: The capture device used to capture the monster.
            sprite: The sprite to animate.
        """
        monster_sprite = self.sprite_map.get_sprite(monster)
        if monster_sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")
        capdev = self.animate_throwing(monster, item)
        animate = partial(
            self.animate, capdev.rect, transition="in_quad", duration=1.0
        )
        self.task(partial(toggle_visible, monster_sprite), interval=1.0)

        # TODO: cache this sprite from the first time it's used.
        assert sprite.animation
        self.task(sprite.animation.play, interval=1.0)
        self.task(partial(self.sprites.add, sprite), interval=1.0)
        sprite.rect.midbottom = monster_sprite.rect.midbottom

        def kill_monster() -> None:
            self.sprite_map.remove_sprite(monster)
            self.hud_manager.delete_hud(monster)

        def shake_ball(initial_delay: float) -> None:
            # Define reusable shake animation functions
            def shake_up() -> Animation:
                return animate(
                    capdev.rect, y=scale(3), relative=True, duration=0.1
                )

            def shake_down() -> Animation:
                return animate(
                    capdev.rect, y=-scale(6), relative=True, duration=0.2
                )

            self.chain_animations(
                shake_up, shake_down, shake_up, start_delay=initial_delay
            )

        # Perform shakes with delays
        for i in range(num_shakes):
            shake_ball(1.8 + i * 1.0)

        if is_captured and monster.owner:
            combat = item.get_combat_state()
            trainer = monster.get_owner()
            combat._captured_mon = monster

            def show_success(delay: float) -> None:
                self.task(combat.end_combat, interval=delay + 4)
                gotcha = T.translate("gotcha")
                params = {"name": monster.name.upper()}
                if len(trainer.monsters) >= prepare.PARTY_LIMIT:
                    info = T.format("gotcha_kennel", params)
                else:
                    info = T.format("gotcha_team", params)
                gotcha += "\n" + info
                delay += len(gotcha) * config_combat.letter_time
                self.task(
                    partial(self.alert, gotcha),
                    interval=delay,
                )

            self.task(kill_monster, interval=2 + num_shakes)
            delay = num_shakes / 2
            self.task(partial(show_success, delay), interval=num_shakes)
        else:
            breakout_delay = 1.8 + num_shakes * 1.0

            def show_monster(delay: float) -> None:
                self.task(
                    partial(toggle_visible, monster_sprite), interval=delay
                )
                self.play_sound_effect(monster.combat_call, delay)

            def capture_capsule(delay: float) -> None:
                assert sprite.animation
                self.task(sprite.animation.play, interval=delay)
                self.task(capdev.kill, interval=delay)

            def blink_monster(delay: float) -> None:
                self.task(partial(self.blink, sprite), interval=delay + 0.5)

            def show_failure(delay: float) -> None:
                label = f"captured_failed_{num_shakes}"
                failed = T.translate(label)
                delay += len(failed) * config_combat.letter_time
                self.task(
                    partial(self.alert, failed),
                    interval=delay,
                )

            show_monster(breakout_delay)
            capture_capsule(breakout_delay)
            blink_monster(breakout_delay)
            show_failure(breakout_delay)

    def update_hud(self, character: NPC, animate: bool, delete: bool) -> None:
        """
        Updates the Heads-Up Display (HUD) for monsters belonging to the given character.

        Parameters:
            character: The character whose monsters' HUDs should be refreshed.
            animate: Whether to animate HUD transitions.
            delete: Whether to delete existing HUDs before updating.
        """
        monsters = self.field_monsters.get_monsters(character)
        if not monsters:
            return

        if delete:
            self._delete_monster_huds(monsters)

        alive_members = alive_party(character)
        if len(monsters) > 1 and len(monsters) <= len(alive_members):
            self._update_multiple_huds(monsters, animate)
        else:
            self._update_single_hud(monsters[0], animate)

    def _delete_monster_huds(self, monsters: list[Monster]) -> None:
        """Deletes the HUDs of all given monsters."""
        for monster in monsters:
            self.hud_manager.delete_hud(monster)

    def _update_multiple_huds(
        self, monsters: list[Monster], animate: bool
    ) -> None:
        """Updates HUDs for multiple monsters with indexed HUD positions."""
        for i, monster in enumerate(monsters):
            hud_id = f"hud{i}"
            self.build_hud(monster, hud_id, animate)

    def _update_single_hud(self, monster: Monster, animate: bool) -> None:
        """Updates the HUD for a single monster using a default HUD ID."""
        self.build_hud(monster, "hud", animate)
