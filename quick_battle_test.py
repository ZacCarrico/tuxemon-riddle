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
        
        try:
            super().__init__(config, screen)
        except OSError as e:
            if "Address already in use" in str(e):
                print("⚠️ Network port in use - retrying in 2 seconds...")
                import time
                time.sleep(2)
                super().__init__(config, screen)
            else:
                raise
        
        # Set up global references (needed for the game to work properly)
        setattr(prepare, "GLOBAL_CONTROL", self)
        local_session.set_client(self)
        
        # Push background state to prevent early exit
        self.push_state("BackgroundState")
        
        # Call startup to initialize the test scenario
        print("🎯 Calling startup...")
        self.startup()
    
    def startup(self):
        """Initialize and jump directly into battle"""
        try:
            print("🧩 QUICK RIDDLE BATTLE TEST")
            print("=" * 40)
            print("Use 'Answer Riddle' instead of 'Fight'!")
            print("=" * 40)
            
            print(f"📊 State manager initialized")
            if hasattr(self.state_manager, 'current_state') and self.state_manager.current_state:
                print(f"✅ Current state: {type(self.state_manager.current_state).__name__}")
            else:
                print("❌ No current state!")
            
            # Delay battle setup to let the window initialize
            import threading
            import time
            
            def delayed_setup():
                time.sleep(1)  # Wait 1 second
                print("🎯 Setting up battle...")
                self.setup_battle()
            
            threading.Thread(target=delayed_setup, daemon=True).start()
            print("🕒 Battle setup scheduled, window should stay open...")
            
        except Exception as e:
            print(f"💥 Error in startup: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_battle(self):
        """Set up a quick battle"""
        try:
            # Set up a minimal mock world to satisfy session requirements
            class MockWorld:
                def __init__(self):
                    pass
            
            # Set mock world in session
            local_session.set_world(MockWorld())
            
            # Create simple player and NPC
            from tuxemon.player import Player
            from tuxemon.npc import NPC
            
            # Create a basic player using npc_test as base
            player = Player(npc_slug="npc_test", session=local_session)
            player.monsters.clear()
            
            # Create player monster
            player_monster = Monster.create("bamboon")
            player_monster.level = 10
            player_monster.set_level(10)
            player_monster.current_hp = player_monster.hp
            player.monsters.append(player_monster)
            
            # Create enemy NPC using another existing NPC
            enemy_npc = NPC(npc_slug="npc_red", session=local_session)
            
            # Create enemy monster
            enemy_monster = Monster.create("rockitten")
            enemy_monster.level = 8
            enemy_monster.set_level(8)
            enemy_monster.current_hp = enemy_monster.hp
            enemy_npc.monsters.clear()
            enemy_npc.monsters.append(enemy_monster)
            
            # Battle environment
            env = EnvironmentModel.lookup("grass", db)
            
            # Create battle context
            context = CombatContext(
                session=local_session,
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
            print("🎯 Close the window to exit the test")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ Battle setup failed, but keeping window open for debugging")

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