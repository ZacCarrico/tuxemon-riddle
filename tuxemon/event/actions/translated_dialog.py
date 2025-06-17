# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, final

from tuxemon.db import DialogueModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar, string_to_colorlike
from tuxemon.locale import process_translate_text
from tuxemon.session import Session
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)

style_cache: dict[str, DialogueModel] = {}


@final
@dataclass
class TranslatedDialogAction(EventAction):
    """
    Open a dialog window with translated text according to the passed
    translation key. Parameters passed to the translation string will also
    be checked if a translation key exists.

    Script usage:
        .. code-block::

            translated_dialog <text>[,avatar][,position][,style]

    Script parameters:
        text: Text of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.
        position: Position of the dialog box. Can be 'top', 'bottom', 'center',
            'topleft', 'topright', 'bottomleft', 'bottomright', 'right', 'left'.
            Default 'bottom'.
        alignment: Alignment of text in the dialog box, it can be 'left', 'center'
            or 'right'. Default 'left'.
        vertical_alignment: Alignment of text in the dialog box, it can be 'bottom',
            'middle' or 'top'. Default 'top'.
        style: a predefined style in db/dialogue/dialogue.json
    """

    name = "translated_dialog"
    raw_parameters: str
    avatar: Optional[str] = None
    position: Optional[str] = None
    alignment: Optional[str] = None
    v_alignment: Optional[str] = None
    style: Optional[str] = None

    def start(self, session: Session) -> None:
        key = process_translate_text(session, self.raw_parameters, [])

        avatar_sprite = None
        if self.avatar:
            avatar_sprite = get_avatar(session, self.avatar)

        dialogue = self.style if self.style else "default"
        alignment = self.alignment if self.alignment else "left"
        v_alignment = self.v_alignment if self.v_alignment else "top"
        style = _get_style(dialogue)
        box_style: dict[str, Any] = {
            "bg_color": string_to_colorlike(style.bg_color),
            "font_color": string_to_colorlike(style.font_color),
            "font_shadow": string_to_colorlike(style.font_shadow_color),
            "border": style.border_path,
            "alignment": alignment,
            "v_alignment": v_alignment,
        }
        position = self.position if self.position else "bottom"

        open_dialog(
            client=session.client,
            text=key,
            avatar=avatar_sprite,
            box_style=box_style,
            position=position,
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("DialogState")
        except ValueError:
            self.stop()


def _get_style(cache_key: str) -> DialogueModel:
    if cache_key in style_cache:
        return style_cache[cache_key]
    else:
        try:
            style = DialogueModel.lookup(cache_key, db)
            style_cache[cache_key] = style
            return style
        except KeyError:
            raise RuntimeError(f"Dialogue {cache_key} not found")
