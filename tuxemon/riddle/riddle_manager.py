# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Optional

from tuxemon.db import db
from tuxemon.riddle.riddle import Riddle

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class RiddleManager:
    """
    Manages riddle selection and difficulty scaling for combat.
    """

    def __init__(self) -> None:
        self._riddles_cache: dict[str, list[str]] = {}
        self._load_riddles_cache()

    def _load_riddles_cache(self) -> None:
        """Load all riddles and organize them by category and difficulty."""
        try:
            # Ensure database is loaded
            if not hasattr(db, 'database') or not db.database:
                logger.warning("Database not loaded, attempting to load now...")
                try:
                    db.load()
                except Exception as db_error:
                    logger.error(f"Failed to load database: {db_error}")
                    self._create_fallback_cache()
                    return
            
            # Get all riddle slugs from the database
            riddle_data = db.database.get("riddle", {})
            
            if not riddle_data:
                logger.warning("No riddle data found in database, using fallback cache")
                self._create_fallback_cache()
                return
            
            for slug, riddle_model in riddle_data.items():
                try:
                    category = riddle_model.category
                    difficulty = riddle_model.difficulty
                    key = f"{category}_{difficulty}"
                    
                    if key not in self._riddles_cache:
                        self._riddles_cache[key] = []
                    self._riddles_cache[key].append(slug)
                except AttributeError as attr_error:
                    logger.warning(f"Riddle {slug} missing required attributes: {attr_error}")
                    continue
                
            logger.info(f"Loaded {len(self._riddles_cache)} riddle categories with {sum(len(riddles) for riddles in self._riddles_cache.values())} total riddles")
                
        except Exception as e:
            logger.error(f"Failed to load riddles cache: {e}")
            self._create_fallback_cache()
    
    def _create_fallback_cache(self) -> None:
        """Create a basic fallback cache when database loading fails."""
        logger.info("Creating fallback riddle cache")
        self._riddles_cache = {
            "math_easy": ["math_easy_01", "math_easy_02"],
            "logic_easy": ["logic_easy_01"],
            "wordplay_easy": ["wordplay_easy_01"],
            "color_hard": ["color_hard_01"],
            "sequence_medium": ["sequence_medium_01"],
            "time_easy": ["time_easy_01"]
        }

    def get_random_riddle(
        self, 
        category: Optional[str] = None, 
        difficulty: Optional[str] = None,
        monster: Optional[Monster] = None
    ) -> Riddle:
        """
        Get a random riddle based on criteria.

        Parameters:
            category: Specific category to choose from (math, logic, wordplay, etc.)
            difficulty: Specific difficulty (easy, medium, hard)
            monster: Monster for determining appropriate difficulty

        Returns:
            A random riddle matching the criteria.
        """
        # Auto-determine difficulty based on monster level if not specified
        if difficulty is None and monster is not None:
            difficulty = self._get_difficulty_for_monster(monster)
            
        # Auto-determine category based on monster type if not specified
        if category is None and monster is not None:
            category = self._get_category_for_monster(monster)
            
        # Get available riddles
        available_riddles = self._get_available_riddles(category, difficulty)
        
        if not available_riddles:
            # Fallback to any available riddle
            logger.warning(f"No riddles found for category={category}, difficulty={difficulty}")
            available_riddles = self._get_all_available_riddles()
            
        if not available_riddles:
            # Ultimate fallback - create a simple math riddle
            logger.error("No riddles available at all! Creating fallback riddle.")
            return self._create_fallback_riddle()
            
        # Select random riddle
        slug = random.choice(available_riddles)
        try:
            return Riddle.create(slug)
        except Exception as e:
            logger.error(f"Failed to create riddle from slug '{slug}': {e}")
            return self._create_fallback_riddle()

    def _get_difficulty_for_monster(self, monster: Monster) -> str:
        """
        Determine appropriate riddle difficulty based on monster level.

        Parameters:
            monster: The monster to determine difficulty for.

        Returns:
            Difficulty string: easy, medium, or hard.
        """
        level = monster.level
        if level <= 10:
            return "easy"
        elif level <= 25:
            return "medium"
        else:
            return "hard"

    def _get_category_for_monster(self, monster: Monster) -> str:
        """
        Determine appropriate riddle category based on monster characteristics.

        Parameters:
            monster: The monster to determine category for.

        Returns:
            Category string.
        """
        # Simple mapping based on monster types or names
        # This could be expanded with more sophisticated logic
        primary_type = monster.types.primary.slug if monster.types.primary else ""
        
        if primary_type in ["metal", "earth"]:
            return "math"  # Logical, structured types get math
        elif primary_type in ["aether", "wood"]:
            return "logic"  # Mystical types get logic puzzles
        else:
            return random.choice(["math", "logic", "wordplay"])

    def _get_available_riddles(
        self, 
        category: Optional[str] = None, 
        difficulty: Optional[str] = None
    ) -> list[str]:
        """
        Get list of available riddle slugs matching criteria.

        Parameters:
            category: Optional category filter.
            difficulty: Optional difficulty filter.

        Returns:
            List of riddle slugs.
        """
        # Refresh cache if empty
        if not self._riddles_cache:
            self._load_riddles_cache()
        if category and difficulty:
            key = f"{category}_{difficulty}"
            return self._riddles_cache.get(key, [])
        elif category:
            # Get all difficulties for this category
            riddles = []
            for key, slug_list in self._riddles_cache.items():
                if key.startswith(f"{category}_"):
                    riddles.extend(slug_list)
            return riddles
        elif difficulty:
            # Get all categories for this difficulty
            riddles = []
            for key, slug_list in self._riddles_cache.items():
                if key.endswith(f"_{difficulty}"):
                    riddles.extend(slug_list)
            return riddles
        else:
            return self._get_all_available_riddles()

    def _get_all_available_riddles(self) -> list[str]:
        """Get all available riddle slugs."""
        all_riddles = []
        for slug_list in self._riddles_cache.values():
            all_riddles.extend(slug_list)
        return all_riddles

    def _create_fallback_riddle(self) -> Riddle:
        """
        Create a simple fallback riddle when none are available.

        Returns:
            A basic math riddle.
        """
        # Create a simple riddle in memory
        riddle = Riddle()
        riddle.riddle_id = 999
        riddle.category = "math"
        riddle.difficulty = "easy"
        riddle.question = "What is 2 + 2?"
        riddle.answer = "4"
        riddle.alternate_answers = ["four"]
        riddle.hint = "Count on your fingers!"
        riddle.damage_multiplier = 1.0
        riddle.experience_reward = 5
        riddle.slug = "fallback_riddle"
        riddle.tags = ["fallback", "math"]
        riddle.name = "Simple Math"
        riddle.description = "A simple addition problem"
        return riddle

    def get_riddle_by_difficulty(self, difficulty: str) -> Riddle:
        """
        Get a random riddle of specific difficulty.

        Parameters:
            difficulty: The difficulty level.

        Returns:
            A riddle of the specified difficulty.
        """
        return self.get_random_riddle(difficulty=difficulty)

    def get_riddle_by_category(self, category: str) -> Riddle:
        """
        Get a random riddle of specific category.

        Parameters:
            category: The riddle category.

        Returns:
            A riddle of the specified category.
        """
        return self.get_random_riddle(category=category)

    def get_riddle_for_battle(self, player: NPC, opponent: NPC) -> Riddle:
        """
        Get an appropriate riddle for a battle between two NPCs.

        Parameters:
            player: The player NPC.
            opponent: The opponent NPC.

        Returns:
            An appropriate riddle for the battle.
        """
        try:
            # Use the player's active monster to determine riddle difficulty
            active_monster = None
            if player and hasattr(player, 'monsters') and player.monsters:
                # Find the first non-fainted monster
                for monster in player.monsters:
                    if hasattr(monster, 'is_fainted') and not monster.is_fainted:
                        active_monster = monster
                        break
                        
            if active_monster is None and player and hasattr(player, 'monsters') and player.monsters:
                # Fallback to first monster
                active_monster = player.monsters[0]
                
            return self.get_random_riddle(monster=active_monster)
        except Exception as e:
            logger.error(f"Error in get_riddle_for_battle: {e}")
            # Return fallback riddle
            return self._create_fallback_riddle()

    def reload_riddles(self) -> None:
        """Reload the riddles cache from the database."""
        self._riddles_cache.clear()
        self._load_riddles_cache()


# Global riddle manager instance
riddle_manager = RiddleManager()