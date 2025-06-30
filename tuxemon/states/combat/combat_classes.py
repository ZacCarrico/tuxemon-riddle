# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Deque, Optional, Union

from tuxemon.animation_entity import AnimationEntity
from tuxemon.formula import config_combat, speed_monster
from tuxemon.item.item import Item
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.sprite import Sprite
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique


@dataclass
class MenuVisibility:
    menu_fight: bool = True
    menu_monster: bool = True
    menu_item: bool = True
    menu_forfeit: bool = False
    menu_run: bool = True

    def update_visibility(self, key: str, visible: bool) -> None:
        if hasattr(self, key):
            setattr(self, key, visible)
        else:
            raise ValueError(f"Invalid menu item key: {key}")

    def reset_to_default(self) -> None:
        self.__dict__.update(MenuVisibility().__dict__)


@dataclass
class EnqueuedAction:
    user: Union[Monster, NPC, None]
    method: Union[Technique, Item, Status, None]
    target: Monster

    def __repr__(self) -> str:
        return f"EnqueuedAction(user={self.user}, method={self.method}, target={self.target})"


@dataclass
class DamageReport:
    attack: Monster
    defense: Monster
    damage: int
    turn: int

    def __repr__(self) -> str:
        return (
            f"DamageReport(attack={self.attack}, defense={self.defense}, "
            f"damage={self.damage}, turn={self.turn})"
        )


class DamageTracker:
    def __init__(self) -> None:
        self._damage_map: dict[tuple[Monster, Monster], list[DamageReport]] = (
            {}
        )

    def log_damage(
        self, attacker: Monster, defender: Monster, damage: int, turn: int
    ) -> None:
        """
        Log a damage event into the damage map.
        """
        key = (attacker, defender)
        if key not in self._damage_map:
            self._damage_map[key] = []
        self._damage_map[key].append(
            DamageReport(attacker, defender, damage, turn)
        )

    def get_damages(
        self, attacker: Monster, defender: Monster
    ) -> list[DamageReport]:
        """
        Retrieve all damage reports for a specific pair of attacker
        and defender.
        """
        key = (attacker, defender)
        return self._damage_map.get(key, [])

    def remove_monster(self, monster: Monster) -> None:
        """
        Remove all damage reports involving the given monster.
        """
        self._damage_map = {
            key: reports
            for key, reports in self._damage_map.items()
            if key[0] != monster and key[1] != monster
        }

    def clear_damage(self) -> None:
        """
        Clear all damage reports.
        """
        self._damage_map.clear()

    def get_all_damages(self) -> list[DamageReport]:
        """
        Flatten and retrieve all recorded damage reports as a single list.
        """
        return [
            report
            for reports in self._damage_map.values()
            for report in reports
        ]

    def get_attackers(self, loser: Monster) -> set[Monster]:
        """
        Retrieve all monsters who attacked the given target (loser).
        """
        attackers = set()
        for reports in self._damage_map.values():
            for report in reports:
                if report.defense == loser:
                    attackers.add(report.attack)
        return attackers

    def count_hits(
        self, loser: Monster, winner: Optional[Monster] = None
    ) -> tuple[int, int]:
        """
        Count the number of hits on the loser and optionally the hits
        by a specific winner.
        """
        total_hits = 0
        winner_hits = 0
        for reports in self._damage_map.values():
            for report in reports:
                if report.defense == loser:
                    total_hits += 1
                    if winner and report.attack == winner:
                        winner_hits += 1
        return total_hits, winner_hits

    def total_damage_by_attacker(self, attacker: Monster) -> int:
        """
        Calculate the total damage dealt by a specific attacker.
        """
        return sum(
            report.damage
            for reports in self._damage_map.values()
            for report in reports
            if report.attack == attacker
        )

    def __repr__(self) -> str:
        return (
            f"DamageTracker with {len(self.get_all_damages())} entries. "
            f"Attackers: {set(report.attack for report in self.get_all_damages())}"
        )


