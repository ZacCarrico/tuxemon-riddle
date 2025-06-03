# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import set_var
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class ParkEffect(CoreEffect):
    """
    Handles the items used in the park.

    Parameters:
        method: capture, doll or food

    """

    name = "park"
    method: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if self.method == "capture":
            labels = [
                "spyder_park_afraid",
                "spyder_park_stare",
                "spyder_park_wander",
            ]
            label = random.choice(labels)
            set_var(session, item.slug, label)
        elif self.method == "doll":
            pass
        elif self.method == "food":
            pass
        else:
            raise ValueError(f"Must be capture, doll or food")

        return ItemEffectResult(name=item.name, success=True)
