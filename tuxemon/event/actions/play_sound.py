# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class PlaySoundAction(EventAction):
    """
    Plays a short sound effect from the "resources/sounds/" folder.

    Script usage:
        .. code-block::

            play_sound <filename>[,volume]

    Script parameters:
        filename: The sound file to load (must exist in the sounds database).
        volume: A float between 0.0 and 1.0 representing the relative volume level.
            This value is multiplied by the user's configured sound volume.

    Example:
        If volume=0.5 and the player's sound setting is also 0.5,
        the resulting effective playback volume will be 0.25.

    Note:
        This is intended for short non-looping sound effects (e.g., cues, UI feedback),
        not for ambient or background music.
    """

    name = "play_sound"
    filename: str
    volume: Optional[float] = None

    def start(self, session: Session) -> None:
        client = session.client
        sound_volume = client.config.sound_volume

        if self.volume is not None:
            lower, upper = prepare.SOUND_RANGE
            if not (lower <= self.volume <= upper):
                raise ValueError(
                    f"Volume must be between {lower} and {upper}",
                )
        volume = (
            self.volume * sound_volume
            if self.volume is not None
            else sound_volume
        )

        client.sound_manager.play_sound(self.filename, volume)