class MethodAnimationCache:
    def __init__(self) -> None:
        self._sprites: dict[
            Union[Technique, Status, Item], Optional[Sprite]
        ] = {}

    def get(
        self, method: Union[Technique, Status, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return a sprite usable as a method (technique, item, status) animation.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        try:
            return self._sprites[method]
        except KeyError:
            sprite = self.load_method_animation(method, is_flipped)
            self._sprites[method] = sprite
            return sprite

    @staticmethod
    def load_method_animation(
        method: Union[Technique, Status, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return animated sprite from a technique, status or item.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        if not method.animation:
            return None

        ani = AnimationEntity(method.animation)
        if is_flipped:
            ani.play.flip(method.flip_axes)
        return Sprite(animation=ani.play)


class SortManager:
    SORT_ORDER = config_combat.sort_order

    @classmethod
    def get_sort_index(cls, action_sort_type: str) -> int:
        """Returns the index of the action sort type in the SORT_ORDER list."""
        try:
            return cls.SORT_ORDER.index(action_sort_type)
        except ValueError:
            return len(cls.SORT_ORDER)

    @classmethod
    def get_action_sort_key(cls, action: EnqueuedAction) -> tuple[int, int]:
        """
        Returns a tuple representing the sort key for the given action.

        The sort key is a tuple of two integers: the primary order and the
        secondary order. The primary order is determined by the action's sort
        type, and the secondary order is determined by the user's speed test
        result (if applicable).

        If the action's method is None, or if the action's user is None, the
        function returns a default sort key of (0, 0).
        """
        if action.method is None or action.user is None:
            return 0, 0

        action_sort_type = action.method.sort
        primary_order = cls.get_sort_index(action_sort_type)

        if action_sort_type in ["meta", "potion"]:
            return primary_order, 0
        else:
            return primary_order, -speed_test(action)


def speed_test(action: EnqueuedAction) -> int:
    """
    Calculate the speed modifier for the given action.
    """
    if isinstance(action.user, Monster):
        if isinstance(action.method, Technique):
            return speed_monster(action.user, action.method)
    if isinstance(action.user, NPC):
        return 10
    return 0


class ActionHistory:
    def __init__(self) -> None:
        self.history: list[tuple[int, EnqueuedAction]] = []

    def add_action(self, turn: int, action: EnqueuedAction) -> None:
        self.history.append((turn, action))

    def get_actions_by_turn(self, turn: int) -> list[EnqueuedAction]:
        return [action for _turn, action in self.history if _turn == turn]

    def clear(self) -> None:
        """Clears the entire action history."""
        self.history.clear()

    def get_actions_by_turn_range(
        self, start_turn: int, end_turn: int
    ) -> list[EnqueuedAction]:
        """Retrieves all actions that occurred between the specified turn range."""
        return [
            action
            for _turn, action in self.history
            if start_turn <= _turn <= end_turn
        ]

    def count_actions(self) -> int:
        """Returns the total number of actions recorded in history."""
        return len(self.history)

    def get_last_action(self) -> Optional[EnqueuedAction]:
        """Retrieves the last action recorded in history."""
        return self.history[-1][1] if self.history else None

    def __repr__(self) -> str:
        """Returns a string representation of the ActionHistory."""
        action_count = len(self.history)
        # Get the last 3 actions for the sample
        sample_actions = self.history[-3:]
        sample_repr = ", ".join(
            f"({turn}, {action})" for turn, action in sample_actions
        )
        return f"ActionHistory(count={action_count}, sample=[{sample_repr}])"


class ActionQueue:
    def __init__(self) -> None:
        self._action_queue: list[EnqueuedAction] = []
        self._pending_queue: list[tuple[int, EnqueuedAction]] = []
        self._action_history = ActionHistory()

    @property
    def queue(self) -> list[EnqueuedAction]:
        """Returns the current action queue."""
        return self._action_queue

    @property
    def history(self) -> ActionHistory:
        """Returns the current action history."""
        return self._action_history

    @property
    def pending(self) -> list[tuple[int, EnqueuedAction]]:
        """Returns the pending actions."""
        return self._pending_queue

    def enqueue(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the queue and history."""
        self._action_queue.append(action)
        self._action_history.add_action(turn, action)

    def add_pending(self, action: EnqueuedAction, turn: int) -> None:
        """Adds an action to the end of the pending queue."""
        self._pending_queue.append((turn, action))

    def autoclean_pending(self) -> None:
        """Removes actions from the pending queue under certain conditions."""
        self._pending_queue = [
            (turn, pend)
            for turn, pend in self._pending_queue
            if not (
                (
                    pend.user
                    and isinstance(pend.user, Monster)
                    and pend.user.is_fainted
                )
                or pend.target.is_fainted
            )
        ]

    def from_pending_to_action(self, turn: int) -> None:
        """
        Removes actions from the pending queue and implements them in the
        action queue.
        """
        for _turn, pend in self._pending_queue[:]:
            if _turn == turn:
                self.enqueue(pend, turn)
                self._pending_queue.remove((turn, pend))

    def dequeue(self, action: EnqueuedAction) -> None:
        """Removes an action from the queue if it exists."""
        try:
            self._action_queue.remove(action)
        except ValueError:
            raise ValueError(f"Action {action} not found in queue")

    def pop(self) -> EnqueuedAction:
        """Removes and returns the last action from the queue."""
        return self._action_queue.pop()

    def is_empty(self) -> bool:
        """Returns True if the queue is empty, False otherwise."""
        return len(self._action_queue) == 0

    def clear_queue(self) -> None:
        """Clears the entire queue."""
        self._action_queue.clear()

    def clear_history(self) -> None:
        """Clears the entire history."""
        self._action_history.clear()

    def clear_pending(self) -> None:
        """Clears the entire pending queue."""
        self._pending_queue.clear()

    def sort(self) -> None:
        """
        Sorts the queue based on the action's sort key (game rules).
        * Techniques that damage are sorted by monster speed (fastest monsters first)
        * Items are sorted by trainer speed (fastest trainers first)
        * Actions are ordered from lowest to highest priority, with the highest priority
        actions last in the queue.
        """
        self._action_queue.sort(
            key=SortManager.get_action_sort_key, reverse=True
        )

    def swap(self, old: Monster, new: Monster) -> None:
        """Swaps the target of all actions in the queue from old to new."""
        for index, action in enumerate(self._action_queue):
            if action.target == old:
                self.__replace(index, action.user, action.method, new)

    def rewrite(
        self, monster: Monster, method: Union[Technique, Item, Status]
    ) -> None:
        """Rewrites the method of all actions in the queue for the given monster."""
        for index, action in enumerate(self._action_queue):
            if action.user == monster:
                self.__replace(index, monster, method, action.target)

    def __replace(
        self,
        index: int,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, Status, None],
        target: Monster,
    ) -> None:
        """Replaces an action in the queue at the given index."""
        new_action = EnqueuedAction(user, method, target)
        self._action_queue[index] = new_action

    def get_last_action(
        self, turn: int, monster: Monster, field: str
    ) -> Optional[EnqueuedAction]:
        """
        Retrieves the last action involving the specified monster in the given turn.

        Parameters:
            turn: The turn number to search in.
            monster: The monster to search for.
            field: The field to search in ('user' or 'target').

        Returns:
            The last matching action, or None if not found.
        """
        if field not in ("user", "target"):
            raise ValueError(f"{field} must be 'user' or 'target'")

        for _turn, action in reversed(self._action_history.history):
            if _turn == turn and (
                (field == "user" and action.user == monster)
                or (field == "target" and action.target == monster)
            ):
                return action

        return None

    def get_all_actions_by_turn(self, turn: int) -> list[EnqueuedAction]:
        """
        Retrieves all actions that occurred in the specified turn.

        Parameters:
            turn: The turn number to retrieve actions for.

        Returns:
            A list of actions that occurred in the specified turn.
        """
        return self._action_history.get_actions_by_turn(turn)


def compute_text_anim_time(message: str) -> float:
    """
    Compute required time for a text animation.

    Parameters:
        message: The given text to be animated.

    Returns:
        The time in seconds expected to be taken by the animation.
    """
    return config_combat.action_time + config_combat.letter_time * len(message)


class TextAnimationManager:
    """
    Manages a queue of timed text animations.
    """

    def __init__(self) -> None:
        self.text_queue: Deque[tuple[Callable[[], None], float]] = deque()
        self._text_time_left: float = 0
        self._xp_messages: list[str] = []

    def update_text_animation(self, time_delta: float) -> None:
        """Update the text animation."""
        self._text_time_left -= time_delta
        if self._text_time_left <= 0 and self.text_queue:
            next_animation, self._text_time_left = self.text_queue.popleft()
            next_animation()

    def add_text_animation(
        self, animation: Callable[..., None], duration: float = 0
    ) -> None:
        """Adds a text animation to the queue."""
        self.text_queue.append((animation, duration))

    def get_text_animation_time_left(self) -> float:
        return self._text_time_left

    def add_xp_message(self, message: str) -> None:
        """Handles XP messages separately, appends them and prepares animation."""
        self._xp_messages.append(message)

    def trigger_xp_animation(self, alert_func: Callable[..., None]) -> None:
        """Only triggers XP animation when explicitly called."""
        if self._xp_messages:
            combined_message = "\n".join(self._xp_messages)
            timed_text_animation = partial(alert_func, combined_message)
            self.add_text_animation(
                timed_text_animation, compute_text_anim_time(combined_message)
            )
            self._xp_messages.clear()
