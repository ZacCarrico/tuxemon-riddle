# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

from pygame.rect import Rect

from tuxemon.platform.events import PlayerInput
from tuxemon.state import State


class HeadlessServerState(State):
    """State for running the game server without graphics."""

    rect = Rect((0, 0), (0, 0))
    transparent = True
    force_draw = False

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
