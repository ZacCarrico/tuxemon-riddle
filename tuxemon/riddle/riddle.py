# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon.constants import paths
from tuxemon.core.core_manager import EffectManager
from tuxemon.db import db
from tuxemon.db import RiddleModel
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "riddle_id",
    "category",
    "difficulty",
    "question",
    "answer",
    "alternate_answers",
    "hint",
    "damage_multiplier",
    "experience_reward",
    "name",
    "description",
    "tags",
)


class Riddle:
    """
    A riddle that can be asked during combat to deal damage.
    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.instance_id: UUID = uuid4()
        self.riddle_id: int = 0
        self.category: str = ""
        self.difficulty: str = ""
        self.question: str = ""
        self.answer: str = ""
        self.alternate_answers: list[str] = []
        self.hint: str = ""
        self.damage_multiplier: float = 1.0
        self.experience_reward: int = 10
        self.slug: str = ""
        self.tags: list[str] = []
        self.name: str = ""
        self.description: str = ""
        self.combat_state: Optional[CombatState] = None

        self.set_state(save_data)

    @classmethod
    def create(cls, slug: str) -> Riddle:
        """
        Create a riddle from its slug.

        Parameters:
            slug: The riddle slug.

        Returns:
            The riddle.
        """
        try:
            results = db.lookup(slug, table="riddle")
            if results is None:
                raise RuntimeError(f"Riddle {slug} not found")
        except KeyError:
            raise RuntimeError(f"Riddle {slug} not found")

        return cls.create_from_db(results)

    @classmethod
    def create_from_db(cls, results: RiddleModel) -> Riddle:
        """
        Create a riddle from database results.

        Parameters:
            results: Query results.

        Returns:
            A riddle object.
        """
        riddle = cls()
        riddle.load_from_db(results)
        return riddle

    def load_from_db(self, results: RiddleModel) -> None:
        """
        Load riddle from database results.

        Parameters:
            results: The riddle model from database.
        """
        self.riddle_id = results.riddle_id
        self.category = results.category
        self.difficulty = results.difficulty
        self.question = results.question
        self.answer = results.answer
        self.alternate_answers = results.alternate_answers or []
        self.hint = results.hint or ""
        self.damage_multiplier = results.damage_multiplier or 1.0
        self.experience_reward = results.experience_reward or 10
        self.slug = results.slug
        self.tags = results.tags or []
        
        # Set name and description with fallbacks
        try:
            self.name = T.translate(f"riddle_{self.slug}_name")
        except:
            self.name = f"Riddle #{self.riddle_id}"
        
        try:
            self.description = T.translate(f"riddle_{self.slug}_description")
        except:
            self.description = self.question

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the riddle to be saved to a file.

        Returns:
            Dictionary containing all the information about the riddle.
        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id.hex)

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        Parameters:
            save_data: Data used to reconstruct the riddle.
        """
        if not save_data:
            return

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)

    def check_answer(self, user_answer: str) -> bool:
        """
        Check if the user's answer is correct.

        Parameters:
            user_answer: The answer provided by the user.

        Returns:
            True if correct, False otherwise.
        """
        if user_answer is None:
            return False
        # Convert to string if it's a number
        if isinstance(user_answer, (int, float)):
            user_answer = str(user_answer)
        user_answer = user_answer.strip().lower()
        correct_answer = self.answer.strip().lower()
        
        if user_answer == correct_answer:
            return True
            
        # Check alternate answers
        for alt_answer in self.alternate_answers:
            if user_answer == alt_answer.strip().lower():
                return True
                
        return False

    def get_difficulty_factor(self) -> float:
        """
        Get difficulty factor for damage calculations.

        Returns:
            Multiplier based on difficulty.
        """
        difficulty_factors = {
            "easy": 1.0,
            "medium": 1.5,
            "hard": 2.0
        }
        return difficulty_factors.get(self.difficulty, 1.0)

    def get_damage_multiplier(self) -> float:
        """
        Get the total damage multiplier for this riddle.

        Returns:
            Combined damage multiplier.
        """
        return self.damage_multiplier * self.get_difficulty_factor()

    def set_combat_state(self, combat: CombatState) -> None:
        """
        Set the combat state for this riddle.

        Parameters:
            combat: The combat state.
        """
        self.combat_state = combat

    def get_combat_state(self) -> Optional[CombatState]:
        """
        Get the combat state for this riddle.

        Returns:
            The combat state or None.
        """
        return self.combat_state

    def validate_monster(self, session: Session, monster: Monster) -> bool:
        """
        Validate if a monster can use this riddle.
        
        For now, all monsters can attempt any riddle.

        Parameters:
            session: The game session.
            monster: The monster attempting the riddle.

        Returns:
            Always True for riddles.
        """
        return True