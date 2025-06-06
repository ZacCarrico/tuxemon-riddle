# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class HasTechCondition(CoreCondition):
    """
    Checks if the monster knows already the technique.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "has_tech"
    expected: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return target.moves.has_move(self.expected)
