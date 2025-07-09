# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.npc import NPC
from tuxemon.session import Session
from tuxemon.ui.text_formatter import TextFormatter

logger = logging.getLogger(__name__)


@final
@dataclass
class ChoiceMonsterAction(EventAction):
    """
    Ask the player to make a choice among monsters.

    Script usage:
        .. code-block::

            choice_monster <choices>,<variable>

    Script parameters:
        choices: List of possible choices
            (monster slugs eg: rockitten:apeoro),
            separated by a colon ":".
        variable: Variable to store the result of the choice.
    """

    name = "choice_monster"

    choices: str
    variable: str

    def start(self, session: Session) -> None:
        def _set_variable(var_value: str, player: NPC) -> None:
            player.game_variables[self.variable] = var_value
            session.client.pop_state()

        # perform text substitutions
        choices = TextFormatter.replace_text(session, self.choices, T)
        player = session.player

        # make menu options for each string between the colons
        var_list: list[str] = choices.split(":")
        var_menu: list[tuple[str, str, Callable[[], None]]] = []

        for val in var_list:
            text = T.translate(val)
            var_menu.append((text, val, partial(_set_variable, val, player)))

        session.client.push_state("ChoiceMonster", menu=var_menu)

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("ChoiceMonster")
        except ValueError:
            self.stop()
