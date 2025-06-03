# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import set_var
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import StatType

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class ChangeStatEffect(CoreEffect):
    """
    Increases or decreases target's stats by percentage permanently.

    Parameters:
        statistic: type of statistic (hp, armour, etc.)
        percentage: percentage of the statistic (increase / decrease)

    """

    name = "change_stat"
    statistic: str
    percentage: float

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if self.statistic not in list(StatType):
            raise ValueError(f"{self.statistic} isn't among {list(StatType)}")

        set_var(session, self.name, str(target.instance_id.hex))
        client = session.client.event_engine
        params = [self.name, self.statistic, self.percentage]
        client.execute_action("modify_monster_stats", params, True)
        return ItemEffectResult(name=item.name, success=True)
