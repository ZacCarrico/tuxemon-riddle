# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_coord_direction, get_direction


@final
@dataclass
class PathfindToPlayerAction(EventAction):
    """
    Handles NPC movement by pathfinding towards the player with configurable
    direction and distance.

    Script usage:
        .. code-block::

            pathfind_to_player <npc_slug>,[direction],[distance]

    Script parameters:
        npc_slug: Unique identifier for the NPC (e.g., "npc_maple").
        direction: Determines approach direction (up, down, left, or right).
        distance: Number of tiles to maintain from the player (e.g. 2,3,4).
    """

    name = "pathfind_to_player"
    npc_slug: str
    direction: Optional[Direction] = None
    distance: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        client = self.session.client
        self.npc = get_npc(self.session, self.npc_slug)
        assert self.npc

        distance = max(1, self.distance or 1)

        direction = self.direction or get_direction(
            player.tile_pos, self.npc.tile_pos
        )
        closest = get_coord_direction(
            player.tile_pos, direction, client.map_size, distance
        )

        self.npc.set_facing(direction)

        self.npc.pathfind(closest)

    def update(self) -> None:
        assert self.npc
        if not (self.npc.moving or self.npc.path):
            self.stop()
