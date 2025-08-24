#!/usr/bin/env python3
"""
Quick Riddle Battle Test

Simple script to quickly launch into a riddle battle for testing.
Just run it and you'll be in a battle immediately!

Usage: python quick_battle_test.py
"""

import sys
import pygame
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
# Remove the CONFIG import since we'll use prepare.CONFIG
from tuxemon.db import db, EnvironmentModel
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.states.combat.combat_context import CombatContext

class QuickBattleClient(LocalPygameClient):
    """Minimal client that launches directly into battle"""
    
    def __init__(self):
        # Initialize pygame and prepare
        prepare.init()
        config = prepare.CONFIG
        screen = prepare.SCREEN
        super().__init__(config, screen)
        
        # Set up global references (needed for the game to work properly)
        setattr(prepare, "GLOBAL_CONTROL", self)
        local_session.set_client(self)
    
    def startup(self):
        """Initialize and jump directly into battle"""
        super().startup()
        
        print("🧩 QUICK RIDDLE BATTLE TEST")
        print("=" * 40)
        print("Use 'Answer Riddle' instead of 'Fight'!")
        print("=" * 40)
        
        self.setup_battle()
    
    def setup_battle(self):
        """Set up a quick battle"""
        try:
            session = local_session
            player = session.player
            
            # Clear and create player monster
            player.monsters.clear()
            player_monster = Monster.create("bamboon")
            player_monster.level = 10
            player_monster.set_level(10)
            player_monster.current_hp = player_monster.hp
            player.monsters.append(player_monster)
            
            # Create enemy NPC
            enemy_npc = NPC()
            enemy_npc.name = "Test Enemy"
            enemy_npc.slug = "test_enemy"
            
            enemy_monster = Monster.create("rockitten")
            enemy_monster.level = 8
            enemy_monster.set_level(8)
            enemy_monster.current_hp = enemy_monster.hp
            enemy_npc.monsters = [enemy_monster]
            
            # Battle environment
            env = EnvironmentModel.lookup("grass", db)
            
            # Create battle context
            context = CombatContext(
                session=session,
                teams=[player, enemy_npc],
                combat_type="trainer",
                graphics=env.battle_graphics,
                battle_mode="single",
            )
            
            # Launch battle directly
            self.push_state("CombatState", context=context)
            self.event_engine.execute_action("play_music", [env.battle_music], True)
            
            print("✅ Battle started!")
            print("🎮 Window is now open for manual testing - battle should be running!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self.exit = True

def main():
    """Launch the quick battle"""
    try:
        client = QuickBattleClient()
        client.main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()