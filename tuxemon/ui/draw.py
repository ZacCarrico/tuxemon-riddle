# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from collections.abc import Callable, Generator, Iterable, Sequence
from itertools import product
from typing import Optional

from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.transform import scale

from tuxemon import prepare
from tuxemon.graphics import ColorLike
from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

__all__ = ("GraphicBox",)


def create_layout(
    scale: float,
) -> Callable[[Sequence[float]], Sequence[float]]:
    def func(area: Sequence[float]) -> Sequence[float]:
        return [scale * i for i in area]

    return func


layout = create_layout(prepare.SCALE)


class TileLayout:
    """
    Extracts a grid of tiles from a border image and assigns logical names
    like 'nw', 'n', 'ne', etc. Assumes a 3x3 layout by default.
    """

    def __init__(self, image: Surface, grid_size: int = 3) -> None:
        if grid_size <= 0:
            raise ValueError("Grid size must be a positive integer")
        self.grid_size = grid_size
        self.tiles: dict[str, Surface] = self._extract_tiles(image)

    def _extract_tiles(self, image: Surface) -> dict[str, Surface]:
        if image.get_size() == (0, 0):
            raise ValueError("Image cannot be empty")

        iw, ih = image.get_size()

        if iw % self.grid_size != 0 or ih % self.grid_size != 0:
            raise ValueError("Image dimensions must be divisible by grid size")

        tw, th = iw // self.grid_size, ih // self.grid_size
        layout_map = {
            (0, 0): "nw",
            (0, 1): "n",
            (0, 2): "ne",
            (1, 0): "w",
            (1, 1): "c",
            (1, 2): "e",
            (2, 0): "sw",
            (2, 1): "s",
            (2, 2): "se",
        }

        tiles: dict[str, Surface] = {}
        for (row, col), label in layout_map.items():
            x, y = col * tw, row * th
            rect = Rect(x, y, tw, th)
            tiles[label] = image.subsurface(rect)

        if len(tiles) != self.grid_size**2:
            raise ValueError(
                f"Expected {self.grid_size ** 2} tiles, got {len(tiles)}"
            )

        return tiles


class GraphicBox(Sprite):
    """
    Generic class for drawing graphical boxes.

    Draws a border and can fill in the box with a _color from the border file,
    an external file, or a solid _color.

    box = GraphicBox('border.png')
    box.draw(surface, rect)

    The border graphic must contain 9 tiles laid out in a box.
    """

    TILE_GRID_SIZE = 3

    def __init__(
        self,
        border: Optional[Surface] = None,
        background: Optional[Surface] = None,
        color: Optional[ColorLike] = None,
        fill_tiles: bool = False,
    ) -> None:
        """
        Initializes the GraphicBox object.

        Parameters:
            border: The border image.
            background: The background image.
            color: The fill color.
            fill_tiles: Whether to fill the box with tiles from the border image.
        """
        super().__init__()
        self._background = background
        self._color = color
        self._fill_tiles = fill_tiles
        self._tiles: dict[str, Surface] = {}
        self._tile_size = 0, 0

        if border:
            self._set_border(border)

    def calc_inner_rect(self, rect: Rect) -> Rect:
        """
        Calculates the inner rectangle of the box.

        Parameters:
            rect: The outer rectangle of the box.

        Returns:
            The inner rectangle of the box.
        """
        if self._tiles:
            tw, th = self._tile_size
            return rect.inflate(-tw * 2, -th * 2)
        else:
            return rect

    def _set_border(self, image: Surface) -> None:
        """
        Sets the border image and extracts the individual tiles.
        The border graphic must contain 9 tiles laid out in a 3x3 grid.

        Parameters:
            image: The border image.
        """
        layout = TileLayout(image, self.TILE_GRID_SIZE)
        self._tiles = layout.tiles
        self._tile_size = next(iter(self._tiles.values())).get_size()
        self._needs_update = True

    def update_image(self) -> None:
        """
        Updates the object's image by drawing the box on a new surface.
        """
        rect = Rect((0, 0), self._rect.size)
        surface = Surface(rect.size, SRCALPHA)
        self._draw(surface, rect)
        self.image = surface

    def _draw(
        self,
        surface: Surface,
        rect: Rect,
    ) -> Rect:
        inner = self.calc_inner_rect(rect)

        # Fill center
        if self._background:
            surface.blit(scale(self._background, inner.size), inner)
        elif self._color:
            surface.fill(self._color, inner)
        elif self._fill_tiles:
            self._draw_tiled_fill(surface, inner)

        # Draw border
        if self._tiles:
            self._draw_border(surface, rect, inner)

        return rect

    def _draw_tiled_fill(self, surface: Surface, inner: Rect) -> None:
        tw, th = self._tile_size
        center_tile = self._tiles["c"]
        for x in range(inner.left, inner.right, tw):
            for y in range(inner.top, inner.bottom, th):
                surface.blit(center_tile, (x, y))

    def _draw_border(self, surface: Surface, rect: Rect, inner: Rect) -> None:
        """
        Draws the tiled border around the inner rectangle.
        """
        left, top = rect.topleft
        tw, th = self._tile_size
        surface_blit = surface.blit  # cache the blit method

        # Draw top and bottom border tiles
        for x in range(inner.left, inner.right, tw):
            area = (
                (0, 0, tw, th)
                if x + tw < inner.right
                else (0, 0, tw - (x + tw - inner.right), th)
            )
            surface_blit(self._tiles["n"], (x, top), area)
            surface_blit(self._tiles["s"], (x, inner.bottom), area)

        # Draw left and right border tiles
        for y in range(inner.top, inner.bottom, th):
            area = (
                (0, 0, tw, th)
                if y + th < inner.bottom
                else (0, 0, tw, th - (y + th - inner.bottom))
            )
            surface_blit(self._tiles["w"], (left, y), area)
            surface_blit(self._tiles["e"], (inner.right, y), area)

        # Draw corner tiles
        surface_blit(self._tiles["nw"], (left, top))
        surface_blit(self._tiles["sw"], (left, inner.bottom))
        surface_blit(self._tiles["ne"], (inner.right, top))
        surface_blit(self._tiles["se"], (inner.right, inner.bottom))


