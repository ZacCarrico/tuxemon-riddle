# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Optional


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
    def __init__(self, options: Sequence[ChoiceOption]):
        self.options = list(options)

    def add(self, option: ChoiceOption, position: Optional[int] = None):
        if position is None:
            self.options.append(option)
        else:
            self.options.insert(position, option)

    def remove(self, key: str):
        self.options = [opt for opt in self.options if opt.key != key]

    def replace(self, key: str, new_option: ChoiceOption):
        for i, opt in enumerate(self.options):
            if opt.key == key:
                self.options[i] = new_option
                break

    def get_menu(self) -> Sequence[ChoiceOption]:
        return self.options
