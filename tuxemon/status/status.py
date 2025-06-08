# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon.constants import paths
from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.core.core_manager import ConditionManager, EffectManager
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.db import (
    CategoryStatus,
    Range,
    ResponseStatus,
    db,
)
from tuxemon.locale import T
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.plugin import PluginObject
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "steps",
)


class Status:
    """
    Particular status that tuxemon monsters can be affected.
    """

    effect_manager: Optional[EffectManager] = None
    condition_manager: Optional[ConditionManager] = None

    def __init__(
        self,
        steps: float = 0.0,
        host: Optional[Monster] = None,
        save_data: Optional[Mapping[str, Any]] = None,
    ) -> None:
        save_data = save_data or {}

        self.instance_id: UUID = uuid4()
        self.set_steps(steps)
        self.bond: bool = False
        self.counter: int = 0
        self.cond_id: int = 0
        self.animation: Optional[str] = None
        self.category: Optional[CategoryStatus] = None
        self.combat_state: Optional[CombatState] = None
        self.description: str = ""
        self.flip_axes: FlipAxes = FlipAxes.NONE
        self.gain_cond: str = ""
        self.icon: str = ""
        self.set_host(host)
        self.name: str = ""
        self.nr_turn: int = 0
        self.duration: int = 0
        self.phase: Optional[str] = None
        self.range: Range = Range.melee
        self.on_positive_status: Optional[ResponseStatus] = None
        self.on_negative_status: Optional[ResponseStatus] = None
        self.on_tech_use: Optional[str] = None
        self.on_item_use: Optional[str] = None
        self.sfx: str = ""
        self.sort: str = ""
        self.slug: str = ""
        self.use_success: str = ""
        self.use_failure: str = ""

        if Status.effect_manager is None:
            Status.effect_manager = EffectManager(
                CoreEffect, paths.CORE_EFFECT_PATH.as_posix()
            )
        if Status.condition_manager is None:
            Status.condition_manager = ConditionManager(
                CoreCondition, paths.CORE_CONDITION_PATH.as_posix()
            )

        self.effects: Sequence[PluginObject] = []
        self.conditions: Sequence[PluginObject] = []

        self.set_state(save_data)

    @classmethod
    def create(
        cls,
        slug: str,
        steps: float = 0.0,
        host: Optional[Monster] = None,
        save_data: Optional[Mapping[str, Any]] = None,
    ) -> Status:
        method = cls(steps, host, save_data)
        method.load(slug)
        return method

    def load(self, slug: str) -> None:
        """
        Loads and sets this status's attributes from the status
        database. The status is looked up in the database by slug.

        Parameters:
            The slug of the status to look up in the database.
        """
        try:
            results = db.lookup(slug, table="status")
        except KeyError:
            raise RuntimeError(f"Status {slug} not found")

        self.slug = results.slug
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        self.sort = results.sort

        # status use notifications (translated!)
        self.gain_cond = T.maybe_translate(results.gain_cond)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon

        self.modifiers = results.modifiers
        # monster stats
        self.statspeed = results.statspeed
        self.stathp = results.stathp
        self.statarmour = results.statarmour
        self.statmelee = results.statmelee
        self.statranged = results.statranged
        self.statdodge = results.statdodge
        # status fields
        self.duration = results.duration
        self.bond = results.bond
        self.category = results.category
        self.on_negative_status = results.on_negative_status
        self.on_positive_status = results.on_positive_status
        self.on_tech_use = results.on_tech_use
        self.on_item_use = results.on_item_use

        self.cond_id = results.cond_id

        if self.effect_manager and results.effects:
            self.effects = self.effect_manager.parse_effects(results.effects)
        if self.condition_manager and results.conditions:
            self.conditions = self.condition_manager.parse_conditions(
                results.conditions
            )
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_handler = EffectProcessor(self.effects)

        # Load the animation sprites that will be used for this status
        self.animation = results.animation
        self.flip_axes = results.flip_axes

        # Load the sound effect for this status
        self.sfx = results.sfx

    def get_combat_state(self) -> CombatState:
        """Returns the CombatState."""
        if not self.combat_state:
            raise ValueError("No CombatState.")
        return self.combat_state

    def set_combat_state(self, combat_state: Optional[CombatState]) -> None:
        """Sets the CombatState."""
        self.combat_state = combat_state

    def advance_round(self) -> None:
        """Advance the counter for this status if used."""
        self.counter += 1

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the status has on its use.
        """
        return self.condition_handler.validate(session=session, target=target)

    def get_host(self) -> Monster:
        """Returns the monster associated with this status."""
        if not self.host:
            raise ValueError("No monster is linked to this status.")
        return self.host

    def set_host(self, monster: Optional[Monster]) -> None:
        """Sets the monster associated with this status."""
        self.host = monster

    def set_steps(self, steps: float) -> None:
        """Sets the steps."""
        self.steps = steps

    def has_reached_duration(self) -> bool:
        """Checks if the status has reached or exceeded its duration."""
        return self.nr_turn >= self.duration > 0

    def has_exceeded_duration(self) -> bool:
        """Checks if the status has lasted beyond its intended duration."""
        return self.nr_turn > self.duration

    def execute_status_action(
        self,
        session: Session,
        combat_instance: CombatState,
        target: Monster,
        phase: str,
    ) -> StatusEffectResult:
        """Executes the current status action and returns the result."""
        self.set_combat_state(combat_instance)
        self.phase = phase
        return self.use(session, target)

    def use(self, session: Session, target: Monster) -> StatusEffectResult:
        """
        Applies the status's effects using EffectProcessor and returns the results.
        """
        result = self.effect_handler.process_status(
            session=session,
            source=self,
            target=target,
        )
        return result

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the status to be saved to a file.
        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id.hex)

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """Loads information from saved data."""
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_status(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Status]:
    return [Status(save_data=cond) for cond in json_data or {}]


def encode_status(
    conds: Sequence[Status],
) -> Sequence[Mapping[str, Any]]:
    return [cond.get_state() for cond in conds]
