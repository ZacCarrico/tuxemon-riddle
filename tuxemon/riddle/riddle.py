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
        Check if the user's answer is correct with fuzzy matching.

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
        if not user_answer:
            return False
        
        # Collect all possible correct answers
        all_correct_answers = [self.answer.strip().lower()]
        all_correct_answers.extend([alt.strip().lower() for alt in self.alternate_answers if alt])
        
        # Check each possible answer
        for correct_answer in all_correct_answers:
            if self._is_answer_match(user_answer, correct_answer):
                return True
                
        return False

    def _is_answer_match(self, user_answer: str, correct_answer: str) -> bool:
        """
        Check if user answer matches correct answer using fuzzy matching.
        
        Parameters:
            user_answer: The user's answer (normalized).
            correct_answer: The correct answer (normalized).
            
        Returns:
            True if answers match with tolerance.
        """
        # Exact match
        if user_answer == correct_answer:
            return True
        
        # Check common number word variations
        if self._check_number_variations(user_answer, correct_answer):
            return True
            
        # Check partial word matching for multi-word answers
        if self._check_partial_word_match(user_answer, correct_answer):
            return True
            
        # Check edit distance for typos (allow 1-2 character differences)
        if self._check_edit_distance(user_answer, correct_answer):
            return True
            
        return False
    
    def _check_number_variations(self, user_answer: str, correct_answer: str) -> bool:
        """Check if answers are equivalent number representations."""
        # Common number word mappings
        number_words = {
            '0': ['zero', 'nothing', 'none'],
            '1': ['one', 'first'],
            '2': ['two', 'second'],
            '3': ['three', 'third'],
            '4': ['four', 'fourth'],
            '5': ['five', 'fifth'],
            '6': ['six', 'sixth'],
            '7': ['seven', 'seventh'],
            '8': ['eight', 'eighth'],
            '9': ['nine', 'ninth'],
            '10': ['ten', 'tenth'],
            '11': ['eleven', 'eleventh'],
            '12': ['twelve', 'twelfth'],
            '13': ['thirteen', 'thirteenth'],
            '14': ['fourteen', 'fourteenth'],
            '15': ['fifteen', 'fifteenth'],
            '16': ['sixteen', 'sixteenth'],
            '17': ['seventeen', 'seventeenth'],
            '18': ['eighteen', 'eighteenth'],
            '19': ['nineteen', 'nineteenth'],
            '20': ['twenty', 'twentieth']
        }
        
        # Check if one is digit and other is word form
        for digit, words in number_words.items():
            if (user_answer == digit and correct_answer in words) or \
               (user_answer in words and correct_answer == digit):
                return True
                
        return False
    
    def _check_partial_word_match(self, user_answer: str, correct_answer: str) -> bool:
        """Check if significant words from the answer are present."""
        user_words = set(user_answer.split())
        correct_words = set(correct_answer.split())
        
        # Ignore common words that don't add meaning
        ignore_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but'}
        
        significant_correct_words = {word for word in correct_words if len(word) > 2 and word not in ignore_words}
        significant_user_words = {word for word in user_words if len(word) > 2 and word not in ignore_words}
        
        # For answers with only articles/small words (like "a map"), be very strict
        if not significant_correct_words:
            # For phrases like "a map", require exact word match - no partial matching
            return False
            
        # For single significant word answers, be stricter
        if len(significant_correct_words) == 1:
            # If the original answer has multiple words (like "a map"), don't allow partial matching
            # This prevents "map" from matching "a map"
            if len(correct_words) > 1:
                return False
            # Only allow partial matching for true single-word answers
            return significant_correct_words.issubset(significant_user_words)
            
        # For multi-word answers, check if user got most key words
        matches = len(significant_correct_words.intersection(significant_user_words))
        return matches >= max(1, len(significant_correct_words) * 0.6)  # Increased to 60% for better accuracy
    
    def _check_edit_distance(self, user_answer: str, correct_answer: str) -> bool:
        """Check if answers are close using Levenshtein distance."""
        def levenshtein_distance(s1: str, s2: str) -> int:
            """Calculate Levenshtein distance between two strings."""
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(user_answer, correct_answer)
        user_len = len(user_answer)
        correct_len = len(correct_answer)
        min_len = min(user_len, correct_len)
        max_len = max(user_len, correct_len)
        
        # Be stricter with single digit/character answers - no typos allowed for numbers
        if max_len <= 1:
            return False
            
        # For single digits that are actually numbers, be very strict
        if correct_answer.isdigit() and correct_len == 1:
            return False
            
        # For very short answers (both strings 4 chars or less), be very selective
        if max_len <= 4:
            # Allow distance 1 only if lengths are same
            if distance == 1:
                return user_len == correct_len
            elif distance == 2:
                # Only allow distance 2 if both strings are at least 3 chars and same length
                return min_len >= 3 and user_len == correct_len
            else:
                return False
        elif max_len <= 10:
            # For medium length, allow more flexibility but still consider length differences
            if abs(user_len - correct_len) > 2:
                return False  # Don't allow big length differences
            
            # Be stricter with extensions of short words (like four -> foura)
            if min_len <= 4 and abs(user_len - correct_len) > 0:
                # Only allow same-length typos for short words, not extensions
                return False
                
            return distance <= 2
        else:
            # For very long answers, allow up to 15% character differences
            return distance <= max(2, max_len * 0.15)

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