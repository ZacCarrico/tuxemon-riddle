# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import SeenStatus, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.time_handler import today_ordinal


@final
@dataclass
class AddMonsterAction(EventAction):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            add_monster <mon_slug>,<mon_level>[,npc_slug][,exp_mod][,money_mod]

    Script parameters:
        mon_slug: Monster slug to look up in the monster database or name variable
            where it's stored the mon_slug
        mon_level: Level of the added monster.
        npc_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.
        exp_mod: Experience modifier
        money_mod: Money modifier

    """

    name = "add_monster"
    monster_slug: str
    monster_level: int
    npc_slug: Optional[str] = None
    exp: Optional[float] = None
    money: Optional[float] = None

    def start(self, session: Session) -> None:
        player = session.player
        self.npc_slug = self.npc_slug or "player"
        trainer = get_npc(session, self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        if self.monster_slug not in db.database["monster"]:
            if self.monster_slug in player.game_variables:
                monster_slug = player.game_variables[self.monster_slug]
            else:
                raise ValueError(
                    f"{self.monster_slug} doesn't exist (monster or variable)"
                )
        else:
            monster_slug = self.monster_slug

        monster = Monster.create(monster_slug)
        monster.set_level(self.monster_level)
        monster.set_moves(self.monster_level)
        monster.set_capture(today_ordinal())
        monster.current_hp = monster.hp

        if self.exp is not None:
            monster.experience_modifier = self.exp
        if self.money is not None:
            monster.money_modifier = self.money

        trainer.add_monster(monster, len(trainer.monsters))
        trainer.tuxepedia.add_entry(monster.slug, SeenStatus.caught)
        player.game_variables[self.name] = str(monster.instance_id.hex)
