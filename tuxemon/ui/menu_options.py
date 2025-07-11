# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional


def noop_action() -> None:
    """A no-op placeholder action."""


@dataclass
class ChoiceOption:
    """Represents a single option in a choice dialog."""

    key: str = ""
    display_text: str = ""
    action: Callable[[], None] = field(default_factory=lambda: noop_action)

    def __post_init__(self) -> None:
        self.key = self.key.lower().strip()

        if not self.display_text:
            self.display_text = f"Option {self.key or 'Unnamed'}"


class MenuOptions:
    """Manages a collection of ChoiceOption entries for a menu dialog."""

    def __init__(self, options: Sequence[ChoiceOption]) -> None:
        """Initializes the menu with a sequence of choice options."""
        self.options = list(options)

    def add(
        self, option: ChoiceOption, position: Optional[int] = None
    ) -> None:
        """Adds a new option to the menu, optionally at a specific index."""
        if position is None:
            self.options.append(option)
        else:
            self.options.insert(position, option)

    def remove(self, key: str) -> None:
        """Removes the option with the specified key from the menu."""
        self.options = [opt for opt in self.options if opt.key != key]

    def replace(self, key: str, new_option: ChoiceOption) -> None:
        """Replaces an option with the given key using a new option."""
        for i, opt in enumerate(self.options):
            if opt.key == key:
                self.options[i] = new_option
                break

    def get_menu(self) -> Sequence[ChoiceOption]:
        """Returns the current list of menu options."""
        return self.options

    def remove_by_condition(
        self, condition: Callable[[ChoiceOption], bool]
    ) -> None:
        """Removes all options that satisfy the provided condition function."""
        self.options = [opt for opt in self.options if not condition(opt)]

    def add_or_replace(self, new_option: ChoiceOption) -> None:
        """Adds the new option, or replaces the existing one if the key matches."""
        for i, opt in enumerate(self.options):
            if opt.key == new_option.key:
                self.options[i] = new_option
                return
        self.options.append(new_option)

    def sort(
        self,
        key_function: Callable[[ChoiceOption], Any],
        reverse: bool = False,
    ) -> None:
        """Sorts the menu options using the provided key function."""
        self.options.sort(key=key_function, reverse=reverse)

    def filter(self, condition: Callable[[ChoiceOption], bool]) -> None:
        """Keeps only the options that match the condition function."""
        self.options = [opt for opt in self.options if condition(opt)]

    def group_by_prefix(self, prefix: str) -> list[ChoiceOption]:
        """Returns options whose keys start with the given prefix."""
        return [opt for opt in self.options if opt.key.startswith(prefix)]

    def disable(self, key: str) -> None:
        """Disables the option with the given key by replacing its action with no-op."""
        for opt in self.options:
            if opt.key == key:
                opt.action = noop_action
                break
