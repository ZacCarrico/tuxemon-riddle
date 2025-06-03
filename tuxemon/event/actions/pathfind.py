# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class PathfindAction(EventAction):
    """
    Pathfind the player / npc to the given location.

    This action blocks until the destination is reached.

    Script usage:
        .. code-block::

            pathfind <npc_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
    """

    name = "pathfind"
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int

    def start(self, session: Session) -> None:
        self.moving_entity = get_npc(session, self.npc_slug)
        assert self.moving_entity
        destination = (self.tile_pos_x, self.tile_pos_y)
        self.moving_entity.pathfind(destination)

    def update(self, session: Session) -> None:
        assert self.moving_entity
        if not (self.moving_entity.moving or self.moving_entity.path):
            self.stop()
