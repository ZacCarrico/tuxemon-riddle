# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.combat import check_battle_legal
from tuxemon.db import EnvironmentModel, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.combat.combat import CombatContext

logger = logging.getLogger(__name__)


@final
@dataclass
class StartBattleAction(EventAction):
    """
    Start a battle between two characters and switch to the combat module.

    Script usage:
        .. code-block::

            start_battle <character1>,<character2>[,music]

    Script parameters:
        character1: Either "player" or character slug name (e.g. "npc_maple").
        character2: Either "player" or character slug name (e.g. "npc_maple").
        music: The name of the music file to play (Optional).
    """

    name = "start_battle"
    character1: str
    character2: Optional[str] = None
    music: Optional[str] = None

    def start(self, session: Session) -> None:
        self.character2 = self.character2 or "player"

        character1 = get_npc(session, self.character1)
        character2 = get_npc(session, self.character2)

        if not character1 or not character2:
            _char = self.character1 if not character1 else self.character2
            logger.error(f"Character not found in map: {_char}")
            return

        if not (
            check_battle_legal(character1) and check_battle_legal(character2)
        ):
            logger.warning("Battle is not legal, won't start")
            return

        env_slug = "grass"
        for fighter in [character1, character2]:
            if fighter.isplayer:
                env_slug = fighter.game_variables.get("environment", "grass")
            else:
                env_slug = session.player.game_variables.get(
                    "environment", "grass"
                )

        env = EnvironmentModel.lookup(env_slug, db)

        fighters = sorted(
            [character1, character2], key=lambda x: not x.isplayer
        )

        logger.info(
            f"Starting battle between {fighters[0].name} and {fighters[1].name}!"
        )
        context = CombatContext(
            session=session,
            players=(fighters[0], fighters[1]),
            combat_type="trainer",
            graphics=env.battle_graphics,
            battle_mode="single",
        )
        session.client.push_state("CombatState", context=context)

        filename = env.battle_music if not self.music else self.music
        session.client.event_engine.execute_action(
            "play_music", [filename], True
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("CombatState")
        except ValueError:
            self.stop()
