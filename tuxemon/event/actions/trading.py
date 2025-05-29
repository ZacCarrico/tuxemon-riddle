# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.db import SeenStatus, db
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.time_handler import today_ordinal

if TYPE_CHECKING:
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


@final
@dataclass
class TradingAction(EventAction):
    """
    Select a monster in the player party and trade.

    Script usage:
        .. code-block::

            trading <variable>,<added>

    Script parameters:
        variable: Name of the variable where to store the monster id (removed).
        added: Slug monster or Name of the variable where to store the monster
            id (added).

    eg. "trading name_variable,apeoro"
    eg. "trading name_variable,name_variable"

    """

    name = "trading"
    variable: str
    added: str

    def start(self, session: Session) -> None:
        player = session.player
        _monster_id = uuid.UUID(player.game_variables[self.variable])
        monster_id = get_monster_by_iid(session, _monster_id)
        if monster_id is None:
            logger.error("Monster not found")
            return

        if self.added in db.database["monster"]:
            new = _create_traded_monster(monster_id, self.added)
            assert monster_id.owner
            slot = monster_id.owner.monsters.index(monster_id)
            monster_id.owner.remove_monster(monster_id)
            monster_id.owner.add_monster(new, slot)
            monster_id.owner.tuxepedia.add_entry(new.slug, SeenStatus.caught)
        else:
            _added_id = uuid.UUID(player.game_variables[self.added])
            added_id = get_monster_by_iid(session, _added_id)
            if added_id is None:
                logger.error("Monster not found")
                return
            _switch_monsters(monster_id, added_id)


def _create_traded_monster(removed: Monster, added: str) -> Monster:
    """Create a new monster with the same level and moves as the removed monster."""
    new = Monster.create(added)
    new.set_level(removed.level)
    new.set_moves(removed.level)
    new.set_capture(today_ordinal())
    new.current_hp = new.hp
    new.traded = True
    return new


def _switch_monsters(removed: Monster, added: Monster) -> None:
    """Switch two monsters between their owners."""
    receiver = removed.owner
    giver = added.owner
    if receiver is None or giver is None:
        logger.error("Monster owner not found!")
        return

    slot_removed = receiver.monsters.index(removed)
    slot_added = giver.monsters.index(added)

    removed.traded = True
    added.traded = True

    logger.info(f"{removed.name} traded for {added.name}!")
    logger.info(f"{added.name} traded for {removed.name}!")
    logger.info(f"{receiver.name} welcomes {added.name}!")
    logger.info(f"{giver.name} welcomes {removed.name}!")

    giver.remove_monster(removed)
    receiver.add_monster(added, slot_removed)
    receiver.tuxepedia.add_entry(added.slug, SeenStatus.caught)

    receiver.remove_monster(added)
    giver.add_monster(removed, slot_added)
    giver.tuxepedia.add_entry(removed.slug, SeenStatus.caught)