def guest_font_height(font: Font) -> int:
    return guess_rendered_text_size("Tg", font)[1]


def guess_rendered_text_size(
    text: str,
    font: Font,
) -> tuple[int, int]:
    return font.size(text)


def shadow_text(
    font: Font,
    fg: ColorLike,
    bg: ColorLike,
    text: str,
) -> Surface:
    top = font.render(text, True, fg)
    shadow = font.render(text, True, bg)

    offset = layout((0.5, 0.5))
    size = [int(math.ceil(a + b)) for a, b in zip(offset, top.get_size())]
    image = Surface(size, SRCALPHA)

    image.blit(shadow, tuple(offset))
    image.blit(top, (0, 0))
    return image


def iter_render_text(
    text: str,
    font: Font,
    fg: ColorLike,
    bg: ColorLike,
    rect: Rect,
    alignment: str = "left",
    vertical_alignment: str = "top",
) -> Generator[tuple[Rect, Surface], None, None]:
    line_height = guest_font_height(font)

    # Convert generator to list to calculate total height
    lines = list(constrain_width(text, font, rect.width))
    total_text_height = len(lines) * line_height

    # Calculate vertical alignment offset
    if vertical_alignment == "middle":
        vertical_offset = (rect.height - total_text_height) // 2
    elif vertical_alignment == "bottom":
        vertical_offset = rect.height - total_text_height
    else:
        vertical_offset = 0

    for line_index, line in enumerate(lines):
        # Adjust `top` based on the vertical alignment
        top = rect.top + line_index * line_height + vertical_offset

        # Calculate horizontal alignment offset
        if alignment == "center":
            offset = (rect.width - font.size(line)[0]) // 2
        elif alignment == "right":
            offset = rect.width - font.size(line)[0]
        else:
            offset = 0

        for scrap in build_line(line):
            if scrap[-1] == " ":
                # No need to blit a white sprite onto a white background
                continue
            dirty_length = font.size(scrap[:-1])[0]
            surface = shadow_text(font, fg, bg, scrap[-1])
            update_rect = surface.get_rect(
                top=top,
                left=rect.left + dirty_length + offset,
            )
            yield update_rect, surface


def build_line(text: str) -> Generator[str, None, None]:
    for index in range(1, len(text) + 1):
        yield text[:index]


def constrain_width(
    text: str,
    font: Font,
    width: int,
) -> Generator[str, None, None]:
    for line in iterate_word_lines(text):
        scrap = ""
        for word in line:
            test = scrap + " " + word if scrap else word
            if font.size(test)[0] >= width:
                if not scrap:
                    raise RuntimeError("message is too large for width", text)
                yield scrap
                scrap = word
            else:
                scrap = test
        yield scrap


def iterate_words(text: str) -> Generator[str, None, None]:
    yield from text.split(" ")


def iterate_lines(text: str) -> Generator[str, None, None]:
    yield from text.strip().split("\n")


def iterate_word_lines(text: str) -> Generator[Iterable[str], None, None]:
    for line in iterate_lines(text):
        yield iterate_words(line)


def blit_alpha(
    target: Surface,
    source: Surface,
    location: tuple[int, int],
    opacity: int,
) -> None:
    """
    Blits a surface with alpha that can also have its overall transparency
    modified.
    Taken from http://nerdparadise.com/tech/python/pygame/blitopacity/

    Parameters:
        target: The surface to blit onto.
        source: The surface to blit.
        location: The location to blit the source surface.
        opacity: The overall transparency of the source surface, ranging
            from 0 (fully transparent) to 255 (fully opaque).

    Notes:
        This function has performance implications due to the creation of
        a temporary surface. It is recommended to use this function sparingly.
    """

    x = location[0]
    y = location[1]
    temp = Surface((source.get_width(), source.get_height())).convert()
    temp.blit(target, (-x, -y))
    temp.blit(source, (0, 0))
    temp.set_alpha(opacity)
    target.blit(temp, location)
