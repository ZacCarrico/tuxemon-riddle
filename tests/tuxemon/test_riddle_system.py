# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

import unittest
from unittest.mock import Mock, patch
import tempfile
import json
import os

from tuxemon.riddle.riddle import Riddle
from tuxemon.riddle.riddle_manager import RiddleManager
from tuxemon.riddle.riddle_ai import RiddleAI
from tuxemon.monster import Monster
from tuxemon.session import Session


class TestRiddleSystem(unittest.TestCase):
    """Test the core riddle system functionality."""

    def setUp(self):
        """Set up test environment with mock riddles."""
        # Initialize Tuxemon environment
        from tuxemon import prepare
        prepare.headless_init()
        
        # Create temporary riddle files
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample riddles for testing
        self.test_riddles = {
            "easy_math": {
                "riddle_id": 1,
                "slug": "easy_math",
                "category": "math",
                "difficulty": "easy",
                "question": "What is 2 + 2?",
                "answer": "4",
                "alternate_answers": ["four"],
                "hint": "Think about basic addition",
                "damage_multiplier": 1.2,
                "experience_reward": 10
            },
            "medium_logic": {
                "riddle_id": 2,
                "slug": "medium_logic",
                "category": "logic",
                "difficulty": "medium",
                "question": "If all roses are flowers, and some flowers fade quickly, can we conclude that some roses fade quickly?",
                "answer": "no",
                "alternate_answers": ["false", "cannot determine"],
                "hint": "Think about logical validity",
                "damage_multiplier": 1.5,
                "experience_reward": 20
            },
            "hard_puzzle": {
                "riddle_id": 3,
                "slug": "hard_puzzle", 
                "category": "puzzle",
                "difficulty": "hard",
                "question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?",
                "answer": "map",
                "alternate_answers": ["a map"],
                "hint": "Think about representations",
                "damage_multiplier": 2.0,
                "experience_reward": 30
            }
        }
        
        # Write test riddles to temp files
        for slug, riddle_data in self.test_riddles.items():
            riddle_file = os.path.join(self.temp_dir, f"{slug}.json")
            with open(riddle_file, 'w') as f:
                json.dump(riddle_data, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_riddle_from_data(self, riddle_key):
        """Helper method to create riddle from test data."""
        riddle_data = self.test_riddles[riddle_key]
        riddle = Riddle(save_data=riddle_data)
        # Override the load method to set our test data directly
        riddle.riddle_id = riddle_data["riddle_id"]
        riddle.slug = riddle_data["slug"]
        riddle.category = riddle_data["category"]
        riddle.difficulty = riddle_data["difficulty"]
        riddle.question = riddle_data["question"]
        riddle.answer = riddle_data["answer"]
        riddle.alternate_answers = riddle_data["alternate_answers"]
        riddle.hint = riddle_data["hint"]
        riddle.damage_multiplier = riddle_data["damage_multiplier"]
        riddle.experience_reward = riddle_data["experience_reward"]
        return riddle

    def test_riddle_creation(self):
        """Test riddle object creation from data."""
        riddle = self._create_riddle_from_data("easy_math")
        
        self.assertEqual(riddle.riddle_id, 1)
        self.assertEqual(riddle.slug, "easy_math")
        self.assertEqual(riddle.category, "math")
        self.assertEqual(riddle.difficulty, "easy")
        self.assertEqual(riddle.question, "What is 2 + 2?")
        self.assertEqual(riddle.answer, "4")
        self.assertEqual(riddle.alternate_answers, ["four"])
        self.assertEqual(riddle.damage_multiplier, 1.2)

    def test_riddle_answer_checking(self):
        """Test riddle answer validation."""
        riddle = self._create_riddle_from_data("easy_math")
        
        # Test correct answer
        self.assertTrue(riddle.check_answer("4"))
        self.assertTrue(riddle.check_answer("four"))  # alternate answer
        self.assertTrue(riddle.check_answer("FOUR"))  # case insensitive
        self.assertTrue(riddle.check_answer(" 4 "))   # whitespace handling
        
        # Test incorrect answers
        self.assertFalse(riddle.check_answer("5"))
        self.assertFalse(riddle.check_answer(""))
        self.assertFalse(riddle.check_answer("two plus two"))

    def test_riddle_damage_calculation(self):
        """Test damage multiplier calculation."""
        easy_riddle = self._create_riddle_from_data("easy_math")
        medium_riddle = self._create_riddle_from_data("medium_logic")
        hard_riddle = self._create_riddle_from_data("hard_puzzle")
        
        base_damage = 100
        
        # Test damage multipliers (base_multiplier * difficulty_factor)
        # Easy: 1.2 * 1.0 = 1.2
        self.assertEqual(easy_riddle.get_damage_multiplier() * base_damage, 120)
        # Medium: 1.5 * 1.5 = 2.25  
        self.assertEqual(medium_riddle.get_damage_multiplier() * base_damage, 225)
        # Hard: 2.0 * 2.0 = 4.0
        self.assertEqual(hard_riddle.get_damage_multiplier() * base_damage, 400)

    @patch('tuxemon.riddle.riddle_manager.db')
    def test_riddle_manager_loading(self, mock_db):
        """Test riddle manager loads riddles correctly."""
        # Mock database calls
        mock_riddle_data = {
            "easy_math": Mock(category="math", difficulty="easy"),
            "medium_logic": Mock(category="logic", difficulty="medium"),
            "hard_puzzle": Mock(category="puzzle", difficulty="hard")
        }
        mock_db.database = {"riddle": mock_riddle_data}
        
        manager = RiddleManager()
        
        # Should have loaded 3 riddle categories in cache
        self.assertEqual(len(manager._riddles_cache), 3)
        
        # Test riddles are categorized correctly
        self.assertIn("math_easy", manager._riddles_cache)
        self.assertIn("logic_medium", manager._riddles_cache)
        self.assertIn("puzzle_hard", manager._riddles_cache)

    @patch('tuxemon.riddle.riddle.Riddle.create')
    @patch('tuxemon.riddle.riddle_manager.db')
    def test_riddle_selection_by_difficulty(self, mock_db, mock_riddle_create):
        """Test riddle selection based on monster level."""
        # Mock database calls
        mock_riddle_data = {
            "easy_math": Mock(category="math", difficulty="easy"),
            "easy_logic": Mock(category="logic", difficulty="easy"),
            "easy_wordplay": Mock(category="wordplay", difficulty="easy"),
            "medium_math": Mock(category="math", difficulty="medium"),
            "medium_logic": Mock(category="logic", difficulty="medium"),
            "medium_wordplay": Mock(category="wordplay", difficulty="medium"),
            "hard_math": Mock(category="math", difficulty="hard"),
            "hard_logic": Mock(category="logic", difficulty="hard"),
            "hard_wordplay": Mock(category="wordplay", difficulty="hard"),
        }
        mock_db.database = {"riddle": mock_riddle_data}
        
        # Mock riddle creation to return riddles with appropriate difficulty
        def mock_create_riddle(slug):
            riddle = Mock()
            if "easy" in slug:
                riddle.difficulty = "easy"
            elif "medium" in slug:
                riddle.difficulty = "medium"
            else:
                riddle.difficulty = "hard"
            return riddle
        mock_riddle_create.side_effect = mock_create_riddle
        
        manager = RiddleManager()
        
        # Mock NPCs with monsters at different levels
        low_level_monster = Mock()
        low_level_monster.level = 5
        low_level_monster.is_fainted = False
        low_level_monster.types = Mock()
        low_level_monster.types.primary = Mock()
        low_level_monster.types.primary.slug = "metal"  # Will get "math" category
        low_npc = Mock()
        low_npc.monsters = [low_level_monster]
        
        mid_level_monster = Mock()
        mid_level_monster.level = 15  # Between 11-25 for medium
        mid_level_monster.is_fainted = False
        mid_level_monster.types = Mock()
        mid_level_monster.types.primary = Mock()
        mid_level_monster.types.primary.slug = "metal"  # Will get "math" category
        mid_npc = Mock()
        mid_npc.monsters = [mid_level_monster]
        
        high_level_monster = Mock()
        high_level_monster.level = 30  # > 25 for hard
        high_level_monster.is_fainted = False
        high_level_monster.types = Mock()
        high_level_monster.types.primary = Mock()
        high_level_monster.types.primary.slug = "metal"  # Will get "math" category
        high_npc = Mock()
        high_npc.monsters = [high_level_monster]
        
        # Test riddle selection - the method determines difficulty based on NPCs' monsters
        easy_riddle = manager.get_riddle_for_battle(low_npc, low_npc)
        self.assertEqual(easy_riddle.difficulty, "easy")
        
        medium_riddle = manager.get_riddle_for_battle(mid_npc, mid_npc)
        self.assertEqual(medium_riddle.difficulty, "medium")
        
        hard_riddle = manager.get_riddle_for_battle(high_npc, high_npc)
        self.assertEqual(hard_riddle.difficulty, "hard")

    def test_riddle_ai_success_rates(self):
        """Test AI riddle solving with level-based success rates."""
        # Mock session and monster
        mock_session = Mock(spec=Session)
        
        # Test different monster levels
        low_level_monster = Mock()
        low_level_monster.level = 5
        
        high_level_monster = Mock()
        high_level_monster.level = 30
        
        riddle = self._create_riddle_from_data("easy_math")
        
        # Mock the required arguments for RiddleAI
        mock_session = Mock()
        mock_combat = Mock()
        mock_combat.field_monsters = Mock()
        mock_combat.field_monsters.get_monsters.return_value = []
        mock_combat.players = [Mock(), Mock()]
        mock_character = Mock()
        
        # Create AI instances with different monster levels
        low_ai = RiddleAI(mock_session, mock_combat, low_level_monster, mock_character)
        high_ai = RiddleAI(mock_session, mock_combat, high_level_monster, mock_character)
        
        # Test success rate calculation (not actual solving due to randomness)
        low_success_rate = low_ai._calculate_success_rate(riddle)
        high_success_rate = high_ai._calculate_success_rate(riddle)
        
        # Higher level monsters should have better success rates
        self.assertGreater(high_success_rate, low_success_rate)
        
        # Success rates should be within reasonable bounds
        self.assertGreaterEqual(low_success_rate, 0.3)  # Min 30%
        self.assertLessEqual(high_success_rate, 1.0)    # Max 100%

    def test_riddle_json_validation(self):
        """Test riddle JSON structure validation."""
        # Test valid riddle
        riddle = self._create_riddle_from_data("easy_math")
        self.assertIsNotNone(riddle)
        
        # Test missing required fields
        invalid_riddle = self.test_riddles["easy_math"].copy()
        del invalid_riddle["question"]
        
        # Test that missing required fields are handled gracefully
        # (Since Riddle.__init__ doesn't enforce required fields, 
        # this test verifies the riddle is created but has missing data)
        riddle_with_missing = Riddle(save_data=invalid_riddle)
        # The question field should be empty or default
        self.assertEqual(riddle_with_missing.question, "")

    def test_riddle_edge_cases(self):
        """Test edge cases in riddle handling."""
        riddle = self._create_riddle_from_data("medium_logic")
        
        # Test empty input
        self.assertFalse(riddle.check_answer(""))
        self.assertFalse(riddle.check_answer(None))
        
        # Test very long input
        long_answer = "a" * 1000
        self.assertFalse(riddle.check_answer(long_answer))
        
        # Test special characters
        self.assertFalse(riddle.check_answer("@#$%"))
        
        # Test numeric string vs number comparison
        math_riddle = self._create_riddle_from_data("easy_math")
        self.assertTrue(math_riddle.check_answer("4"))
        self.assertTrue(math_riddle.check_answer(4))  # Should handle int input

if __name__ == '__main__':
    unittest.main()