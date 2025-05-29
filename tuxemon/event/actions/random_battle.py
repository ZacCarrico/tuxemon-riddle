# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon import prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import MonsterModel, NpcModel, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState
from tuxemon.time_handler import today_ordinal

logger = logging.getLogger(__name__)

lookup_cache_mon: dict[str, MonsterModel] = {}
lookup_cache_npc: dict[str, NpcModel] = {}


@final
@dataclass
class RandomBattleAction(EventAction):
    """
    Start random battle with a random npc with a determined
    number of monster in a certain range of levels.

    Script usage:
        .. code-block::

            random_battle nr_txmns,min_level,max_level

    Script parameters:
        nr_txmns: Number of tuxemon (1 to 6).
        min_level: Minimum level of the party.
        max_level: Maximum level of the party.
    """

    name = "random_battle"
    nr_txmns: int
    min_level: int
    max_level: int

    def start(self, session: Session) -> None:
        if not lookup_cache_npc or not lookup_cache_mon:
            _lookup()

        # Validate party size and max level
        if not (1 <= self.nr_txmns <= prepare.PARTY_LIMIT):
            logger.error(
                f"Party size {self.nr_txmns} must be between 1 and {prepare.PARTY_LIMIT}"
            )
            return
        if not (1 <= self.max_level <= prepare.MAX_LEVEL):
            logger.error(
                f"Max level {self.max_level} must be between 1 and {prepare.MAX_LEVEL}"
            )
            return

        npc_filters = list(lookup_cache_npc.values())
        self.opponent = random.choice(npc_filters)

        event_engine = session.client.event_engine
        event_engine.execute_action(
            "create_npc", [self.opponent.slug, 0, 0], True
        )

        npc = get_npc(session, self.opponent.slug)
        if npc is None:
            logger.error(f"{self.opponent.slug} not found")
            return

        monster_filters = list(lookup_cache_mon.values())
        monsters = random.sample(monster_filters, self.nr_txmns)
        for monster in monsters:
            level = random.randint(self.min_level, self.max_level)
            current_monster = Monster.create(monster.slug)
            current_monster.set_level(level)
            current_monster.set_moves(level)
            current_monster.set_capture(today_ordinal())
            current_monster.current_hp = current_monster.hp
            current_monster.money_modifier = level
            current_monster.experience_modifier = level
            npc.add_monster(current_monster, len(npc.monsters))

        player = session.player
        env_slug = player.game_variables.get("environment", "grass")
        env = db.lookup(env_slug, table="environment")

        if not (check_battle_legal(player) and check_battle_legal(npc)):
            logger.warning("Battle is not legal, won't start")
            return

        logger.info(f"Starting battle with '{npc.name}'!")
        session.client.push_state(
            "CombatState",
            session=session,
            players=(player, npc),
            combat_type="trainer",
            graphics=env.battle_graphics,
            battle_mode="single",
        )

        session.client.event_engine.execute_action(
            "play_music", [env.battle_music], True
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("CombatState")
        except ValueError:
            self.stop()

    def cleanup(self, session: Session) -> None:
        npc = None
        world = session.client.get_state_by_name(WorldState)
        session.client.npc_manager.remove_npc(self.opponent.slug)


def _lookup() -> None:
    monsters = list(db.database["monster"])
    npcs = list(db.database["npc"])

    for mon in monsters:
        _mon = db.lookup(mon, table="monster")
        if _mon.txmn_id > 0 and _mon.randomly:
            lookup_cache_mon[mon] = _mon

    for npc in npcs:
        _npc = db.lookup(npc, table="npc")
        if not _npc.monsters:
            lookup_cache_npc[npc] = _npc
