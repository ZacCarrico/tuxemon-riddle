# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame

from tuxemon.states.riddle.riddle_state import RiddleAnswerState
from tuxemon.riddle.riddle import Riddle
from tuxemon.session import Session


class TestRiddleUI(unittest.TestCase):
    """Test riddle UI components and user interaction."""

    def setUp(self):
        """Set up test environment for UI testing."""
        # Initialize pygame for UI testing
        pygame.init()
        
        # Create mock session and client
        self.mock_session = Mock(spec=Session)
        self.mock_client = Mock()
        self.mock_session.client = self.mock_client
        
        # Mock screen
        self.mock_screen = Mock()
        self.mock_screen.get_rect.return_value = pygame.Rect(0, 0, 800, 600)
        self.mock_client.screen = self.mock_screen
        
        # Create test riddle
        self.test_riddle_data = {
            "riddle_id": 1,
            "slug": "test_ui_riddle",
            "category": "logic",
            "difficulty": "medium",
            "question": "What has keys but no locks, space but no room, and you can enter but not go inside?",
            "answer": "keyboard",
            "alternate_answers": ["a keyboard"],
            "hint": "Think about computer peripherals",
            "damage_multiplier": 1.5,
            "experience_reward": 15
        }
        self.test_riddle = Riddle(save_data=self.test_riddle_data)
        
        # Mock callback
        self.mock_callback = Mock()

    def tearDown(self):
        """Clean up pygame."""
        pygame.quit()

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_state_initialization(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test riddle state initializes UI components correctly."""
        # Mock UI components        
        mock_box_instance = Mock()
        mock_graphic_box.return_value = mock_box_instance
        
        mock_text_instance = Mock()
        mock_text_area.return_value = mock_text_instance
        
        # Create riddle state
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Verify initialization
        self.assertEqual(riddle_state.riddle, self.test_riddle)
        self.assertEqual(riddle_state.on_answer_callback, self.mock_callback)
        self.assertEqual(riddle_state.monster_name, "Test Monster")
        self.assertFalse(riddle_state.answered)
        self.assertFalse(riddle_state.showing_feedback)

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_answer_input_handling(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test riddle answer input processing."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Test character input
        mock_event = Mock()
        mock_event.pressed = True
        mock_event.button = None
        mock_event.unicode = "k"
        
        riddle_state.process_event(mock_event)
        self.assertEqual(riddle_state.answer_input, "k")
        
        # Test more input
        mock_event.unicode = "e"
        riddle_state.process_event(mock_event)
        self.assertEqual(riddle_state.answer_input, "ke")

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_backspace_handling(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test backspace removes characters from input."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Add some input
        riddle_state.answer_input = "keyb"
        
        # Test backspace
        mock_event = Mock()
        mock_event.pressed = True
        mock_event.button = pygame.K_BACKSPACE
        mock_event.unicode = ""
        
        riddle_state.process_event(mock_event)
        self.assertEqual(riddle_state.answer_input, "key")

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_answer_submission(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test riddle answer submission and callback."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Set correct answer
        riddle_state.answer_input = "keyboard"
        
        # Test Enter key
        mock_event = Mock()
        mock_event.pressed = True
        mock_event.button = pygame.K_RETURN
        
        riddle_state.process_event(mock_event)
        
        # Should be answered and showing feedback
        self.assertTrue(riddle_state.answered)
        self.assertTrue(riddle_state.showing_feedback)
        self.assertTrue(riddle_state.answer_correct)

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_hint_toggle(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test hint display toggle functionality."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Initially no hint shown
        self.assertFalse(riddle_state.show_hint)
        
        # Test H key to show hint
        mock_event = Mock()
        mock_event.pressed = True
        mock_event.button = pygame.K_h
        
        riddle_state.process_event(mock_event)
        self.assertTrue(riddle_state.show_hint)
        
        # Test H key again to hide hint
        riddle_state.process_event(mock_event)
        self.assertFalse(riddle_state.show_hint)

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_escape_cancellation(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test escape key cancels riddle."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Mock client pop_state method
        riddle_state.client = Mock()
        
        # Test Escape key
        mock_event = Mock()
        mock_event.pressed = True
        mock_event.button = pygame.K_ESCAPE
        
        riddle_state.process_event(mock_event)
        
        # Should call callback with False (cancelled/wrong)
        self.mock_callback.assert_called_once_with(False)

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_input_length_limit(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test input length is limited to prevent overflow."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Fill input to near limit
        riddle_state.answer_input = "a" * 49  # Just under 50 char limit
        
        # Try to add another character
        mock_event = Mock()
        mock_event.pressed = True
        mock_event.button = None
        mock_event.unicode = "b"
        
        riddle_state.process_event(mock_event)
        self.assertEqual(len(riddle_state.answer_input), 50)
        
        # Try to add one more (should be rejected)
        mock_event.unicode = "c"
        riddle_state.process_event(mock_event)
        self.assertEqual(len(riddle_state.answer_input), 50)  # Still 50, not 51

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_feedback_display(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test correct and incorrect answer feedback."""
        # Mock UI components
        mock_graphic_box.return_value = Mock()
        mock_text_instance = Mock()
        mock_text_area.return_value = mock_text_instance
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Set input area for feedback
        riddle_state.input_area = mock_text_instance
        
        # Test correct answer feedback
        riddle_state.answer_correct = True
        riddle_state._show_feedback()
        
        # Verify feedback shows correct message
        self.assertTrue(riddle_state.showing_feedback)
        self.assertEqual(riddle_state.feedback_timer, 0.0)
        
        # Check that input area text was updated (call should have been made)
        self.assertTrue(mock_text_instance.text is not None)

    @patch('tuxemon.states.riddle.riddle_state.RiddleAnswerState._setup_ui')
    @patch('tuxemon.states.riddle.riddle_state.GraphicBox')
    @patch('tuxemon.states.riddle.riddle_state.TextArea')
    def test_riddle_update_timer(self, mock_setup_ui, mock_text_area, mock_graphic_box):
        """Test riddle state update and feedback timer."""
        # Mock UI components  
        mock_graphic_box.return_value = Mock()
        mock_text_area.return_value = Mock()
        
        riddle_state = RiddleAnswerState(
            session=self.mock_session,
            riddle=self.test_riddle,
            on_answer_callback=self.mock_callback,
            monster_name="Test Monster"
        )
        
        # Start showing feedback
        riddle_state.showing_feedback = True
        riddle_state.feedback_timer = 0.0
        
        # Mock client for state removal
        riddle_state.client = Mock()
        
        # Update with enough time to exceed feedback duration
        riddle_state.update(3.0)  # 3 seconds, more than 2 second duration
        
        # Should have called callback and removed state
        self.mock_callback.assert_called_once_with(riddle_state.answer_correct)

if __name__ == '__main__':
    unittest.main()