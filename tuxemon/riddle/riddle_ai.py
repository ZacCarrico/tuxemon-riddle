# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tuxemon.riddle.riddle import Riddle
from tuxemon.riddle.riddle_manager import riddle_manager
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


class RiddleAI:
    """
    AI system for riddle-based combat.
    """

    def __init__(
        self,
        session: Session,
        combat: CombatState,
        monster: Monster,
        character: NPC,
    ) -> None:
        self.session = session
        self.combat = combat
        self.character = character
        self.monster = monster
        self.opponents: list[Monster] = (
            combat.field_monsters.get_monsters(combat.players[1])
            if character == combat.players[0]
            else combat.field_monsters.get_monsters(combat.players[0])
        )

    def take_riddle_turn(self) -> None:
        """
        AI takes a turn by attempting to answer a riddle.
        """
        # Get a riddle appropriate for this monster
        riddle = riddle_manager.get_random_riddle(monster=self.monster)
        
        # Determine AI success rate based on monster level and difficulty
        success_rate = self._calculate_success_rate(riddle)
        
        # AI attempts to answer the riddle
        success = random.random() < success_rate
        
        # Create the appropriate technique based on success
        if success:
            technique = Technique.create("riddle_correct")
            target = self.opponents[0] if self.opponents else self.monster
            # Apply riddle damage multiplier
            if hasattr(technique, 'power'):
                technique.power *= riddle.get_damage_multiplier()
            
            logger.debug(f"AI {self.monster.name} answered riddle correctly: {riddle.question}")
        else:
            technique = Technique.create("riddle_incorrect")
            target = self.monster  # AI takes damage for wrong answer
            
            logger.debug(f"AI {self.monster.name} answered riddle incorrectly: {riddle.question}")
        
        technique.set_combat_state(self.combat)
        
        # Enqueue the riddle action
        self.combat.enqueue_action(self.monster, technique, target)

    def _calculate_success_rate(self, riddle: Riddle) -> float:
        """
        Calculate the AI's success rate for answering a riddle.

        Parameters:
            riddle: The riddle to evaluate.

        Returns:
            Success rate between 0.0 and 1.0.
        """
        # Base success rate based on monster level
        level = self.monster.level
        base_rate = min(0.3 + (level * 0.02), 0.9)  # 30% to 90% based on level
        
        # Adjust based on riddle difficulty
        difficulty_modifiers = {
            "easy": 0.2,     # +20% for easy riddles
            "medium": 0.0,   # No modifier for medium
            "hard": -0.3     # -30% for hard riddles
        }
        
        difficulty_mod = difficulty_modifiers.get(riddle.difficulty, 0.0)
        
        # Adjust based on riddle category and monster type
        category_mod = self._get_category_modifier(riddle)
        
        # Calculate final success rate
        final_rate = base_rate + difficulty_mod + category_mod
        
        # Clamp between 0.1 and 0.95 (never 0% or 100%)
        return max(0.1, min(0.95, final_rate))

    def _get_category_modifier(self, riddle: Riddle) -> float:
        """
        Get success rate modifier based on riddle category and monster characteristics.

        Parameters:
            riddle: The riddle to evaluate.

        Returns:
            Modifier value between -0.2 and 0.2.
        """
        primary_type = self.monster.types.primary.slug if self.monster.types.primary else ""
        
        # Different monster types are better at different riddle categories
        type_bonuses = {
            "math": {
                "metal": 0.15,   # Metal types are logical
                "earth": 0.1,    # Earth types are steady
            },
            "logic": {
                "aether": 0.15,  # Aether types are mystical
                "water": 0.1,    # Water types are adaptable
            },
            "wordplay": {
                "wood": 0.15,    # Wood types are creative
                "fire": 0.1,     # Fire types are quick-thinking
            }
        }
        
        category_bonuses = type_bonuses.get(riddle.category, {})
        return category_bonuses.get(primary_type, 0.0)

    def get_riddle_difficulty_preference(self) -> str:
        """
        Get the AI's preferred riddle difficulty based on monster level.

        Returns:
            Preferred difficulty: easy, medium, or hard.
        """
        level = self.monster.level
        if level <= 10:
            return "easy"
        elif level <= 25:
            return "medium"
        else:
            return "hard"

    def simulate_riddle_answer(self, riddle: Riddle) -> bool:
        """
        Simulate the AI answering a riddle for testing purposes.

        Parameters:
            riddle: The riddle to answer.

        Returns:
            True if AI would answer correctly, False otherwise.
        """
        success_rate = self._calculate_success_rate(riddle)
        return random.random() < success_rate