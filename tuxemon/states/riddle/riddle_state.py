# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Callable

import pygame
from pygame.rect import Rect

from pygame.font import Font

from tuxemon import prepare, tools
from tuxemon.locale import T
from tuxemon.riddle.riddle import Riddle
from tuxemon.state import State
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class RiddleAnswerState(State):
    """
    State for presenting riddles and accepting user input for answers.
    """

    def __init__(
        self,
        session: Session,
        riddle: Riddle,
        on_answer_callback: Callable[[bool], None],
        monster_name: str = "Monster"
    ) -> None:
        super().__init__()
        self.session = session
        self.riddle = riddle
        self.on_answer_callback = on_answer_callback
        self.monster_name = monster_name
        
        # Font attributes (similar to Menu class)
        self.font_filename = prepare.fetch("font", prepare.CONFIG.locale.font_file)
        self.font = Font(self.font_filename, tools.scale(12))
        self.font_color = prepare.FONT_COLOR
        self.font_shadow_color = prepare.FONT_SHADOW_COLOR
        
        # UI components
        self.dialog_box: Optional[GraphicBox] = None
        self.question_area: Optional[TextArea] = None
        self.answer_input = ""
        self.input_area: Optional[TextArea] = None
        self.hint_area: Optional[TextArea] = None
        self.show_hint = False
        
        # State management
        self.answered = False
        self.feedback_timer = 0.0
        self.feedback_duration = 2.0  # Show feedback for 2 seconds
        self.showing_feedback = False
        self.answer_correct = False
        
        # Error logging setup
        self._setup_error_logging()
        
        try:
            self._setup_ui()
        except Exception as e:
            self._log_error(f"Error setting up riddle UI: {e}", e)

    def _setup_ui(self) -> None:
        """Set up the UI components for the riddle state."""
        try:
            logger.info("Setting up riddle UI components...")
            screen_rect = self.client.screen.get_rect()
            logger.info(f"Screen rect: {screen_rect}")
            
            # Create dialog box
            box_width = int(screen_rect.width * 0.8)
            box_height = int(screen_rect.height * 0.6)
            box_x = (screen_rect.width - box_width) // 2
            box_y = (screen_rect.height - box_height) // 2
            
            logger.info(f"Creating dialog box at {box_x}, {box_y} with size {box_width}x{box_height}")
            self.dialog_box = GraphicBox()
            self.dialog_box.rect = Rect(box_x, box_y, box_width, box_height)
            
            # Initialize the dialog box properly (it may need assets)
            try:
                # Try to load a border asset, fallback to simple drawing if not available
                border_path = prepare.fetch("gfx", "dialog-box01.png")
                logger.info(f"Attempting to load border: {border_path}")
            except:
                logger.warning("Could not load dialog border, will use fallback rendering")
                # Set a flag to use fallback rendering
                self.dialog_box = None
        
            # Question area
            question_rect = Rect(
                box_x + 20,
                box_y + 20,
                box_width - 40,
                int(box_height * 0.4)
            )
            logger.info(f"Creating question area at {question_rect}")
            self.question_area = TextArea(
                self.font, self.font_color, (96, 96, 128)
            )
            self.question_area.rect = question_rect
            
            # Format question text
            category_text = self.riddle.category.title()
            difficulty_text = self.riddle.difficulty.title()
            header = f"{self.monster_name} faces a {difficulty_text} {category_text} riddle!\n\n"
            question_text = header + self.riddle.question
            logger.info(f"Question text: {question_text}")
            
            # Set the question text if we successfully created the question area
            if self.question_area:
                self.question_area.text = question_text
            
            # Input area
            input_rect = Rect(
                box_x + 20,
                box_y + int(box_height * 0.5),
                box_width - 40,
                40
            )
            logger.info(f"Creating input area at {input_rect}")
            self.input_area = TextArea(
                self.font, self.font_color, (128, 128, 96)
            )
            self.input_area.rect = input_rect
            self._update_input_display()
            
            # Hint area (initially hidden)
            hint_rect = Rect(
                box_x + 20,
                box_y + int(box_height * 0.65),
                box_width - 40,
                int(box_height * 0.25)
            )
            logger.info(f"Creating hint area at {hint_rect}")
            self.hint_area = TextArea(
                self.font, (128, 128, 255), (96, 96, 128)
            )
            logger.info("UI setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up UI components: {e}")
            # Set fallback values
            self.dialog_box = None
            self.question_area = None
            self.input_area = None
            self.hint_area = None
        self.hint_area.rect = hint_rect
        
        # Add sprites
        self.sprites.add(self.dialog_box)
        self.sprites.add(self.question_area)
        self.sprites.add(self.input_area)

    def _setup_error_logging(self) -> None:
        """Set up error logging to a file for debugging purposes."""
        try:
            # Create error log directory if it doesn't exist
            log_dir = Path("error_logs")
            log_dir.mkdir(exist_ok=True)
            
            # Set up the error log file
            self.error_log_path = log_dir / "riddle_errors.log"
            
            # Set up logging
            self.error_logger = logging.getLogger(f"riddle_error_{id(self)}")
            self.error_logger.setLevel(logging.ERROR)
            
            # Avoid duplicate handlers
            if not self.error_logger.handlers:
                handler = logging.FileHandler(self.error_log_path, mode='a')
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.error_logger.addHandler(handler)
                
        except Exception as e:
            # Fallback to console logging if file logging fails
            logger.error(f"Failed to set up error logging: {e}")
            self.error_logger = logger

    def _log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        Log an error to the error file for debugging.
        
        Parameters:
            message: The error message to log.
            exception: The exception that occurred (optional).
        """
        try:
            # Log to our error logger
            if exception:
                self.error_logger.error(f"{message}\nTraceback: {traceback.format_exc()}")
            else:
                self.error_logger.error(message)
                
            # Also log to console for immediate visibility
            logger.error(message)
            if exception:
                logger.error(f"Exception details: {traceback.format_exc()}")
                
        except Exception as log_error:
            # Fallback logging
            logger.error(f"Failed to log error: {log_error}")
            logger.error(f"Original error: {message}")

    def _update_input_display(self) -> None:
        """Update the input area with current answer and prompt."""
        if self.input_area:
            prompt = "Your answer: "
            cursor = "|" if int(pygame.time.get_ticks() / 500) % 2 else " "
            display_text = f"{prompt}{self.answer_input}{cursor}"
            
            if not self.showing_feedback:
                display_text += "\n\n[ENTER] Submit  [H] Hint  [ESC] Cancel"
            
            self.input_area.text = display_text

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Process player input events.

        Parameters:
            event: The input event to process.

        Returns:
            The event if not handled, None if handled.
        """
        try:
            if self.showing_feedback:
                # During feedback, only accept ENTER to continue
                if event.pressed and event.button == pygame.K_RETURN:
                    self._finish_riddle()
                return None
                
            if event.pressed:
                if event.button == pygame.K_RETURN:
                    self._submit_answer()
                elif event.button == pygame.K_ESCAPE:
                    self._cancel_riddle()
                elif event.button == pygame.K_h:
                    self._toggle_hint()
                elif event.button == pygame.K_BACKSPACE:
                    self.answer_input = self.answer_input[:-1]
                    self._update_input_display()
                elif event.unicode and event.unicode.isprintable():
                    # Add character to answer (limit length)
                    if len(self.answer_input) < 50:
                        self.answer_input += event.unicode.lower()
                        self._update_input_display()
                        
            return None
        except Exception as e:
            self._log_error(f"Error processing event: {e}", e)
            return event

    def _submit_answer(self) -> None:
        """Submit the current answer and show feedback."""
        if self.answered or self.showing_feedback:
            return
            
        self.answered = True
        self.answer_correct = self.riddle.check_answer(self.answer_input)
        
        # Show feedback
        self._show_feedback()

    def _show_feedback(self) -> None:
        """Show feedback about the answer."""
        self.showing_feedback = True
        self.feedback_timer = 0.0
        
        if self.answer_correct:
            feedback = f"Correct! The answer is '{self.riddle.answer}'.\n"
            feedback += f"{self.monster_name} deals extra damage!"
            if self.riddle.experience_reward > 0:
                feedback += f"\n+{self.riddle.experience_reward} XP!"
        else:
            feedback = f"Incorrect. The answer was '{self.riddle.answer}'.\n"
            feedback += f"{self.monster_name} takes damage instead!"
            
        # Update input area to show feedback
        if self.input_area:
            self.input_area.text = feedback + "\n\n[ENTER] Continue"

    def _toggle_hint(self) -> None:
        """Toggle hint display."""
        if not self.riddle.hint or self.showing_feedback:
            return
            
        self.show_hint = not self.show_hint
        
        if self.show_hint:
            if self.hint_area:
                self.hint_area.text = f"Hint: {self.riddle.hint}"
                self.sprites.add(self.hint_area)
        else:
            if self.hint_area:
                self.sprites.remove(self.hint_area)

    def _cancel_riddle(self) -> None:
        """Cancel the riddle (counts as wrong answer)."""
        if not self.showing_feedback:
            self.answer_correct = False
            self._finish_riddle()

    def _finish_riddle(self) -> None:
        """Finish the riddle and call the callback."""
        self.client.pop_state(self)
        self.on_answer_callback(self.answer_correct)

    def update(self, dt: float) -> None:
        """
        Update the state.

        Parameters:
            dt: Time delta since last update.
        """
        try:
            super().update(dt)
            
            if self.showing_feedback:
                self.feedback_timer += dt
                if self.feedback_timer >= self.feedback_duration:
                    # Auto-advance after feedback timeout
                    if not self.answered:  # Only if user hasn't pressed ENTER
                        self._finish_riddle()
            
            # Update input display periodically for cursor blink
            if not self.showing_feedback and int(pygame.time.get_ticks() / 500) % 10 == 0:
                self._update_input_display()
        except Exception as e:
            self._log_error(f"Error in update: {e}", e)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the riddle state.

        Parameters:
            surface: Surface to draw on.
        """
        try:
            # Fill background
            surface.fill((32, 32, 64))
            
            # Draw sprites
            self.sprites.draw(surface)
            
            # Draw UI components or use fallback rendering
            if self.dialog_box or self.question_area or self.input_area:
                # Try normal rendering first
                if self.dialog_box:
                    self.dialog_box.draw(surface)
                    
                if self.question_area:
                    self.question_area.draw(surface)
                    
                if self.input_area:
                    self.input_area.draw(surface)
                    
                if self.hint_area and self.show_hint:
                    self.hint_area.draw(surface)
            else:
                # Fallback rendering - draw text directly
                self._draw_fallback(surface)
                
        except Exception as e:
            self._log_error(f"Error in draw: {e}", e)
            # If drawing fails, try fallback
            try:
                self._draw_fallback(surface)
            except Exception as fallback_error:
                self._log_error(f"Fallback rendering also failed: {fallback_error}", fallback_error)

    def _draw_fallback(self, surface: pygame.Surface) -> None:
        """Fallback rendering method that draws text directly to surface."""
        try:
            import pygame
            
            # Get screen dimensions
            screen_rect = surface.get_rect()
            
            # Draw a simple background box
            box_width = int(screen_rect.width * 0.8)
            box_height = int(screen_rect.height * 0.6)
            box_x = (screen_rect.width - box_width) // 2
            box_y = (screen_rect.height - box_height) // 2
            
            # Draw background box
            pygame.draw.rect(surface, (64, 64, 96), (box_x, box_y, box_width, box_height))
            pygame.draw.rect(surface, (255, 255, 255), (box_x, box_y, box_width, box_height), 3)
            
            # Prepare question text
            category_text = self.riddle.category.title() if hasattr(self.riddle, 'category') else "Unknown"
            difficulty_text = self.riddle.difficulty.title() if hasattr(self.riddle, 'difficulty') else "Easy"
            header = f"{self.monster_name} faces a {difficulty_text} {category_text} riddle!"
            question_text = self.riddle.question if hasattr(self.riddle, 'question') else "What is 2 + 2?"
            
            # Draw text
            y_offset = box_y + 20
            
            # Header
            header_surface = self.font.render(header, True, (255, 255, 255))
            surface.blit(header_surface, (box_x + 20, y_offset))
            y_offset += 40
            
            # Question
            question_surface = self.font.render(question_text, True, (255, 255, 255))
            surface.blit(question_surface, (box_x + 20, y_offset))
            y_offset += 60
            
            # Input prompt
            input_prompt = f"Your answer: {self.answer_input}_"
            input_surface = self.font.render(input_prompt, True, (255, 255, 128))
            surface.blit(input_surface, (box_x + 20, y_offset))
            y_offset += 40
            
            # Instructions
            instructions = "Press ENTER to submit, H for hint, ESC to cancel"
            instruction_surface = self.font.render(instructions, True, (200, 200, 200))
            surface.blit(instruction_surface, (box_x + 20, y_offset))
            
            # Show hint if requested
            if self.show_hint and hasattr(self.riddle, 'hint'):
                y_offset += 40
                hint_text = f"Hint: {self.riddle.hint}"
                hint_surface = self.font.render(hint_text, True, (128, 128, 255))
                surface.blit(hint_surface, (box_x + 20, y_offset))
                
            logger.info("Fallback rendering completed")
            
        except Exception as e:
            logger.error(f"Error in fallback rendering: {e}")
            # Ultimate fallback - just show basic text
            try:
                text = f"RIDDLE: {self.riddle.question if hasattr(self.riddle, 'question') else 'What is 2 + 2?'}"
                text_surface = self.font.render(text, True, (255, 255, 255))
                surface.blit(text_surface, (50, 50))
            except:
                pass