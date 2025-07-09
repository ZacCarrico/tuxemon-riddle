# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class QuarantineAction(EventAction):
    """
    Quarantine or release monsters infected with a specific plague.

    Usage:
        quarantine <character>,<plague_slug>,<value>[,amount]

    Parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        plague_slug: The slug of the plague to target.
        value: "in" to quarantine infected monsters, "out" to release them.
        amount: (Optional, only for "out") The number of monsters to release
            randomly.

    Example: "quarantine out,5" (Release 5 infected monsters randomly)
    """

    name = "quarantine"
    npc_slug: str
    plague_slug: str
    value: str
    amount: Optional[int] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        if not character.monster_boxes.has_box(self.name, "monster"):
            character.monster_boxes.create_box(self.name, "monster")
        if self.value == "in":
            plague = [
                mon
                for mon in character.monsters
                if mon.plague.has_plague(self.plague_slug)
                and mon.plague.is_infected_with(self.plague_slug)
            ]
            for _monster in plague:
                _monster.plague.inoculate(self.plague_slug)
                character.monster_boxes.add_monster(self.name, _monster)
                character.party.remove_monster(_monster)
                logger.info(f"{_monster} has been quarantined")
        elif self.value == "out":
            if not character.monster_boxes.has_box(self.name, "monster"):
                logger.info(f"Box {self.name} does not exist")
                return
            box = [
                mon
                for mon in character.monster_boxes.get_monsters(self.name)
                if mon.plague.has_plague(self.plague_slug)
            ]
            if not box:
                logger.info(f"Box {self.name} is empty")
                return
            if self.amount is None or self.amount >= len(box):
                for _monster in box:
                    _monster.plague.inoculate(self.plague_slug)
                    character.party.add_monster(
                        _monster, len(character.monsters)
                    )
                    character.monster_boxes.remove_monster_from(
                        self.name, _monster
                    )
                    logger.info(f"{_monster} has been inoculated")
            elif self.amount > 0 and self.amount <= len(box):
                sample = random.sample(box, self.amount)
                for _monster in sample:
                    _monster.plague.inoculate(self.plague_slug)
                    character.party.add_monster(
                        _monster, len(character.monsters)
                    )
                    character.monster_boxes.remove_monster_from(
                        self.name, _monster
                    )
                    logger.info(f"{_monster} has been inoculated")
            else:
                logger.info(f"Invalid sample size")
        else:
            raise ValueError(f"{self.value} must be in or out")
