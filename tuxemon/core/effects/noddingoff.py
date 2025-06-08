# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class NoddingOffEffect(CoreEffect):
    """
    This effect has a chance to apply the nodding off status effect.

    Sleep lasts for a minimum of one turn.
    It has a 50% chance to end after each turn.
    If it has gone on for 5 turns, it ends.

    Parameters:
        chance: The chance.

    """

    name = "noddingoff"
    chance: float

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        extra: list[str] = []
        tech: list[Technique] = []

        if status.phase == "pre_checking" and status.on_tech_use:
            skip = Technique.create(status.on_tech_use)
            tech = [skip]

        if status.phase == "perform_action_tech" and self.wake_up(status):
            params = {"target": target.name.upper()}
            extra = [T.format("combat_state_dozing_end", params)]
            target.status.clear_status()
        return StatusEffectResult(
            name=status.name,
            success=True,
            techniques=tech,
            extras=extra,
        )

    def wake_up(self, status: Status) -> bool:
        if status.has_reached_duration() and random.random() > self.chance:
            return True
        if status.has_exceeded_duration():
            return True
        return False
