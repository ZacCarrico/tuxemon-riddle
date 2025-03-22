# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

import yaml
from pydantic import BaseModel, Field, ValidationError

from tuxemon.constants.paths import ITEM_EFFECT_PATH
from tuxemon.db import MonsterModel, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
logger = logging.getLogger(__name__)

lookup_cache: dict[str, MonsterModel] = {}
fishing_configs: dict[str, FishingConfig] = {}


class FishingConfig(BaseModel):
    bait: float = Field(..., ge=0, le=1)
    lower_bound: int = Field(..., ge=0)
    upper_bound: int = Field(..., ge=0)
    stage: list[str]
    shape: list[str]
    shape_weights: dict[str, float]
    sea_blue_color: list[int]
    environment: dict[str, str]


def load_fishing_config_pydantic(yaml_path: str) -> None:
    try:
        with open(yaml_path) as file:
            logger.debug("Loading YAML file...")
            data = yaml.safe_load(file)
            logger.debug("YAML file loaded. Data:", data)
            if not isinstance(data, dict):
                logger.error("Error: Data is not a dictionary.")
                return
            fishing_configs["fishing"] = {
                item_slug: FishingConfig(**item_config)
                for item_slug, item_config in data.items()
            }
            logger.debug("Fishing configs loaded:", fishing_configs)
    except FileNotFoundError:
        logger.error("Error: YAML file not found.")
    except yaml.YAMLError as e:
        logger.error("Error: YAML file is malformed. Error:", e)
    except Exception as e:
        logger.error("Error: An error occurred. Error:", e)


@dataclass
class FishingEffect(ItemEffect):
    """This effect triggers fishing."""

    name = "fishing"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_monsters()

        self.player = self.session.player

        yaml_filename = f"/{self.name}.yaml"
        yaml_path = ITEM_EFFECT_PATH + yaml_filename

        if not fishing_configs:
            load_fishing_config_pydantic(yaml_path)

        self._fish: FishingConfig = fishing_configs["fishing"][item.slug]

        monster_lists = self._get_fishing_monsters()

        if monster_lists and random.random() <= self._fish.bait:
            mon_slug = random.choice(monster_lists)
            level = random.randint(
                self._fish.lower_bound, self._fish.upper_bound
            )
            self._trigger_fishing_encounter(mon_slug, level)
            return ItemEffectResult(
                name=item.name, success=True, num_shakes=0, extras=[]
            )
        return ItemEffectResult(
            name=item.name, success=False, num_shakes=0, extras=[]
        )

    def _get_fishing_monsters(self) -> list[str]:
        """Return a list of monster slugs based on config and shapes with logging for errors."""
        monsters = [
            mon.slug
            for mon in lookup_cache.values()
            if mon.stage.value in self._fish.stage
            and mon.shape in self._fish.shape
        ]

        if not monsters:
            logger.error(
                f" Expected shapes: {self._fish.shape}, but none matched."
            )

        weights = [self._fish.shape_weights.get(mon, 1.0) for mon in monsters]
        if not monsters:
            return []
        else:
            return random.choices(monsters, weights=weights, k=1)

    def _trigger_fishing_encounter(self, mon_slug: str, level: int) -> None:
        """Trigger a fishing encounter"""
        client = self.session.client

        environment = (
            self._fish.environment.get("night")
            if self.player.game_variables["stage_of_day"] == "night"
            else self._fish.environment.get("default")
        )
        rgb = ":".join(map(str, self._fish.sea_blue_color))
        client.event_engine.execute_action(
            "wild_encounter",
            [mon_slug, level, None, None, environment, rgb],
            True,
        )


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results
