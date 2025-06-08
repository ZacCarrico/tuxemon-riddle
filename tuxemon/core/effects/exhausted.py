# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class ExhaustedEffect(CoreEffect):
    """
    Exhausted status

    """

    name = "exhausted"

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        player = target.owner
        assert player
        _statuses: list[Status] = []
        if status.phase == "perform_action_tech":
            target.status.clear_status()
            if status.on_tech_use:
                cond = Status.create(status.on_tech_use, player.steps, target)
                _statuses = [cond]
        return StatusEffectResult(
            name=status.name, success=True, statuses=_statuses
        )
