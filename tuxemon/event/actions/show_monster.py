# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final
from uuid import UUID

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.session import Session

logger = logging.getLogger()


@final
@dataclass
class ShowMonsterAction(EventAction):
    """
    Change to MonsterInfoState.

    This action transitions to the MonsterInfoState, displaying detailed
    information about a specific monster.

    Script usage:
        .. code-block::

            monster_info_state <monster_variable>

    Script parameters:
        monster_variable: The name of the game variable holding the monster's UUID.
    """

    name = "show_monster"
    monster_variable: str

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name == "MonsterInfoState":
            logger.error(
                f"The state 'MonsterInfoState' is already active. No action taken."
            )
            return

        monster = self._retrieve_monster(session)
        if monster is None:
            logger.error("Monster not found for MonsterInfoState.")
            return

        params = {"monster": monster, "source": self.name}
        self.client.push_state("MonsterInfoState", kwargs=params)

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("MonsterInfoState")
        except ValueError:
            self.stop()

    def _retrieve_monster(self, session: Session) -> Optional[Monster]:
        """Retrieve a monster from the game database."""
        player = session.player
        if self.monster_variable not in player.game_variables:
            logger.error(f"Game variable {self.monster_variable} not found")
            return None
        try:
            monster_id = UUID(player.game_variables[self.monster_variable])
        except ValueError:
            logger.error(
                f"Invalid UUID in game variable {self.monster_variable}: "
                f"{player.game_variables[self.monster_variable]}"
            )
            return None
        return get_monster_by_iid(session, monster_id)
