# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Callable

import pygame
from pygame.rect import Rect

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.platform.const import events, buttons
from tuxemon.riddle.riddle import Riddle
from tuxemon.state import State
from tuxemon.ui.draw import GraphicBox

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Simple text wrapping function."""
    if not text or max_width <= 0:
        return [text] if text else []
        
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines


def render_text_in_rect(surface: pygame.Surface, text: str, rect: Rect, font: pygame.font.Font, color: tuple = (255, 255, 255)) -> None:
    """Render text within a rectangle with proper padding and line spacing."""
    if not text:
        return
        
    padding = 15  # Larger padding for better separation
    available_width = rect.width - 2 * padding
    
    if available_width <= 0:
        return  # Rectangle too small
        
    lines = wrap_text(text, font, available_width)
    y_offset = rect.y + padding
    line_height = font.get_height() + 4  # Extra spacing between lines
    
    for line in lines:
        # Stop if we would overflow the rectangle
        if y_offset + line_height > rect.bottom - padding:
            break
            
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (rect.x + padding, y_offset))
        y_offset += line_height


class RiddleAnswerState(State):
    """Simple riddle state with reliable feedback display."""

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
        
        # Simple state tracking
        self.answer_input = ""
        self.show_hint = False
        self.answered = False
        self.showing_feedback = False
        self.answer_correct = False
        
        # Font setup - consistent 16px font
        self.font = pygame.font.Font(None, 16)
        self.font_large = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 14)
        
        # Colors
        self.bg_color = (32, 32, 64)
        self.dialog_bg = (64, 64, 96)
        self.text_color = (255, 255, 255)
        self.error_color = (255, 100, 100)
        self.success_color = (100, 255, 100)
        self.hint_color = (200, 200, 255)
        
        # UI areas - simple rectangles with no overlaps
        screen_w, screen_h = prepare.SCREEN_SIZE
        margin = 40
        
        # Main dialog area (centered, 80% of screen)
        dialog_w = int(screen_w * 0.8)
        dialog_h = int(screen_h * 0.8)
        dialog_x = (screen_w - dialog_w) // 2
        dialog_y = (screen_h - dialog_h) // 2
        
        self.dialog_rect = Rect(dialog_x, dialog_y, dialog_w, dialog_h)
        
        # Subdivide dialog area with larger margins for clarity
        inner_margin = 30
        inner_x = dialog_x + inner_margin
        inner_w = dialog_w - 2 * inner_margin
        
        # Question area (top 45% - reduced to make room for other elements)
        question_height = int(dialog_h * 0.45)
        self.question_rect = Rect(
            inner_x, 
            dialog_y + inner_margin,
            inner_w,
            question_height
        )
        
        # Add more separation between sections
        section_gap = 25
        
        # Input/feedback area (middle section)
        input_y = self.question_rect.bottom + section_gap
        input_height = int(dialog_h * 0.25)
        self.input_rect = Rect(
            inner_x,
            input_y,
            inner_w,
            input_height
        )
        
        # Hint area (bottom section - NO overlap with question)
        hint_y = self.input_rect.bottom + section_gap
        hint_height = dialog_y + dialog_h - hint_y - inner_margin
        self.hint_rect = Rect(
            inner_x,
            hint_y,
            inner_w,
            max(hint_height, 40)  # Ensure minimum height
        )

    def _get_question_text(self) -> str:
        """Get the formatted question text."""
        header = f"{self.monster_name} faces a {self.riddle.difficulty.title()} {self.riddle.category.title()} riddle!"
        return f"{header}\n\n{self.riddle.question}"
    
    def _get_input_text(self) -> str:
        """Get the current input display text."""
        if self.showing_feedback:
            if self.answer_correct:
                return f"✅ CORRECT!\nThe answer was: {self.riddle.answer}\n\n[ENTER] Continue"
            else:
                return f"❌ WRONG!\nThe correct answer was: {self.riddle.answer}\n\n[ENTER] Continue"
        else:
            cursor = "|" if int(pygame.time.get_ticks() / 500) % 2 else " "
            return f"Your answer: {self.answer_input}{cursor}\n\n[ENTER] Submit  [H] Hint  [ESC] Cancel"
    
    def _get_hint_text(self) -> str:
        """Get the hint text if hint is shown."""
        if self.show_hint and self.riddle.hint:
            return f"💡 HINT: {self.riddle.hint}"
        return ""

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Process player input events with simple, reliable handling."""
        if self.showing_feedback:
            # During feedback, only ENTER continues
            if event.pressed and event.button == buttons.A:
                self._finish_riddle()
            return None
                
        if event.pressed:
            if event.button == buttons.A:  # ENTER
                self._submit_answer()
            elif event.button == buttons.BACK:  # ESC
                self._cancel_riddle()
            elif event.button == events.BACKSPACE:
                if self.answer_input:
                    self.answer_input = self.answer_input[:-1]
            elif event.button == events.UNICODE and hasattr(event, 'value'):
                char = str(event.value)
                if char == 'H':  # Capital H for hint
                    self._toggle_hint()
                elif char.isprintable() and len(self.answer_input) < 50:
                    self.answer_input += char.lower()
                        
        return None

    def _submit_answer(self) -> None:
        """Submit answer and show immediate feedback."""
        if self.answered:
            return
            
        self.answered = True
        self.answer_correct = self.riddle.check_answer(self.answer_input)
        self.showing_feedback = True
        self.show_hint = False  # Hide hint during feedback

    def _toggle_hint(self) -> None:
        """Toggle hint visibility."""
        if self.riddle.hint and not self.showing_feedback:
            self.show_hint = not self.show_hint

    def _cancel_riddle(self) -> None:
        """Cancel riddle (counts as wrong answer)."""
        if not self.showing_feedback:
            self.answer_correct = False
            self._finish_riddle()

    def _finish_riddle(self) -> None:
        """Clean up and return to combat."""
        # Clear any references to prevent memory leaks
        self.answered = True
        self.showing_feedback = False
        self.show_hint = False
        self.answer_input = ""
        
        # Pop this state to return to combat
        self.client.pop_state(self)
        
        # Call the callback to continue combat
        self.on_answer_callback(self.answer_correct)

    def update(self, dt: float) -> None:
        """Simple update with no complex logic."""
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw with clear visual separation between sections."""
        # Fill background
        surface.fill(self.bg_color)
        
        # Draw main dialog background
        pygame.draw.rect(surface, self.dialog_bg, self.dialog_rect)
        pygame.draw.rect(surface, self.text_color, self.dialog_rect, 3)
        
        # Draw question section with distinct background
        question_bg_color = (80, 80, 120)  # Slightly different shade
        pygame.draw.rect(surface, question_bg_color, self.question_rect)
        pygame.draw.rect(surface, (200, 200, 200), self.question_rect, 2)
        question_text = self._get_question_text()
        render_text_in_rect(surface, question_text, self.question_rect, self.font_large, self.text_color)
        
        # Draw input/feedback section with distinct background  
        input_bg_color = (60, 60, 80)  # Different shade for input
        pygame.draw.rect(surface, input_bg_color, self.input_rect)
        pygame.draw.rect(surface, (150, 150, 150), self.input_rect, 2)
        input_text = self._get_input_text()
        input_color = self.success_color if (self.showing_feedback and self.answer_correct) else \
                     self.error_color if (self.showing_feedback and not self.answer_correct) else \
                     self.text_color
        render_text_in_rect(surface, input_text, self.input_rect, self.font, input_color)
        
        # Draw hint if visible - with clear separation
        if self.show_hint:
            hint_text = self._get_hint_text()
            if hint_text:
                # Distinct background for hint
                pygame.draw.rect(surface, (40, 40, 60), self.hint_rect)
                pygame.draw.rect(surface, self.hint_color, self.hint_rect, 2)
                render_text_in_rect(surface, hint_text, self.hint_rect, self.font_small, self.hint_color)

