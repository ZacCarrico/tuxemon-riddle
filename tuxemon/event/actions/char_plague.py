# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class CharPlagueAction(EventAction):
    """
    Set the entire party as infected or inoculated or healthy.

    Script usage:
        .. code-block::

            char_plague <plague_slug>,<condition>[,character]

    Script parameters:
        plague_slug: The slug of the plague to target.
        condition: Infected, inoculated, or None (removes the plague from the
            character, indicating a healthy state).
        character: Either "player" or character slug name (e.g. "npc_maple").
    """

    name = "char_plague"
    plague_slug: str
    condition: Optional[str] = None
    character: Optional[str] = None

    def start(self, session: Session) -> None:
        self.character = "player" if self.character is None else self.character
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        for monster in character.monsters:
            if self.condition is None:
                monster.plague.clear_plagues()
            elif self.condition == "infected":
                monster.plague.infect(self.plague_slug)
            elif self.condition == "inoculated":
                monster.plague.inoculate(self.plague_slug)
            else:
                raise ValueError(
                    f"{self.condition} must be 'infected' or 'inoculated'."
                )
