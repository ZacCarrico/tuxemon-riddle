# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class PhotogenesisEffect(CoreEffect):
    """
    Healing effect based on photogenesis or not.

    Parameters:
        start_hour: The hour when the effect starts healing.
        peak_hour: The hour when the effect heals (maximum)
        end_hour: The hour when the effect stops healing.

    eg "photogenesis 18,0,6"
    """

    name = "photogenesis"
    start_hour: int
    peak_hour: int
    end_hour: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = tech.get_combat_state()
        player = user.get_owner()
        extra: list[str] = []
        done: bool = False

        tech.hit = tech.accuracy >= combat.get_tech_hit(user)

        hour = int(player.game_variables.get("hour", 0))
        hp = user.shape.attributes.hp
        max_multiplier = hp / 2

        multiplier = formula.calculate_time_based_multiplier(
            hour=hour,
            peak_hour=self.peak_hour,
            max_multiplier=max_multiplier,
            start=self.start_hour,
            end=self.end_hour,
        )

        factors = {self.name: multiplier}

        if tech.hit and not session.client.map_manager.map_inside:
            heal = formula.simple_heal(tech, user, factors)
            if heal == 0:
                extra = [tech.use_failure]
            else:
                if user.hp_ratio < 1.0:
                    heal_amount = min(heal, user.missing_hp)
                    user.current_hp += heal_amount
                    done = True
                elif user.hp_ratio == 1.0:
                    extra = ["combat_full_health"]
        return TechEffectResult(name=tech.name, success=done, extras=extra)
