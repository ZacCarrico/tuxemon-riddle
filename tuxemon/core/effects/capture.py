# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import Acquisition, SeenStatus

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CaptureEffect(CoreEffect):
    """Attempts to capture the target."""

    name = "capture"

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        self.session = session

        # Calculate status modifier
        status_modifier = formula.calculate_status_modifier(item, target)

        # Calculate tuxeball modifier
        player = self.session.player
        tuxeball_modifier = formula.calculate_capdev_modifier(
            item, target, player
        )

        # Perform shake check and capture calculation
        shake_check = formula.shake_check(
            target, status_modifier, tuxeball_modifier
        )
        capture, shakes = formula.capture(shake_check)

        if not capture:
            self._handle_capture_failure(item, target)
            return ItemEffectResult(name=item.name, num_shakes=shakes)

        # Apply capture effects
        self._apply_capture_effects(item, target)

        return ItemEffectResult(
            name=item.name, success=True, num_shakes=shakes
        )

    def _handle_capture_failure(self, item: Item, target: Monster) -> None:
        formula.on_capture_fail(item, target, self.session.player)

    def _apply_capture_effects(self, item: Item, target: Monster) -> None:
        formula.on_capture_success(item, target, self.session.player)
        combat = item.get_combat_state()
        if self.session.player.tuxepedia.is_seen(target.slug):
            combat._new_tuxepedia = True
        self.session.player.tuxepedia.add_entry(target.slug, SeenStatus.caught)
        target.capture_device = item.slug
        target.wild = False
        target.set_acquisition(Acquisition.CAPTURED)
        self.session.player.add_monster(
            target, len(self.session.player.monsters)
        )
