# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest import TestCase
from unittest.mock import MagicMock

from tuxemon.db import MissionStatus
from tuxemon.mission import (
    Mission,
    MissionController,
    MissionProgress,
)
from tuxemon.npc import NPC, NPCBagHandler, PartyHandler


class TestMissionManager(TestCase):
    def setUp(self):
        self.character = MagicMock(spec=NPC)
        self.mission = Mission()
        self.mission_controller = MissionController(self.character)
        self.mission_manager = self.mission_controller.mission_manager

    def test_add_mission(self):
        self.mission_manager.add_mission(self.mission)
        self.assertEqual(self.mission_manager.missions, [self.mission])

    def test_remove_mission(self):
        self.mission_manager.add_mission(self.mission)
        self.mission_manager.remove_mission(self.mission)
        self.assertEqual(self.mission_manager.missions, [])

    def test_remove_mission_not_found(self):
        with self.assertRaises(ValueError):
            self.mission_manager.remove_mission(self.mission)

    def test_find_mission(self):
        self.mission.slug = "test_mission"
        self.mission_manager.add_mission(self.mission)
        found_mission = self.mission_manager.find_mission("test_mission")
        self.assertEqual(found_mission, self.mission)

    def test_find_mission_not_found(self):
        found_mission = self.mission_manager.find_mission("test_mission")
        self.assertIsNone(found_mission)

    def test_update_status(self):
        self.mission.status = MissionStatus.pending
        self.mission.update_status(MissionStatus.completed)
        self.assertEqual(self.mission.status, MissionStatus.completed)

    def test_update_status_no_change(self):
        self.mission.status = MissionStatus.pending
        self.mission.update_status(MissionStatus.pending)
        self.assertEqual(self.mission.status, MissionStatus.pending)

    def test_get_mission_count(self):
        self.assertEqual(self.mission_manager.get_mission_count(), 0)
        self.mission_manager.add_mission(Mission())
        self.assertEqual(self.mission_manager.get_mission_count(), 1)

    def test_check_all_prerequisites(self):
        self.mission.prerequisites = [{"key": "value"}]
        self.mission_manager.add_mission(self.mission)

        self.character.game_variables = {"key": "value"}
        self.assertTrue(self.mission_controller.check_all_prerequisites())

        self.character.game_variables = {"key": "wrong_value"}
        self.assertFalse(self.mission_controller.check_all_prerequisites())

    def test_check_required_items(self):
        self.mission.required_items = ["potion", "lotion"]

        item1 = MagicMock()
        item1.slug = "potion"
        item2 = MagicMock()
        item2.slug = "lotion"

        self.character.items = MagicMock(spec=NPCBagHandler)
        self.character.items.find_item.side_effect = lambda slug: (
            item1 if slug == "potion" else item2 if slug == "lotion" else None
        )

        self.assertTrue(self.mission.check_required_items(self.character))

        self.character.items.find_item.side_effect = lambda slug: (
            item1 if slug == "potion" else None
        )
        self.assertFalse(self.mission.check_required_items(self.character))

    def test_check_required_monsters(self):
        self.mission.required_monsters = ["monster1", "monster2"]

        monster1 = MagicMock()
        monster1.slug = "monster1"
        monster2 = MagicMock()
        monster2.slug = "monster2"

        self.character.party = MagicMock(spec=PartyHandler)
        self.character.party.find_monster.side_effect = lambda slug: (
            monster1
            if slug == "monster1"
            else monster2 if slug == "monster2" else None
        )

        self.assertTrue(self.mission.check_required_monsters(self.character))

        self.character.party.find_monster.side_effect = lambda slug: (
            monster1 if slug == "monster1" else None
        )
        self.assertFalse(self.mission.check_required_monsters(self.character))

    def test_get_progress(self):
        self.mission.progress = []
        self.character.game_variables = {"key": "value"}
        self.assertEqual(self.mission.get_progress(self.character), 0.0)

        self.mission.progress = [
            MissionProgress(
                game_variables={"key": "wrong_value"},
                completion_percentage=50.0,
            ),
        ]
        self.character.game_variables = {"key": "value"}
        self.assertEqual(self.mission.get_progress(self.character), 0.0)

        self.mission.progress = [
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=100.0
            ),
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=50.0
            ),
        ]
        self.character.game_variables = {"key": "value"}
        self.assertEqual(self.mission.get_progress(self.character), 75.0)

        self.mission.progress = [
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=100.0
            ),
            MissionProgress(
                game_variables={"key": "wrong_value"},
                completion_percentage=50.0,
            ),
        ]
        self.character.game_variables = {"key": "value"}
        self.assertEqual(self.mission.get_progress(self.character), 100.0)

        self.mission.progress = [
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=0.0
            ),
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=0.0
            ),
        ]
        self.character.game_variables = {"key": "value"}
        self.assertEqual(self.mission.get_progress(self.character), 0.0)

    def test_check_all_prerequisites_with_no_missions(self):
        self.assertTrue(self.mission_controller.check_all_prerequisites())

    def test_check_all_prerequisites_with_unmet_conditions(self):
        self.mission.prerequisites = [{"key": "required_value"}]
        self.mission_manager.add_mission(self.mission)

        self.character.game_variables = {"key": "incorrect_value"}
        self.assertFalse(self.mission_controller.check_all_prerequisites())

    def test_encode_missions(self):
        self.mission.slug = "mission1"
        self.mission.status = MissionStatus.pending
        self.mission_manager.add_mission(self.mission)

        encoded_missions = self.mission_controller.encode_missions()
        self.assertIsInstance(encoded_missions, list)
        self.assertEqual(len(encoded_missions), 1)
        self.assertEqual(encoded_missions[0]["slug"], "mission1")
        self.assertEqual(encoded_missions[0]["status"], MissionStatus.pending)

    def test_check_connected_missions(self):
        self.mission.check_connected_missions = MagicMock(return_value=True)
        self.mission_manager.add_mission(self.mission)

        self.assertTrue(self.mission_controller.check_connected_missions())

        self.mission.check_connected_missions.return_value = False
        self.assertFalse(self.mission_controller.check_connected_missions())

    def test_large_mission_list(self):
        for i in range(1000):
            mock_mission = MagicMock()
            mock_mission.slug = f"mission_{i}"
            self.mission_manager.add_mission(mock_mission)

        self.assertEqual(self.mission_manager.get_mission_count(), 1000)
