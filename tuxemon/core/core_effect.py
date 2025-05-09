# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Union

from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique


@dataclass
class EffectResult:
    name: str = ""
    success: bool = False
    extras: list[str] = field(default_factory=list)


@dataclass
class TechEffectResult(EffectResult):
    damage: int = 0
    element_multiplier: float = 0.0
    should_tackle: bool = False


@dataclass
class ItemEffectResult(EffectResult):
    num_shakes: int = 0


@dataclass
class StatusEffectResult(EffectResult):
    statuses: list[Status] = field(default_factory=list)
    techniques: list[Technique] = field(default_factory=list)


@dataclass
class Effect:
    name: ClassVar[str]

    def __post_init__(self) -> None:
        cast_dataclass_parameters(self)

    def apply(
        self, session: Session, *args: Any, **kwargs: Any
    ) -> EffectResult:
        raise NotImplementedError(
            "This method should be implemented by subclasses"
        )


@dataclass
class TechEffect(Effect):
    def apply(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        return TechEffectResult(name=tech.name)


@dataclass
class ItemEffect(Effect):
    def apply(
        self, session: Session, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        return ItemEffectResult(name=item.name)


@dataclass
class StatusEffect(Effect):
    def apply(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        return StatusEffectResult(name=status.name)
