# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    TypedDict,
    no_type_check,
)

from pygame.surface import Surface

from tuxemon import networking, prepare
from tuxemon.camera import Camera
from tuxemon.db import Direction
from tuxemon.map_view import MapRenderer
from tuxemon.movement import MovementManager, Pathfinder
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import translate_input_event
from tuxemon.player import Player
from tuxemon.session import Session
from tuxemon.state import State
from tuxemon.states.world.world_transition import WorldTransition
from tuxemon.teleporter import Teleporter

if TYPE_CHECKING:
    from tuxemon.entity import Entity
    from tuxemon.networking import EventData

logger = logging.getLogger(__name__)

direction_map: Mapping[int, Direction] = {
    intentions.UP: Direction.up,
    intentions.DOWN: Direction.down,
    intentions.LEFT: Direction.left,
    intentions.RIGHT: Direction.right,
}


class WorldSave(TypedDict, total=False):
    pass


class WorldState(State):
    """The state responsible for the world game play"""

    def __init__(self, session: Session, map_name: str) -> None:
        super().__init__()
        self.session = session
        self.session.set_world(self)
        self.screen = self.client.screen
        self.tile_size = prepare.TILE_SIZE
        self.movement = MovementManager(self.client)
        self.teleporter = Teleporter(self.client, self)
        self.pathfinder = Pathfinder(self.client)
        self.transition_manager = WorldTransition(self)
        self.player = Player.create(self.session, self)
        self.camera = Camera(self.player, self.client.boundary)
        self.client.camera_manager.add_camera(self.camera)
        self.map_renderer = MapRenderer(self.client)

        if map_name:
            self.change_map(map_name)
        else:
            raise ValueError("You must pass the map name to load")

    def get_state(self, session: Session) -> WorldSave:
        """Returns a dictionary of the World to be saved."""
        state: WorldSave = {}
        return state

    def set_state(self, session: Session, save_data: WorldSave) -> None:
        """Recreates the World from the provided saved data."""

    def resume(self) -> None:
        """Called after returning focus to this state"""
        self.movement.unlock_controls(self.player)

    def pause(self) -> None:
        """Called before another state gets focus"""
        self.movement.lock_controls(self.player)
        self.movement.stop_char(self.player)

    def broadcast_player_teleport_change(self) -> None:
        """Tell clients/host that player has moved after teleport."""
        # Set the transition variable in event_data to false when we're done
        self.client.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        self.network = self.client.network_manager
        if self.network.is_connected():
            assert self.network.client
            current_map = self.client.get_map_name()
            self.client.npc_manager.add_clients_to_map(
                self.network.client.client.registry, current_map
            )
            self.network.client.update_player(self.player.facing)

        # Update the location of the npcs. Doesn't send network data.
        for npc in self.client.npc_manager.npcs.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

        for npc in self.client.npc_manager.npcs_off_map.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

    def update(self, time_delta: float) -> None:
        """
        The primary game loop that executes the world's functions every frame.

        Parameters:
            time_delta: Amount of time passed since last frame.
        """
        super().update(time_delta)
        self.client.npc_manager.update_npcs(time_delta, self.client)
        self.client.npc_manager.update_npcs_off_map(time_delta, self.client)
        self.map_renderer.update(time_delta)

        logger.debug("*** Game Loop Started ***")

    def draw(self, surface: Surface) -> None:
        """
        Draw the game world to the screen.

        Parameters:
            surface: Surface to draw into.
        """
        self.screen = surface
        if self.client.map_manager.current_map is None:
            raise ValueError("Unable to draw the game world.")
        self.map_renderer.draw(surface, self.client.map_manager.current_map)
        self.transition_manager.draw(surface)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Handles player input events.

        This function is only called when the player provides input such
        as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        Parameters:
            event: Event to handle.

        Returns:
            Passed events, if other states should process it, ``None``
            otherwise.
        """
        event = translate_input_event(event)

        # Handle menu activation
        if event.button == intentions.WORLD_MENU and event.pressed:
            logger.info("Opening main menu!")
            self.client.event_manager.release_controls(
                self.client.input_manager
            )
            self.client.push_state("WorldMenuState", character=self.player)
            return None

        # Return early if no player is registered
        if self.player is None:
            return None

        # Handle interaction event
        if event.button == intentions.INTERACT and event.pressed:
            if False:  # Multiplayer logic placeholder
                self.check_interactable_space()
                return None

        # Handle running movement toggle
        if event.button == intentions.RUN:
            self.player.mover.update_movement_state(event.held)

        # Handle directional movement
        if (direction := direction_map.get(event.button)) is not None:
            if not self.camera.follows_entity:
                return self.client.camera_manager.handle_input(event)
            if event.held:
                self.movement.queue_movement(self.player.slug, direction)
                if self.movement.is_movement_allowed(self.player):
                    self.movement.move_char(self.player, direction)
                return None
            if not event.pressed and self.movement.has_pending_movement(
                self.player
            ):
                self.movement.stop_char(self.player)
                return None

        # Debug tools (DEV_TOOLS)
        if prepare.DEV_TOOLS and event.pressed:
            if event.button == intentions.NOCLIP:
                self.player.ignore_collisions = (
                    not self.player.ignore_collisions
                )
                return None
            elif event.button == intentions.RELOAD_MAP:
                assert self.client.map_manager.current_map
                self.client.map_manager.current_map.reload_tiles()
                return None

        # Return event for others to process
        return event

    def add_collision(self, entity: Entity[Any], pos: Sequence[float]) -> None:
        """
        Registers the given entity's position within the collision zone.
        """
        self.client.collision_manager.add_collision(entity, pos)

    def remove_collision(self, tile_pos: tuple[int, int]) -> None:
        """
        Removes the specified tile position from the collision zone.
        """
        self.client.collision_manager.remove_collision(tile_pos)

    def pathfind(
        self, start: tuple[int, int], dest: tuple[int, int], facing: Direction
    ) -> Optional[Sequence[tuple[int, int]]]:
        return self.pathfinder.pathfind(start, dest, facing)

    ####################################################
    #             Map Change/Load Functions            #
    ####################################################
    def change_map(self, map_name: str) -> None:
        """
        Changes the current map and updates the game state accordingly.

        This method loads the map data, updates the game state, and notifies
        the client and boundary checker. The currently loaded map is updated
        because the event engine loads event conditions and event actions from
        the currently loaded map. If we change maps, we need to update this.

        Parameters:
            map_name: The name of the map to load.
        """
        logger.debug(f"Loading map '{map_name}' using Client's MapLoader.")
        map_data = self.client.map_loader.load_map_data(map_name)

        self.client.event_engine.reset()
        self.client.event_engine.set_current_map(map_data)

        self.client.map_manager.load_map(map_data)
        self.client.npc_manager.clear_npcs()
        map_size = self.client.map_manager.map_size
        self.client.boundary.update_boundaries(map_size)

    @no_type_check  # only used by multiplayer which is disabled
    def check_interactable_space(self) -> bool:
        """
        Checks to see if any Npc objects around the player are interactable.

        It then populates a menu of possible actions.

        Returns:
            ``True`` if there is an Npc to interact with. ``False`` otherwise.
        """
        collision_dict = self.get_collision_map()
        player_tile_pos = self.player.tile_pos
        collisions = self.player.collision_check(
            player_tile_pos,
            collision_dict,
            self.client.map_manager.collision_lines_map,
        )
        if not collisions:
            pass
        else:
            for direction in collisions:
                if self.player.facing == direction:
                    if direction == Direction.up:
                        tile = (player_tile_pos[0], player_tile_pos[1] - 1)
                    elif direction == Direction.down:
                        tile = (player_tile_pos[0], player_tile_pos[1] + 1)
                    elif direction == Direction.left:
                        tile = (player_tile_pos[0] - 1, player_tile_pos[1])
                    elif direction == Direction.right:
                        tile = (player_tile_pos[0] + 1, player_tile_pos[1])
                    for npc in self.client.npc_manager.npcs:
                        tile_pos = (
                            int(round(npc.tile_pos[0])),
                            int(round(npc.tile_pos[1])),
                        )
                        if tile_pos == tile:
                            logger.info("Opening interaction menu!")
                            self.client.push_state("InteractionMenu")
                            return True
                        else:
                            continue

        return False

    @no_type_check  # FIXME: dead code
    def handle_interaction(
        self, event_data: EventData, registry: Mapping[str, Any]
    ) -> None:
        """
        Presents options window when another player has interacted with this player.

        :param event_data: Information on the type of interaction and who sent it.
        :param registry:

        :type event_data: Dictionary
        :type registry: Dictionary
        """
        target = registry[event_data["target"]]["sprite"]
        target_name = str(target.name)
        networking.update_client(target, event_data["char_dict"], self.client)
        if event_data["interaction"] == "DUEL":
            if not event_data["response"]:
                self.interaction_menu.visible = True
                self.interaction_menu.interactable = True
                self.interaction_menu.player = target
                self.interaction_menu.interaction = "DUEL"
                self.interaction_menu.menu_items = [
                    target_name + " would like to Duel!",
                    "Accept",
                    "Decline",
                ]
            else:
                if self.wants_duel:
                    if event_data["response"] == "Accept":
                        world = self.client.current_state
                        pd = self.player.__dict__
                        event_data = {
                            "type": "CLIENT_INTERACTION",
                            "interaction": "START_DUEL",
                            "target": [event_data["target"]],
                            "response": None,
                            "char_dict": {
                                "monsters": pd["monsters"],
                                "inventory": pd["inventory"],
                            },
                        }
                        self.client.server.notify_client_interaction(
                            "cuuid", event_data
                        )
