# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class RemoveEffect(CoreEffect):
    """
    This effect has a chance to remove a status effect.

    Parameters:
        status: The Status slug (e.g. enraged).
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg "remove xxx,own_monster" removes only xxx
    eg "remove all,own_monster" removes everything
    """

    name = "remove"
    status: str
    objectives: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters: list[Monster] = []
        combat = tech.get_combat_state()

        objectives = self.objectives.split(":")
        potency = random.random()
        value = combat._random_tech_hit.get(user, 0.0)
        success = tech.potency >= potency and tech.accuracy >= value

        if success:
            monsters = get_target_monsters(objectives, tech, user, target)
            if self.status == "all":
                for monster in monsters:
                    monster.status.clear_status(session)
            else:
                for monster in monsters:
                    if monster.status.has_status(self.status):
                        monster.status.clear_status(session)

        if monsters:
            combat.update_icons_for_monsters()
            combat.animate_update_party_hud()

        return TechEffectResult(name=tech.name, success=bool(monsters))
