# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import StatType

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class BuffEffect(CoreEffect):
    """
    Increases or decreases target's stats by percentage temporarily.

    Parameters:
        statistic: type of statistic (hp, armour, etc.)
        percentage: percentage of the statistic (increase / decrease)

    """

    name = "buff"
    statistic: StatType
    percentage: float

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if self.statistic not in list(StatType):
            raise ValueError(f"{self.statistic} isn't among {list(StatType)}")

        amount = target.return_stat(StatType(self.statistic))
        value = int(amount * self.percentage)

        target.armour += value if self.statistic == StatType.armour else 0
        target.dodge += value if self.statistic == StatType.dodge else 0
        target.hp += value if self.statistic == StatType.hp else 0
        target.melee += value if self.statistic == StatType.melee else 0
        target.speed += value if self.statistic == StatType.speed else 0
        target.ranged += value if self.statistic == StatType.ranged else 0

        return ItemEffectResult(name=item.name, success=True)
