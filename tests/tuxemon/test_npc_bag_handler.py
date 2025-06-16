# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from tuxemon.npc import NPCBagHandler


class TestNPCBagHandler(unittest.TestCase):

    def setUp(self):
        self.handler = NPCBagHandler(item_boxes=MagicMock())
        self.item = MagicMock(slug="test_item", instance_id=uuid4())

    def test_init(self):
        self.assertEqual(self.handler._items, [])
        self.assertEqual(self.handler._bag_limit, 99)

    def test_add_item(self):
        self.handler.add_item(self.item)
        self.assertIn(self.item, self.handler._items)

    def test_add_item_to_locker(self):
        self.handler._bag_limit = 0

        self.handler.add_item(self.item)
        self.assertEqual(self.handler._items, [])

    def test_remove_item(self):
        self.handler.add_item(self.item)
        self.handler.remove_item(self.item)
        self.assertNotIn(self.item, self.handler._items)

    def test_find_item(self):
        self.handler.add_item(self.item)
        found_item = self.handler.find_item("test_item")
        self.assertEqual(found_item, self.item)

    def test_find_item_not_found(self):
        found_item = self.handler.find_item("test_item")
        self.assertIsNone(found_item)

    def test_get_items(self):
        item1 = MagicMock(slug="test_item1", instance_id=uuid4())
        item2 = MagicMock(slug="test_item2", instance_id=uuid4())
        self.handler.add_item(item1)
        self.handler.add_item(item2)
        items = self.handler.get_items()
        self.assertIn(item1, items)
        self.assertIn(item2, items)

    def test_has_item(self):
        self.handler.add_item(self.item)
        self.assertTrue(self.handler.has_item("test_item"))

    def test_has_item_not_found(self):
        self.assertFalse(self.handler.has_item("test_item"))

    def test_find_item_by_id(self):
        self.handler.add_item(self.item)
        found_item = self.handler.find_item_by_id(self.item.instance_id)
        self.assertEqual(found_item, self.item)

    def test_find_item_by_id_not_found(self):
        found_item = self.handler.find_item_by_id(uuid4())
        self.assertIsNone(found_item)

    def test_clear_items(self):
        self.handler.add_item(self.item)
        self.handler.clear_items()
        self.assertEqual(self.handler._items, [])

    def test_count_item(self):
        self.handler.add_item(self.item)
        self.handler.add_item(self.item)
        self.assertEqual(self.handler.count_item("test_item"), 2)
