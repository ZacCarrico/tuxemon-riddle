# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random as rd
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import EvolutionStage, MonsterModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

lookup_cache: dict[str, MonsterModel] = {}


@final
@dataclass
class RandomMonsterAction(EventAction):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            random_monster <level>[,npc_slug][,exp][,mon][,shape][,evo]

    Script parameters:
        level: Level of the added monster.
        npc_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.
        exp: Experience modifier
        mon: Money modifier
        shape: Shape (eg. varmint, brute, etc.)
        evo: Stage (eg. basic, stage1, etc.)

    """

    name = "random_monster"
    monster_level: int
    trainer_slug: Optional[str] = None
    exp: Optional[float] = None
    money: Optional[float] = None
    shape: Optional[str] = None
    evo: Optional[str] = None

    def start(self, session: Session) -> None:
        if not lookup_cache:
            _lookup_monsters()

        valid_evos = list(EvolutionStage)

        if self.evo and self.evo not in valid_evos:
            raise ValueError(f"{self.evo} is not a valid evolution stage.")

        filters = [
            monster.slug
            for monster in lookup_cache.values()
            if monster.txmn_id > 0
            and monster.randomly
            and (not self.shape or monster.shape == self.shape)
            and (not self.evo or monster.stage == self.evo)
        ]

        if not filters:
            if self.shape and not self.evo:
                raise ValueError(f"No monsters found with shape: {self.shape}")
            elif self.evo and not self.shape:
                raise ValueError(
                    f"No monsters found with evolution stage: {self.evo}"
                )
            else:
                raise ValueError(
                    f"No monsters found with evolution stage: {self.evo} and shape: {self.shape}.\n"
                    "Please open an issue on Github to request new monsters with these characteristics."
                )

        monster_slug = rd.choice(filters)

        session.client.event_engine.execute_action(
            "add_monster",
            [
                monster_slug,
                self.monster_level,
                self.trainer_slug,
                self.exp,
                self.money,
            ],
            True,
        )


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = MonsterModel.lookup(mon, db)
        if results.txmn_id > 0:
            lookup_cache[mon] = results
