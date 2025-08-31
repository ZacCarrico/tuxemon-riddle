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
from tuxemon.platform.const import events, buttons
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
        
        # Font attributes - using minimum font size of 10
        self.font_filename = prepare.fetch("font", prepare.CONFIG.locale.font_file)
        self.font_size = max(tools.scale(10), 10)  # Main text font, minimum 10
        self.font = Font(self.font_filename, self.font_size)
        self.small_font = Font(self.font_filename, max(tools.scale(10), 10))  # Also minimum 10 for readability
        self.instruction_font = Font(self.font_filename, max(tools.scale(10), 10))  # Instructions, minimum 10
        self.font_color = prepare.FONT_COLOR
        self.font_shadow_color = prepare.FONT_SHADOW_COLOR
        
        # UI components
        self.dialog_box: Optional[GraphicBox] = None
        self.question_area: Optional[TextArea] = None
        self.answer_input = ""
        self.input_area: Optional[TextArea] = None
        self.hint_area: Optional[TextArea] = None
        self.show_hint = False
        
        # Text box layout system
        self.text_boxes = {}  # Will store defined text box areas
        
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

    def _define_text_boxes(self, screen_rect: Rect) -> None:
        """Define text box areas to prevent overlap."""
        # Main dialog area (80% of screen)
        dialog_width = int(screen_rect.width * 0.8)
        dialog_height = int(screen_rect.height * 0.8)
        dialog_x = (screen_rect.width - dialog_width) // 2
        dialog_y = (screen_rect.height - dialog_height) // 2
        
        # Define text box regions within dialog
        padding = 20
        usable_width = dialog_width - (padding * 2)
        usable_height = dialog_height - (padding * 2)
        
        # Header area (top 15%)
        header_height = int(usable_height * 0.15)
        self.text_boxes['header'] = Rect(
            dialog_x + padding,
            dialog_y + padding,
            usable_width,
            header_height
        )
        
        # Question area (middle 45%)
        question_height = int(usable_height * 0.45)
        self.text_boxes['question'] = Rect(
            dialog_x + padding,
            dialog_y + padding + header_height + 10,
            usable_width,
            question_height
        )
        
        # Input/Feedback area (bottom 25%)
        input_height = int(usable_height * 0.25)
        self.text_boxes['input'] = Rect(
            dialog_x + padding,
            dialog_y + padding + header_height + question_height + 20,
            usable_width,
            input_height
        )
        
        # Hint area (overlays question area bottom, separate box)
        hint_height = int(usable_height * 0.15)
        self.text_boxes['hint'] = Rect(
            dialog_x + padding,
            dialog_y + padding + header_height + question_height - hint_height - 10,
            usable_width,
            hint_height
        )
        
        # Instructions area (very bottom)
        instruction_height = 30
        self.text_boxes['instructions'] = Rect(
            dialog_x + padding,
            dialog_y + dialog_height - instruction_height - 10,
            usable_width,
            instruction_height
        )

    def _get_dialog_bounds(self) -> Rect:
        """Get the overall dialog bounds that encompasses all text boxes."""
        if not self.text_boxes:
            # Fallback if text boxes not defined
            screen_rect = self.client.screen.get_rect()
            return Rect(
                int(screen_rect.width * 0.1), 
                int(screen_rect.height * 0.1),
                int(screen_rect.width * 0.8),
                int(screen_rect.height * 0.8)
            )
        
        # Find bounds that encompass all text boxes
        all_boxes = list(self.text_boxes.values())
        min_x = min(box.x for box in all_boxes) - 20
        min_y = min(box.y for box in all_boxes) - 20
        max_x = max(box.right for box in all_boxes) + 20
        max_y = max(box.bottom for box in all_boxes) + 20
        
        return Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def _render_text_in_box(self, surface: pygame.Surface, text: str, box_name: str, 
                           font: Font, color: tuple, center: bool = False) -> None:
        """Render text within a defined text box boundary."""
        if box_name not in self.text_boxes:
            logger.warning(f"Text box '{box_name}' not defined")
            return
            
        text_box = self.text_boxes[box_name]
        
        # Text wrapping function
        def wrap_text_to_box(text: str, font: Font, max_width: int) -> list[str]:
            """Wrap text to fit within max_width."""
            words = text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                text_width = font.size(test_line)[0]
                
                if text_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        # Single word is too long, add it anyway
                        lines.append(word)
                        current_line = ""
            
            if current_line:
                lines.append(current_line)
                
            return lines
        
        # Wrap text to fit in box width
        wrapped_lines = wrap_text_to_box(text, font, text_box.width - 10)
        
        # Calculate line height and total text height
        line_height = font.get_height() + 2
        total_text_height = len(wrapped_lines) * line_height
        
        # Determine starting Y position
        if center:
            start_y = text_box.y + (text_box.height - total_text_height) // 2
        else:
            start_y = text_box.y + 5
        
        # Render each line within the box
        y_offset = start_y
        for line in wrapped_lines:
            # Stop if we exceed the box height
            if y_offset + line_height > text_box.bottom:
                break
                
            # Render the line
            if center:
                line_width = font.size(line)[0]
                x_pos = text_box.x + (text_box.width - line_width) // 2
            else:
                x_pos = text_box.x + 5
                
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (x_pos, y_offset))
            y_offset += line_height

    def _setup_ui(self) -> None:
        """Set up the UI components for the riddle state."""
        try:
            logger.info("Setting up riddle UI components...")
            screen_rect = self.client.screen.get_rect()
            logger.info(f"Screen rect: {screen_rect}")
            
            # Define text box layout system
            self._define_text_boxes(screen_rect)
            
            # Create dialog box using text box bounds
            dialog_bounds = self._get_dialog_bounds()
            box_width = dialog_bounds.width
            box_height = dialog_bounds.height  
            box_x = dialog_bounds.x
            box_y = dialog_bounds.y
            
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
            self.hint_area.rect = hint_rect
            logger.info("UI setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up UI components: {e}")
            # Set fallback values
            self.dialog_box = None
            self.question_area = None
            self.input_area = None
            self.hint_area = None
        
        # Add sprites only if they exist and are valid
        if self.dialog_box is not None:
            try:
                self.sprites.add(self.dialog_box)
            except:
                logger.warning("Could not add dialog_box to sprites")
                
        if hasattr(self, 'question_area') and self.question_area is not None:
            try:
                self.sprites.add(self.question_area)
            except:
                logger.warning("Could not add question_area to sprites")
                
        if hasattr(self, 'input_area') and self.input_area is not None:
            try:
                self.sprites.add(self.input_area)
            except:
                logger.warning("Could not add input_area to sprites")

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
        # Only update input display when not showing feedback
        if self.input_area and not self.showing_feedback:
            prompt = "Your answer: "
            cursor = "|" if int(pygame.time.get_ticks() / 500) % 2 else " "
            display_text = f"{prompt}{self.answer_input}{cursor}"
            display_text += "\n\n[ENTER] Submit  [CAPITAL H] Hint  [ESC] Cancel"
            
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
            # Debug logging for input events
            logger.info(f"Processing event: button={event.button}, pressed={getattr(event, 'pressed', 'N/A')}, value={getattr(event, 'value', 'N/A')}")
            
            # Special debug for specific keys
            if event.button == pygame.K_BACKSPACE:
                logger.info("BACKSPACE key detected!")
            if event.button == buttons.A:
                logger.info("ENTER/A button detected!")
            if event.button == buttons.BACK:
                logger.info("ESC/BACK button detected!")
            
            if self.showing_feedback:
                # During feedback, only accept ENTER to continue
                if event.pressed and event.button == buttons.A:  # ENTER is mapped to buttons.A
                    logger.info("ENTER pressed in feedback mode - finishing riddle")
                    self._finish_riddle()
                return None
                
            if event.pressed:
                if event.button == buttons.A:  # ENTER is mapped to buttons.A
                    logger.info("ENTER pressed - submitting answer")
                    self._submit_answer()
                elif event.button == buttons.BACK:  # ESC is mapped to buttons.BACK
                    logger.info("ESC pressed - cancelling riddle")
                    self._cancel_riddle()
                elif event.button == buttons.HINT:  # H key is properly mapped now
                    logger.info("H pressed - toggling hint")
                    self._toggle_hint()
                elif event.button == events.BACKSPACE:  # Correct backspace event
                    logger.info(f"Backspace pressed! Current input: '{self.answer_input}'")
                    if self.answer_input:  # Only delete if there's something to delete
                        self.answer_input = self.answer_input[:-1]
                        logger.info(f"After backspace: '{self.answer_input}'")
                    self._update_input_display()
                elif event.button == events.UNICODE:
                    # Add character to answer (limit length)
                    if len(self.answer_input) < 50 and hasattr(event, 'value') and event.value:
                        char = str(event.value)
                        # Only allow standard printable characters (letters, numbers, basic punctuation)
                        if char.isprintable() and ord(char) >= 32 and ord(char) < 127:
                            # Check if character is capital 'H' for hint
                            if char == 'H':
                                logger.info("Capital H pressed - toggling hint")
                                self._toggle_hint()
                            else:
                                # Add character to answer (including lowercase 'h')
                                self.answer_input += char.lower()
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
            feedback = f"🎉 Correct! The answer is '{self.riddle.answer}'.\n"
            
            # Add riddle category and difficulty info
            if hasattr(self.riddle, 'category') and hasattr(self.riddle, 'difficulty'):
                feedback += f"({self.riddle.difficulty.title()} {self.riddle.category.title()} riddle solved!)\n"
            
            feedback += f"⚔️ {self.monster_name} deals extra damage!"
            
            # Show damage multiplier if available
            if hasattr(self.riddle, 'damage_multiplier') and self.riddle.damage_multiplier != 1.0:
                multiplier_percent = int(self.riddle.damage_multiplier * 100)
                feedback += f"\n💥 {multiplier_percent}% damage bonus!"
            
            # Show experience reward
            if hasattr(self.riddle, 'experience_reward') and self.riddle.experience_reward > 0:
                feedback += f"\n⭐ +{self.riddle.experience_reward} XP bonus!"
        else:
            feedback = f"❌ Incorrect. The correct answer was '{self.riddle.answer}'.\n"
            
            # Add explanation if your answer was close
            if hasattr(self, 'answer_input') and self.answer_input:
                user_input = self.answer_input.strip().lower()
                correct_answer = self.riddle.answer.strip().lower()
                if user_input and user_input != correct_answer:
                    # Check if it was a close attempt
                    if len(user_input) > 0 and (user_input in correct_answer or correct_answer in user_input):
                        feedback += f"(Your answer '{self.answer_input}' was close!)\n"
                    elif len(user_input) >= 3:
                        # For longer answers, check if it was a near miss using simple similarity
                        try:
                            # Simple character-based similarity check
                            common_chars = set(user_input) & set(correct_answer)
                            total_chars = set(user_input) | set(correct_answer)
                            if len(common_chars) / len(total_chars) > 0.5:  # 50% character overlap
                                feedback += f"(Your answer '{self.answer_input}' was very close!)\n"
                        except:
                            pass
            
            feedback += f"💔 {self.monster_name} takes damage instead!"
            
        # Hide hint when showing feedback
        if self.show_hint and self.hint_area:
            self.show_hint = False
            self.sprites.remove(self.hint_area)
        
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
        """Improved rendering method using text box system with minimum font size 10."""
        try:
            import pygame
            
            # Get screen dimensions and ensure text boxes are defined
            screen_rect = surface.get_rect()
            if not self.text_boxes:
                self._define_text_boxes(screen_rect)
            
            # Draw the dialog background
            dialog_bounds = self._get_dialog_bounds()
            pygame.draw.rect(surface, (64, 64, 96), dialog_bounds)
            pygame.draw.rect(surface, (255, 255, 255), dialog_bounds, 3)
            
            # Prepare content
            category_text = self.riddle.category.title() if hasattr(self.riddle, 'category') else "Unknown"
            difficulty_text = self.riddle.difficulty.title() if hasattr(self.riddle, 'difficulty') else "Easy"
            header = f"{self.monster_name} faces a {difficulty_text} {category_text} riddle!"
            question_text = self.riddle.question if hasattr(self.riddle, 'question') else "What is 2 + 2?"
            
            # Render header in header box
            self._render_text_in_box(surface, header, 'header', self.font, (255, 255, 255), center=True)
            
            # Render question in question box
            self._render_text_in_box(surface, question_text, 'question', self.font, (255, 255, 255))
            
            # Render input or feedback in input box
            if self.showing_feedback:
                if self.answer_correct:
                    feedback_text = f"🎉 Correct! The answer is '{self.riddle.answer}'."
                    feedback_color = (128, 255, 128)
                    if hasattr(self.riddle, 'experience_reward') and self.riddle.experience_reward > 0:
                        feedback_text += f" +{self.riddle.experience_reward} XP!"
                else:
                    feedback_text = f"❌ Incorrect. The answer was '{self.riddle.answer}'."
                    feedback_color = (255, 128, 128)
                
                self._render_text_in_box(surface, feedback_text, 'input', self.font, feedback_color)
                instructions = "ENTER=continue"
            else:
                cursor = "|" if int(pygame.time.get_ticks() / 500) % 2 else " "
                input_text = f"Answer: {self.answer_input}{cursor}"
                self._render_text_in_box(surface, input_text, 'input', self.font, (255, 255, 128))
                instructions = "ENTER=submit, CAPITAL H=hint, ESC=cancel"
            
            # Render instructions at bottom
            self._render_text_in_box(surface, instructions, 'instructions', self.instruction_font, (200, 200, 200), center=True)
            
            # Show hint in hint box if requested (and not showing feedback)
            if self.show_hint and hasattr(self.riddle, 'hint') and not self.showing_feedback:
                hint_text = f"💡 Hint: {self.riddle.hint}"
                # Draw hint box background for visibility
                hint_box = self.text_boxes['hint']
                pygame.draw.rect(surface, (48, 48, 80), hint_box)
                pygame.draw.rect(surface, (128, 128, 255), hint_box, 2)
                self._render_text_in_box(surface, hint_text, 'hint', self.font, (128, 255, 255))
                
        except Exception as e:
            logger.error(f"Error in improved rendering: {e}")
            # Ultimate fallback with minimum font size
            try:
                font = self.font if hasattr(self, 'font') else pygame.font.Font(None, 10)
                question = self.riddle.question if hasattr(self.riddle, 'question') else 'What is 2 + 2?'
                
                # Simple layout with minimum font size
                y = 50
                
                # Question
                question_surface = font.render(question, True, (255, 255, 255))
                surface.blit(question_surface, (20, y))
                y += 40
                
                # Input or feedback
                if self.showing_feedback:
                    if self.answer_correct:
                        status = f"Correct! Answer: {self.riddle.answer}"
                        color = (128, 255, 128)
                    else:
                        status = f"Wrong! Answer: {self.riddle.answer}"
                        color = (255, 128, 128)
                else:
                    cursor = "|" if int(pygame.time.get_ticks() / 500) % 2 else " "
                    status = f"Answer: {self.answer_input}{cursor}"
                    color = (255, 255, 128)
                    
                status_surface = font.render(status, True, color)
                surface.blit(status_surface, (20, y))
                y += 30
                
                # Instructions
                if self.showing_feedback:
                    instructions = "ENTER=continue"
                else:
                    instructions = "ENTER=submit, CAPITAL H=hint, ESC=cancel"
                    
                instruction_surface = font.render(instructions, True, (200, 200, 200))
                surface.blit(instruction_surface, (20, y))
                
            except Exception as ultimate_error:
                logger.error(f"Ultimate fallback failed: {ultimate_error}")
                # Draw basic error message
                try:
                    error_font = pygame.font.Font(None, 12)
                    error_surface = error_font.render("Riddle display error", True, (255, 128, 128))
                    surface.blit(error_surface, (20, 20))
                except:
                    pass