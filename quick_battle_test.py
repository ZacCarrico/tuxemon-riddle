#!/usr/bin/env python3
"""
Quick Riddle Battle Test

Simple script to quickly launch into a riddle battle for testing.
Just run it and you'll be in a battle immediately!

Usage: python quick_battle_test.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Launch directly into a riddle battle"""
    
    print("🧩 QUICK RIDDLE BATTLE TEST")
    print("=" * 40)
    print("Starting battle in 3 seconds...")
    print("Use 'Answer Riddle' instead of 'Fight'!")
    print("=" * 40)
    
    try:
        # Import Tuxemon after path setup
        from tuxemon.main import main as tuxemon_main
        from tuxemon.session import local_session
        
        # Monkey patch to auto-start battle
        original_startup = None
        
        def auto_battle_startup(client_self):
            """Auto-start a battle after normal startup"""
            # Call original startup first
            if original_startup:
                original_startup(client_self)
            
            # Give the game a moment to initialize
            import threading
            import time
            
            def delayed_battle():
                time.sleep(2)  # Wait for initialization
                try:
                    # Execute battle setup commands
                    action = client_self.event_engine.execute_action
                    
                    # Create a test NPC and start battle
                    action("create_npc", ["npc_test", 5, 5], True)
                    action("start_battle", ["npc_test"], True)
                    
                    print("✅ Auto-battle started!")
                    print("🎮 Click 'Answer Riddle' to test the system!")
                    
                except Exception as e:
                    print(f"❌ Auto-battle failed: {e}")
                    # Try alternative approach
                    try:
                        # Use CLI command instead
                        if hasattr(client_self, 'cli_commands'):
                            client_self.cli_commands['trainer_battle'].invoke(
                                client_self, "npc_test"
                            )
                    except Exception as e2:
                        print(f"❌ Alternative auto-battle failed: {e2}")
            
            # Start battle in background thread
            threading.Thread(target=delayed_battle, daemon=True).start()
        
        # Patch the client startup
        from tuxemon.client import LocalPygameClient
        if hasattr(LocalPygameClient, 'startup'):
            original_startup = LocalPygameClient.startup
            LocalPygameClient.startup = auto_battle_startup
        
        # Run the game normally
        tuxemon_main()
        
    except ImportError as e:
        print(f"❌ Failed to import Tuxemon: {e}")
        print("Make sure you're running from the Tuxemon directory!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()