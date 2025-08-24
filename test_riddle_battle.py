#!/usr/bin/env python3
"""
Riddle Battle Test Script

This script launches Tuxemon directly into a battle scenario to test the riddle combat system.
You can test different battle scenarios, difficulty levels, and monster combinations.

Usage:
    python test_riddle_battle.py [options]

Options:
    --npc <npc_name>        Choose opponent NPC (default: npc_test)
    --level <level>         Set player monster level (default: 10)
    --monster <slug>        Choose player monster (default: bamboon)
    --enemy-level <level>   Set enemy monster level (default: 8)
    --help                  Show this help message

Examples:
    python test_riddle_battle.py
    python test_riddle_battle.py --npc red --level 15
    python test_riddle_battle.py --monster tux --level 20 --enemy-level 18
"""

import sys
import argparse
import pygame
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
from tuxemon.db import db, EnvironmentModel
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.states.combat.combat_context import CombatContext
from tuxemon.platform.events import PlayerInput


class BattleTestClient(LocalPygameClient):
    """Custom client for battle testing"""
    
    def __init__(self, player_monster="bamboon", player_level=10, 
                 enemy_npc="npc_test", enemy_level=8):
        # Initialize pygame and prepare
        prepare.init()
        config = prepare.CONFIG
        
        # Disable networking to avoid port conflicts
        config.net_controller_enabled = False
        
        screen = prepare.SCREEN
        
        # Monkey patch the NetworkManager to avoid port conflicts
        original_init = None
        try:
            from tuxemon.networking import NetworkManager
            original_init = NetworkManager.initialize
            NetworkManager.initialize = lambda self: None
        except:
            pass
        
        super().__init__(config, screen)
        
        # Restore the original method
        if original_init:
            NetworkManager.initialize = original_init
        
        # Set up global references (needed for the game to work properly)
        setattr(prepare, "GLOBAL_CONTROL", self)
        local_session.set_client(self)
        
        # Push background state to prevent early exit
        self.push_state("BackgroundState")
        
        # Set instance variables first
        self.player_monster = player_monster
        self.player_level = player_level
        self.enemy_npc = enemy_npc
        self.enemy_level = enemy_level
        
        # Call startup to initialize the test scenario
        print("🎯 Calling startup...")
        self.startup()
        
    def startup(self):
        """Initialize the test scenario"""
        
        print("=" * 60)
        print("🧩 TUXEMON RIDDLE BATTLE TEST")
        print("=" * 60)
        print("Testing the new riddle-based combat system!")
        print("")
        print("🎮 CONTROLS:")
        print("   • Click 'Answer Riddle' to start a riddle")
        print("   • Type your answer and press ENTER")
        print("   • Press H for hints during riddles")
        print("   • Press ESC to cancel riddle (counts as wrong)")
        print("   • Use other menu options (Item, Swap, Run/Forfeit) normally")
        print("")
        print("🧠 RIDDLE SYSTEM:")
        print("   • Correct answers deal extra damage to enemy")
        print("   • Wrong answers cause damage to your monster")
        print("   • Difficulty scales with monster levels")
        print("   • Different monster types get different riddle categories")
        print("")
        print("⚔️  STARTING BATTLE...")
        print(f"   Player: {self.player_monster} (Level {self.player_level})")
        print(f"   Enemy: {self.enemy_npc} (Level {self.enemy_level})")
        print("=" * 60)
        
        # Set up the test battle after a short delay
        print("🔧 Setting up battle...")
        self.setup_test_battle()
        print("✅ Battle setup complete")
    
    def setup_test_battle(self):
        """Set up a test battle scenario"""
        try:
            # Initialize the session and player
            session = local_session
            
            # Create a minimal mock world to avoid map loading
            class MockWorld:
                def __init__(self):
                    self.map_manager = None
                    pass
            
            if not hasattr(session, '_world') or session._world is None:
                session.set_world(MockWorld())
            
            # Create player if not already initialized
            if not hasattr(session, '_player') or session._player is None:
                from tuxemon.player import Player
                # Create player using the proper player NPC
                from tuxemon.player import Player
                player = Player.create(session, "npc_red")
                session.set_player(player)
            else:
                player = session.player
            
            # Clear any existing monsters
            player.monsters.clear()
            
            # Create player's monster
            player_monster = Monster.create(self.player_monster)
            player_monster.level = self.player_level
            player_monster.set_level(self.player_level)
            player_monster.current_hp = player_monster.hp
            player.monsters.append(player_monster)
            
            # Create enemy NPC
            try:
                # Try to load the NPC from database
                enemy_npc = NPC.create(self.enemy_npc)
            except:
                # Fallback: create a basic NPC
                print(f"⚠️  NPC '{self.enemy_npc}' not found, creating basic enemy...")
                enemy_npc = NPC()
                enemy_npc.name = "Test Enemy"
                enemy_npc.slug = "test_enemy"
                
                # Give the enemy a monster
                enemy_monster = Monster.create("bamboon")  # Default enemy monster
                enemy_monster.level = self.enemy_level
                enemy_monster.set_level(self.enemy_level)
                enemy_monster.current_hp = enemy_monster.hp
                enemy_npc.monsters = [enemy_monster]
            
            # Adjust enemy monster level if needed
            if enemy_npc.monsters:
                enemy_npc.monsters[0].level = self.enemy_level
                enemy_npc.monsters[0].set_level(self.enemy_level)
                enemy_npc.monsters[0].current_hp = enemy_npc.monsters[0].hp
            
            # Set up battle environment
            env = EnvironmentModel.lookup("grass", db)
            
            # Create battle context
            context = CombatContext(
                session=session,
                teams=[player, enemy_npc],
                combat_type="trainer",
                graphics=env.battle_graphics,
                battle_mode="single",
            )
            
            # Start the battle
            print("🎯 Launching battle state...")
            self.push_state("CombatState", context=context)
            
            # Play battle music
            self.event_engine.execute_action("play_music", [env.battle_music], True)
            
            print("✅ Battle started successfully!")
            print("\n🎮 Use the game window to test riddle combat!")
            
        except Exception as e:
            print(f"❌ Error setting up battle: {e}")
            import traceback
            traceback.print_exc()
            self.exit = True
    
    def process_events(self):
        """Handle events with helpful information"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("\n👋 Exiting battle test...")
                self.exit = True
                return
            
            # Convert pygame event to PlayerInput
            input_event = PlayerInput()
            
            if event.type == pygame.KEYDOWN:
                input_event.pressed = True
                input_event.button = event.key
                input_event.unicode = getattr(event, 'unicode', '')
                
                # Show helpful key info
                if event.key == pygame.K_ESCAPE:
                    print("🔙 ESC pressed - this will cancel riddles or exit menus")
                elif event.key == pygame.K_RETURN:
                    print("✅ ENTER pressed - this will submit riddle answers")
                elif event.key == pygame.K_h:
                    print("💡 H pressed - this will show/hide riddle hints")
            
            elif event.type == pygame.KEYUP:
                input_event.pressed = False
                input_event.button = event.key
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                input_event.pressed = True
                input_event.button = event.button
                input_event.pos = event.pos
                print(f"🖱️  Mouse clicked at {event.pos}")
            
            elif event.type == pygame.MOUSEBUTTONUP:
                input_event.pressed = False
                input_event.button = event.button
                input_event.pos = event.pos
            
            # Send to the active state
            if hasattr(self, 'current_state') and self.current_state:
                self.current_state.process_event(input_event)


def main():
    """Main function to run the battle test"""
    parser = argparse.ArgumentParser(
        description="Test the Tuxemon riddle combat system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--npc", 
        default="npc_test",
        help="NPC opponent slug (default: npc_test)"
    )
    
    parser.add_argument(
        "--level", 
        type=int, 
        default=10,
        help="Player monster level (default: 10)"
    )
    
    parser.add_argument(
        "--monster",
        default="bamboon", 
        help="Player monster slug (default: bamboon)"
    )
    
    parser.add_argument(
        "--enemy-level",
        type=int,
        default=8,
        help="Enemy monster level (default: 8)"
    )
    
    parser.add_argument(
        "--list-monsters",
        action="store_true",
        help="List available monster slugs and exit"
    )
    
    parser.add_argument(
        "--list-npcs", 
        action="store_true",
        help="List available NPC slugs and exit"
    )
    
    args = parser.parse_args()
    
    # Handle list commands
    if args.list_monsters:
        print("Available monster slugs:")
        try:
            from pathlib import Path
            monster_dir = Path("mods/tuxemon/db/monster")
            if monster_dir.exists():
                monsters = [f.stem for f in monster_dir.glob("*.json")]
                for i, monster in enumerate(sorted(monsters), 1):
                    print(f"  {i:3d}. {monster}")
            else:
                print("  Monster directory not found")
        except Exception as e:
            print(f"  Error listing monsters: {e}")
        return
    
    if args.list_npcs:
        print("Available NPC slugs:")
        try:
            from pathlib import Path
            npc_dir = Path("mods/tuxemon/db/npc")
            if npc_dir.exists():
                npcs = [f.stem for f in npc_dir.glob("*.json")]
                for i, npc in enumerate(sorted(npcs), 1):
                    print(f"  {i:3d}. {npc}")
            else:
                print("  NPC directory not found")
        except Exception as e:
            print(f"  Error listing NPCs: {e}")
        return
    
    # Validate arguments
    if args.level < 1 or args.level > 100:
        print("❌ Player level must be between 1 and 100")
        return
    
    if args.enemy_level < 1 or args.enemy_level > 100:
        print("❌ Enemy level must be between 1 and 100") 
        return
    
    try:
        # Initialize and run the test client
        print("🚀 Initializing battle test client...")
        client = BattleTestClient(
            player_monster=args.monster,
            player_level=args.level,
            enemy_npc=args.npc,
            enemy_level=args.enemy_level
        )
        
        print("🎮 Starting main game loop...")
        client.main()
        print("🛑 Main loop exited")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error running battle test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()