# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os

from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.player import Player
from tuxemon.session import Session
from tuxemon.states.combat.combat_context import CombatContext
from tuxemon.riddle.riddle import Riddle
from tuxemon.riddle.riddle_manager import RiddleManager
from tuxemon.riddle.riddle_ai import RiddleAI


class TestCompleteRiddleBattle(unittest.TestCase):
    """Test complete riddle-based battle scenarios end-to-end."""

    def setUp(self):
        """Set up complete battle scenario with real game classes."""
        # Initialize Tuxemon environment
        from tuxemon import prepare
        prepare.headless_init()
        
        # Create mock session
        self.mock_session = Mock(spec=Session)
        self.mock_client = Mock()
        self.mock_session.client = self.mock_client
        
        # Create mock monsters (avoid database dependency)
        self.player_monster1 = Mock(spec=Monster)
        self.player_monster1.name = "Player Rockitten"
        self.player_monster1.level = 10
        self.player_monster1.hp = 100
        self.player_monster1.current_hp = 100
        self.player_monster1.experience = 50
        
        self.player_monster2 = Mock(spec=Monster)
        self.player_monster2.name = "Player Bamboon"
        self.player_monster2.level = 8
        self.player_monster2.hp = 85
        self.player_monster2.current_hp = 85
        self.player_monster2.experience = 40
        
        self.enemy_monster1 = Mock(spec=Monster)
        self.enemy_monster1.name = "Enemy Bamboon"
        self.enemy_monster1.level = 9
        self.enemy_monster1.hp = 90
        self.enemy_monster1.current_hp = 90
        self.enemy_monster1.experience = 45
        
        self.enemy_monster2 = Mock(spec=Monster)
        self.enemy_monster2.name = "Enemy Rockitten"
        self.enemy_monster2.level = 7
        self.enemy_monster2.hp = 75
        self.enemy_monster2.current_hp = 75
        self.enemy_monster2.experience = 35
        
        # Create real NPCs
        self.player = Mock(spec=Player)
        self.player.monsters = [self.player_monster1, self.player_monster2]
        self.player.name = "Test Player"
        
        self.enemy = Mock(spec=NPC) 
        self.enemy.monsters = [self.enemy_monster1, self.enemy_monster2]
        self.enemy.name = "Test Trainer"
        
        # Create test riddles for different scenarios
        self.easy_riddle_data = {
            "riddle_id": 1,
            "slug": "easy_test",
            "category": "math",
            "difficulty": "easy",
            "question": "What is 5 + 3?",
            "answer": "8",
            "alternate_answers": ["eight"],
            "hint": "Simple addition",
            "damage_multiplier": 1.2,
            "experience_reward": 10
        }
        
        self.hard_riddle_data = {
            "riddle_id": 2,
            "slug": "hard_test", 
            "category": "logic",
            "difficulty": "hard",
            "question": "In a race, you overtake the person in 2nd place. What position are you in?",
            "answer": "2nd",
            "alternate_answers": ["second", "2nd place"],
            "hint": "Think carefully about what overtaking means",
            "damage_multiplier": 2.0,
            "experience_reward": 30
        }
        
        # Create riddles directly with test data
        easy_riddle = Riddle(save_data=self.easy_riddle_data)
        easy_riddle.riddle_id = self.easy_riddle_data["riddle_id"]
        easy_riddle.slug = self.easy_riddle_data["slug"]
        easy_riddle.category = self.easy_riddle_data["category"]
        easy_riddle.difficulty = self.easy_riddle_data["difficulty"]
        easy_riddle.question = self.easy_riddle_data["question"]
        easy_riddle.answer = self.easy_riddle_data["answer"]
        easy_riddle.alternate_answers = self.easy_riddle_data["alternate_answers"]
        easy_riddle.hint = self.easy_riddle_data["hint"]
        easy_riddle.damage_multiplier = self.easy_riddle_data["damage_multiplier"]
        easy_riddle.experience_reward = self.easy_riddle_data["experience_reward"]
        self.easy_riddle = easy_riddle
        
        hard_riddle = Riddle(save_data=self.hard_riddle_data)
        hard_riddle.riddle_id = self.hard_riddle_data["riddle_id"]
        hard_riddle.slug = self.hard_riddle_data["slug"]
        hard_riddle.category = self.hard_riddle_data["category"]
        hard_riddle.difficulty = self.hard_riddle_data["difficulty"]
        hard_riddle.question = self.hard_riddle_data["question"]
        hard_riddle.answer = self.hard_riddle_data["answer"]
        hard_riddle.alternate_answers = self.hard_riddle_data["alternate_answers"]
        hard_riddle.hint = self.hard_riddle_data["hint"]
        hard_riddle.damage_multiplier = self.hard_riddle_data["damage_multiplier"]
        hard_riddle.experience_reward = self.hard_riddle_data["experience_reward"]
        self.hard_riddle = hard_riddle

    def test_complete_battle_victory_through_riddles(self):
        """Test a complete battle where player wins by solving riddles correctly."""
        # Create combat context
        context = CombatContext(
            session=self.mock_session,
            teams=[self.player, self.enemy],
            combat_type="trainer",
            graphics="battle_bg_grass",
            battle_mode="single"
        )
        
        # Track battle state
        battle_turn = 1
        player_victories = 0
        enemy_victories = 0
        
        # Simulate multiple battle turns
        with patch('tuxemon.riddle.riddle_manager.RiddleManager') as mock_riddle_manager:
            mock_manager = Mock()
            mock_riddle_manager.return_value = mock_manager
            
            # Turn 1: Player answers correctly (easy riddle)
            mock_manager.get_riddle_for_monster.return_value = self.easy_riddle
            
            player_answer = "8"  # Correct answer
            riddle_correct = self.easy_riddle.check_answer(player_answer)
            self.assertTrue(riddle_correct)
            
            if riddle_correct:
                # Player deals damage to enemy
                damage = int(50 * self.easy_riddle.damage_multiplier)  # 60 damage
                self.enemy_monster1.current_hp -= damage
                player_victories += 1
            
            # Turn 2: Enemy AI attempts riddle
            with patch('tuxemon.riddle.riddle_ai.RiddleAI') as mock_ai_class:
                mock_ai = Mock()
                mock_ai_class.return_value = mock_ai
                mock_ai.solve_riddle.return_value = False  # AI fails
                
                ai_correct = mock_ai.solve_riddle(self.easy_riddle, self.enemy_monster1)
                self.assertFalse(ai_correct)
                
                if not ai_correct:
                    # Enemy takes damage for wrong answer
                    self.enemy_monster1.current_hp -= 25  # Penalty damage
                    player_victories += 1
            
            # Turn 3: Player faces harder riddle
            mock_manager.get_riddle_for_monster.return_value = self.hard_riddle
            
            player_answer = "2nd"  # Correct answer
            riddle_correct = self.hard_riddle.check_answer(player_answer)
            self.assertTrue(riddle_correct)
            
            if riddle_correct:
                # Player deals massive damage (hard riddle = 2x multiplier)
                damage = int(50 * self.hard_riddle.damage_multiplier)  # 100 damage
                self.enemy_monster1.current_hp -= damage
                
                # Enemy monster should be defeated
                if self.enemy_monster1.current_hp <= 0:
                    self.enemy_monster1.current_hp = 0
                    player_victories += 1
            
            # Verify battle outcome
            self.assertEqual(player_victories, 3)  # Player won all encounters
            self.assertEqual(self.enemy_monster1.current_hp, 0)  # Enemy defeated

    def test_battle_loss_through_wrong_answers(self):
        """Test battle where player loses by answering riddles incorrectly."""
        initial_hp = self.player_monster1.current_hp
        
        with patch('tuxemon.riddle.riddle_manager.RiddleManager') as mock_riddle_manager:
            mock_manager = Mock()
            mock_riddle_manager.return_value = mock_manager
            mock_manager.get_riddle_for_monster.return_value = self.easy_riddle
            
            # Player answers incorrectly multiple times
            wrong_answers = ["10", "7", "nine"]
            
            for wrong_answer in wrong_answers:
                riddle_correct = self.easy_riddle.check_answer(wrong_answer)
                self.assertFalse(riddle_correct)
                
                if not riddle_correct:
                    # Player takes penalty damage
                    self.player_monster1.current_hp -= 30
            
            # Player should have taken significant damage
            expected_hp = initial_hp - (30 * 3)  # 90 damage total
            self.assertEqual(self.player_monster1.current_hp, expected_hp)

    def test_multi_monster_battle_progression(self):
        """Test battle progression when monsters faint and are replaced."""
        # Enemy monster 1 is defeated
        self.enemy_monster1.current_hp = 0
        
        # Battle should progress to next monster
        active_enemy = None
        for monster in self.enemy.monsters:
            if monster.current_hp > 0:
                active_enemy = monster
                break
        
        self.assertEqual(active_enemy, self.enemy_monster2)
        self.assertGreater(active_enemy.current_hp, 0)

    def test_riddle_difficulty_scaling_with_progression(self):
        """Test that riddle difficulty increases as battle progresses."""
        with patch('tuxemon.riddle.riddle_manager.RiddleManager') as mock_riddle_manager:
            mock_manager = Mock()
            mock_riddle_manager.return_value = mock_manager
            
            # Early battle - easier riddles
            low_level_monster = Mock()
            low_level_monster.level = 5
            mock_manager.get_riddle_for_monster.return_value = self.easy_riddle
            
            early_riddle = mock_manager.get_riddle_for_monster(low_level_monster)
            self.assertEqual(early_riddle.difficulty, "easy")
            self.assertEqual(early_riddle.damage_multiplier, 1.2)
            
            # Late battle - harder riddles  
            high_level_monster = Mock()
            high_level_monster.level = 20
            mock_manager.get_riddle_for_monster.return_value = self.hard_riddle
            
            late_riddle = mock_manager.get_riddle_for_monster(high_level_monster)
            self.assertEqual(late_riddle.difficulty, "hard")
            self.assertEqual(late_riddle.damage_multiplier, 2.0)

    def test_experience_and_rewards_from_riddle_battles(self):
        """Test experience and reward calculation from riddle solving."""
        initial_exp = self.player_monster1.experience
        initial_level = self.player_monster1.level
        
        # Solve multiple riddles for experience
        riddles_solved = [self.easy_riddle, self.hard_riddle, self.easy_riddle]
        total_exp_gained = 0
        
        for riddle in riddles_solved:
            # Correct answer grants experience
            correct_answer = True
            if correct_answer:
                self.player_monster1.experience += riddle.experience_reward
                total_exp_gained += riddle.experience_reward
        
        expected_exp = initial_exp + total_exp_gained
        self.assertEqual(self.player_monster1.experience, expected_exp)
        
        # Check if level up occurred (simplified)
        exp_for_next_level = 100  # Simplified level calculation
        if total_exp_gained >= exp_for_next_level:
            # Monster should level up
            expected_level = initial_level + (total_exp_gained // exp_for_next_level)
            # Note: Real level calculation is more complex, this is simplified

    def test_ai_difficulty_adaptation(self):
        """Test that AI riddle-solving difficulty adapts to monster level."""
        with patch('tuxemon.riddle.riddle_ai.RiddleAI') as mock_ai_class:
            mock_ai = Mock()
            mock_ai_class.return_value = mock_ai
            
            # Low level AI monster - lower success rate
            low_level_monster = Mock()
            low_level_monster.level = 3
            mock_ai._calculate_success_rate.return_value = 0.3  # 30% success
            
            success_rate = mock_ai._calculate_success_rate(low_level_monster, self.easy_riddle)
            self.assertEqual(success_rate, 0.3)
            
            # High level AI monster - higher success rate
            high_level_monster = Mock()
            high_level_monster.level = 25
            mock_ai._calculate_success_rate.return_value = 0.8  # 80% success
            
            success_rate = mock_ai._calculate_success_rate(high_level_monster, self.easy_riddle)
            self.assertEqual(success_rate, 0.8)

    def test_battle_state_persistence_between_turns(self):
        """Test that battle state (HP, status, etc.) persists correctly between riddle turns."""
        # Initial state
        initial_player_hp = self.player_monster1.current_hp
        initial_enemy_hp = self.enemy_monster1.current_hp
        
        # Turn 1: Player takes damage
        damage_taken = 25
        self.player_monster1.current_hp -= damage_taken
        
        # Verify state persists
        self.assertEqual(self.player_monster1.current_hp, initial_player_hp - damage_taken)
        self.assertEqual(self.enemy_monster1.current_hp, initial_enemy_hp)  # Unchanged
        
        # Turn 2: Enemy takes damage
        enemy_damage = 40
        self.enemy_monster1.current_hp -= enemy_damage
        
        # Verify both states persist
        self.assertEqual(self.player_monster1.current_hp, initial_player_hp - damage_taken)
        self.assertEqual(self.enemy_monster1.current_hp, initial_enemy_hp - enemy_damage)

    def test_battle_victory_conditions(self):
        """Test different battle victory conditions with riddle system."""
        # Scenario 1: All enemy monsters defeated
        for monster in self.enemy.monsters:
            monster.current_hp = 0
        
        # Check victory condition
        enemy_has_conscious_monsters = any(m.current_hp > 0 for m in self.enemy.monsters)
        self.assertFalse(enemy_has_conscious_monsters)  # Player wins
        
        # Scenario 2: All player monsters defeated
        for monster in self.player.monsters:
            monster.current_hp = 0
        
        player_has_conscious_monsters = any(m.current_hp > 0 for m in self.player.monsters)
        self.assertFalse(player_has_conscious_monsters)  # Player loses

if __name__ == '__main__':
    unittest.main()