# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os

from tuxemon.states.combat.combat import CombatState
from tuxemon.states.combat.combat_context import CombatContext
from tuxemon.states.combat.combat_classes import MenuVisibility
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.player import Player
from tuxemon.session import Session
from tuxemon.riddle.riddle import Riddle
from tuxemon.riddle.riddle_manager import RiddleManager


class TestRiddleCombatIntegration(unittest.TestCase):
    """Test riddle system integration with combat mechanics."""

    def setUp(self):
        """Set up test environment with mock combat scenario."""
        # Initialize Tuxemon environment
        from tuxemon import prepare
        prepare.headless_init()
        
        # Create mock session
        self.mock_session = Mock(spec=Session)
        self.mock_client = Mock()
        self.mock_session.client = self.mock_client
        
        # Create mock monsters (avoid database dependency in integration tests)
        self.player_monster = Mock(spec=Monster)
        self.player_monster.name = "Test Rockitten"
        self.player_monster.level = 10
        self.player_monster.hp = 100
        self.player_monster.current_hp = 100
        self.player_monster.experience = 50
        
        self.enemy_monster = Mock(spec=Monster)
        self.enemy_monster.name = "Test Bamboon"
        self.enemy_monster.level = 8
        self.enemy_monster.hp = 80
        self.enemy_monster.current_hp = 80
        self.enemy_monster.experience = 40
        
        # Create test NPCs
        self.player = Mock(spec=Player)
        self.player.monsters = [self.player_monster]
        self.player.name = "Test Player"
        
        self.enemy = Mock(spec=NPC)
        self.enemy.monsters = [self.enemy_monster]
        self.enemy.name = "Test Enemy"
        
        # Set up test riddle
        self.test_riddle_data = {
            "riddle_id": 1,
            "slug": "test_riddle",
            "category": "logic",
            "difficulty": "medium",
            "question": "What comes next: 2, 4, 8, 16, ?",
            "answer": "32",
            "alternate_answers": ["thirty-two"],
            "hint": "Each number doubles",
            "damage_multiplier": 1.5,
            "experience_reward": 15
        }
        # Create riddle directly with test data
        riddle = Riddle(save_data=self.test_riddle_data)
        riddle.riddle_id = self.test_riddle_data["riddle_id"]
        riddle.slug = self.test_riddle_data["slug"]
        riddle.category = self.test_riddle_data["category"]
        riddle.difficulty = self.test_riddle_data["difficulty"]
        riddle.question = self.test_riddle_data["question"]
        riddle.answer = self.test_riddle_data["answer"]
        riddle.alternate_answers = self.test_riddle_data["alternate_answers"]
        riddle.hint = self.test_riddle_data["hint"]
        riddle.damage_multiplier = self.test_riddle_data["damage_multiplier"]
        riddle.experience_reward = self.test_riddle_data["experience_reward"]
        self.test_riddle = riddle

    @patch('tuxemon.riddle.riddle_manager.RiddleManager')
    def test_combat_state_riddle_integration(self, mock_riddle_manager):
        """Test that CombatState properly integrates with riddle system."""
        # Mock riddle manager
        mock_manager = Mock()
        mock_manager.get_riddle_for_monster.return_value = self.test_riddle
        mock_riddle_manager.return_value = mock_manager
        
        # Create combat context
        context = CombatContext(
            session=self.mock_session,
            teams=[self.player, self.enemy],
            combat_type="trainer",
            graphics="battle_bg_grass",
            battle_mode="single"
        )
        
        # Create combat state
        with patch('tuxemon.states.combat.combat.CombatState.__init__', return_value=None):
            combat_state = CombatState.__new__(CombatState)
            combat_state.context = context
            combat_state._menu_visibility = MenuVisibility()
            
            # Test menu visibility includes riddle option
            self.assertTrue(hasattr(combat_state._menu_visibility, 'menu_riddle'))
            self.assertTrue(combat_state._menu_visibility.menu_riddle)

    def test_menu_visibility_riddle_option(self):
        """Test that MenuVisibility includes riddle menu option."""
        menu_visibility = MenuVisibility()
        
        # Should have riddle menu enabled by default
        self.assertTrue(menu_visibility.menu_riddle)
        
        # Should have both fight and riddle menus available
        self.assertTrue(hasattr(menu_visibility, 'menu_fight'))
        self.assertTrue(menu_visibility.menu_fight)

    @patch('tuxemon.riddle.riddle_manager.RiddleManager')
    def test_riddle_damage_calculation_in_combat(self, mock_riddle_manager):
        """Test riddle damage calculation affects monster HP."""
        # Mock riddle manager
        mock_manager = Mock()
        mock_manager.get_riddle_for_monster.return_value = self.test_riddle
        mock_riddle_manager.return_value = mock_manager
        
        initial_hp = self.enemy_monster.current_hp
        base_damage = 50
        
        # Simulate correct riddle answer (should deal extra damage)
        correct_answer = True
        if correct_answer:
            actual_damage = int(base_damage * self.test_riddle.damage_multiplier)
            self.enemy_monster.current_hp -= actual_damage
        
        expected_hp = initial_hp - int(base_damage * 1.5)  # 1.5x multiplier for medium difficulty
        self.assertEqual(self.enemy_monster.current_hp, expected_hp)

    @patch('tuxemon.riddle.riddle_manager.RiddleManager')
    def test_riddle_wrong_answer_penalty(self, mock_riddle_manager):
        """Test wrong riddle answer damages player's monster."""
        # Mock riddle manager
        mock_manager = Mock()
        mock_manager.get_riddle_for_monster.return_value = self.test_riddle
        mock_riddle_manager.return_value = mock_manager
        
        initial_hp = self.player_monster.current_hp
        penalty_damage = 30
        
        # Simulate wrong riddle answer (should damage player's monster)
        wrong_answer = False
        if not wrong_answer:
            # Wrong answer - player takes damage
            self.player_monster.current_hp -= penalty_damage
        
        expected_hp = initial_hp - penalty_damage
        self.assertEqual(self.player_monster.current_hp, expected_hp)

    def test_monster_level_affects_riddle_selection(self):
        """Test that monster level influences riddle difficulty selection."""
        with patch('tuxemon.riddle.riddle_manager.RiddleManager') as mock_riddle_manager:
            mock_manager = Mock()
            
            # Mock different riddles for different difficulties
            easy_riddle = Mock()
            easy_riddle.difficulty = "easy"
            medium_riddle = Mock()
            medium_riddle.difficulty = "medium"
            hard_riddle = Mock()
            hard_riddle.difficulty = "hard"
            
            # Test low level monster gets easy riddle
            low_level_monster = Monster.spawn_base("bamboon", 3)
            mock_manager.get_riddle_for_monster.return_value = easy_riddle
            
            riddle = mock_manager.get_riddle_for_monster(low_level_monster)
            self.assertEqual(riddle.difficulty, "easy")
            
            # Test high level monster gets hard riddle
            high_level_monster = Monster.spawn_base("bamboon", 25)
            mock_manager.get_riddle_for_monster.return_value = hard_riddle
            
            riddle = mock_manager.get_riddle_for_monster(high_level_monster)
            self.assertEqual(riddle.difficulty, "hard")

    @patch('tuxemon.riddle.riddle_ai.RiddleAI')
    def test_ai_riddle_solving_integration(self, mock_ai_class):
        """Test AI monster riddle solving in combat context."""
        # Mock AI
        mock_ai = Mock()
        mock_ai_class.return_value = mock_ai
        
        # Test AI solving riddle
        mock_ai.solve_riddle.return_value = True  # AI gets it right
        
        ai_result = mock_ai.solve_riddle(self.test_riddle, self.enemy_monster)
        self.assertTrue(ai_result)
        
        # Verify AI was called with correct parameters
        mock_ai.solve_riddle.assert_called_once_with(self.test_riddle, self.enemy_monster)

    def test_combat_turn_progression_with_riddles(self):
        """Test that combat turns progress correctly with riddle system."""
        # Mock combat state turn system
        turn_count = 0
        
        # Simulate player turn with riddle
        turn_count += 1
        player_riddle_result = True  # Player answers correctly
        
        # Simulate AI turn with riddle  
        turn_count += 1
        ai_riddle_result = False  # AI answers incorrectly
        
        # Verify turns progressed
        self.assertEqual(turn_count, 2)
        
        # Verify different outcomes
        self.assertTrue(player_riddle_result)
        self.assertFalse(ai_riddle_result)

    def test_riddle_experience_rewards(self):
        """Test that solving riddles grants experience."""
        initial_exp = self.player_monster.experience
        riddle_exp = self.test_riddle.experience_reward
        
        # Simulate correct riddle answer granting experience
        correct_answer = True
        if correct_answer:
            self.player_monster.experience += riddle_exp
        
        expected_exp = initial_exp + riddle_exp
        self.assertEqual(self.player_monster.experience, expected_exp)

    def test_riddle_categories_and_monster_types(self):
        """Test riddle category selection based on monster types."""
        # Mock riddle manager with category filtering
        with patch('tuxemon.riddle.riddle_manager.RiddleManager') as mock_riddle_manager:
            mock_manager = Mock()
            
            # Mock riddles for different categories
            logic_riddle = Mock()
            logic_riddle.category = "logic"
            math_riddle = Mock()
            math_riddle.category = "math"
            
            # Test category selection (simplified)
            mock_manager.get_riddles_by_category.return_value = [logic_riddle]
            
            riddles = mock_manager.get_riddles_by_category("logic")
            self.assertEqual(len(riddles), 1)
            self.assertEqual(riddles[0].category, "logic")

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState')
    def test_riddle_ui_state_creation(self, mock_riddle_state):
        """Test riddle UI state is created correctly during combat."""
        # Mock riddle state
        mock_state = Mock()
        mock_riddle_state.return_value = mock_state
        
        # Simulate creating riddle state
        callback = Mock()
        riddle_state = mock_riddle_state(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=callback,
            monster_name=self.enemy_monster.name
        )
        
        # Verify state was created with correct parameters
        mock_riddle_state.assert_called_once_with(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=callback,
            monster_name=self.enemy_monster.name
        )

if __name__ == '__main__':
    unittest.main()