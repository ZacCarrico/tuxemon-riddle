# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Callable

import pygame
from pygame.rect import Rect

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
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components for the riddle state."""
        screen_rect = self.client.screen.get_rect()
        
        # Create dialog box
        box_width = int(screen_rect.width * 0.8)
        box_height = int(screen_rect.height * 0.6)
        box_x = (screen_rect.width - box_width) // 2
        box_y = (screen_rect.height - box_height) // 2
        
        self.dialog_box = GraphicBox()
        self.dialog_box.rect = Rect(box_x, box_y, box_width, box_height)
        
        # Question area
        question_rect = Rect(
            box_x + 20,
            box_y + 20,
            box_width - 40,
            int(box_height * 0.4)
        )
        self.question_area = TextArea(
            self.font, self.font_color, (96, 96, 128)
        )
        self.question_area.rect = question_rect
        
        # Format question text
        category_text = self.riddle.category.title()
        difficulty_text = self.riddle.difficulty.title()
        header = f"{self.monster_name} faces a {difficulty_text} {category_text} riddle!\n\n"
        question_text = header + self.riddle.question
        self.question_area.text = question_text
        
        # Input area
        input_rect = Rect(
            box_x + 20,
            box_y + int(box_height * 0.5),
            box_width - 40,
            40
        )
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
        self.hint_area = TextArea(
            self.font, (128, 128, 255), (96, 96, 128)
        )
        self.hint_area.rect = hint_rect
        
        # Add sprites
        self.sprites.add(self.dialog_box)
        self.sprites.add(self.question_area)
        self.sprites.add(self.input_area)

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

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the riddle state.

        Parameters:
            surface: Surface to draw on.
        """
        # Fill background
        surface.fill((32, 32, 64))
        
        # Draw sprites
        self.sprites.draw(surface)