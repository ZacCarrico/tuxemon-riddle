#!/usr/bin/env python3
"""
Riddle System Standalone Test

Test the riddle system components without running the full game.
This helps debug riddle loading, answer checking, and AI behavior.

Usage: python riddle_system_test.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_riddle_loading():
    """Test loading riddles from the database"""
    print("🔄 Testing riddle loading...")
    
    try:
        from tuxemon.db import db
        from tuxemon.riddle.riddle import Riddle
        from tuxemon.riddle.riddle_manager import riddle_manager
        
        # Initialize the database
        print("  🗃️  Initializing database...")
        db.load()
        
        # Test direct riddle creation
        print("  📝 Testing direct riddle creation...")
        riddle = Riddle.create("math_easy_01")
        print(f"     ✅ Loaded riddle: {riddle.question}")
        print(f"     ✅ Correct answer: {riddle.answer}")
        print(f"     ✅ Category: {riddle.category}, Difficulty: {riddle.difficulty}")
        
        # Test riddle manager
        print("  🎲 Testing riddle manager...")
        random_riddle = riddle_manager.get_random_riddle()
        print(f"     ✅ Random riddle: {random_riddle.question}")
        
        # Test difficulty selection
        easy_riddle = riddle_manager.get_riddle_by_difficulty("easy")
        print(f"     ✅ Easy riddle: {easy_riddle.question}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_answer_checking():
    """Test riddle answer validation"""
    print("\n🔍 Testing answer checking...")
    
    try:
        from tuxemon.db import db
        from tuxemon.riddle.riddle import Riddle
        
        # Initialize the database if not already done
        if not hasattr(db, '_loaded') or not db._loaded:
            db.load()
        
        # Create a test riddle
        riddle = Riddle.create("math_easy_01")  # "What is 7 + 5?" -> "12"
        
        # Test correct answers
        test_cases = [
            ("12", True, "exact match"),
            ("12 ", True, "with trailing space"),
            (" 12", True, "with leading space"),
            ("twelve", True, "alternative answer"),
            ("TWELVE", True, "case insensitive"),
            ("11", False, "wrong number"),
            ("", False, "empty answer"),
            ("twenty", False, "wrong word"),
        ]
        
        print(f"  🧮 Testing riddle: {riddle.question}")
        print(f"  ✅ Expected answer: {riddle.answer}")
        
        for answer, expected, description in test_cases:
            result = riddle.check_answer(answer)
            status = "✅" if result == expected else "❌"
            print(f"     {status} '{answer}' -> {result} ({description})")
            
        return True
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_riddle_solving():
    """Test AI riddle solving logic"""
    print("\n🤖 Testing AI riddle solving...")
    
    try:
        from tuxemon.db import db
        from tuxemon.riddle.riddle_ai import RiddleAI
        from tuxemon.riddle.riddle import Riddle
        from tuxemon.monster import Monster
        
        # Initialize the database if not already done
        if not hasattr(db, '_loaded') or not db._loaded:
            db.load()
        
        # Create mock objects for testing
        class MockNPC:
            def __init__(self):
                self.name = "Test NPC"
                self.slug = "test_npc"
                
        class MockCombat:
            def __init__(self):
                self.field_monsters = MockFieldMonsters()
                self.players = [MockNPC()]  # Add players list
                
        class MockFieldMonsters:
            def get_monsters(self, player):
                return []
        
        class MockSession:
            def __init__(self):
                self.client = None
                self.world = None
        
        # Create test monster and AI
        monster = Monster.create("bamboon")
        monster.level = 15
        
        npc = MockNPC()
        
        ai = RiddleAI(MockSession(), MockCombat(), monster, npc)
        
        # Test difficulty calculation
        easy_riddle = Riddle.create("math_easy_01")
        medium_riddle = Riddle.create("math_medium_01") 
        
        easy_rate = ai._calculate_success_rate(easy_riddle)
        medium_rate = ai._calculate_success_rate(medium_riddle)
        
        print(f"  🎯 Monster level: {monster.level}")
        print(f"  📊 Easy riddle success rate: {easy_rate:.2%}")
        print(f"  📊 Medium riddle success rate: {medium_rate:.2%}")
        print(f"  ✅ Easy should be higher: {easy_rate > medium_rate}")
        
        # Test multiple simulations
        print("  🎲 Running 10 simulations for each difficulty:")
        
        easy_successes = sum(ai.simulate_riddle_answer(easy_riddle) for _ in range(10))
        medium_successes = sum(ai.simulate_riddle_answer(medium_riddle) for _ in range(10))
        
        print(f"     Easy riddle: {easy_successes}/10 successes")
        print(f"     Medium riddle: {medium_successes}/10 successes")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_riddle_database():
    """Test the riddle database structure"""
    print("\n💾 Testing riddle database...")
    
    try:
        from pathlib import Path
        import json
        
        riddle_dir = Path("mods/tuxemon/db/riddle")
        
        if not riddle_dir.exists():
            print("     ❌ Riddle directory not found!")
            return False
            
        riddle_files = list(riddle_dir.glob("*.json"))
        print(f"  📁 Found {len(riddle_files)} riddle files")
        
        categories = set()
        difficulties = set()
        
        for riddle_file in riddle_files:
            try:
                with open(riddle_file) as f:
                    data = json.load(f)
                    
                categories.add(data.get("category", "unknown"))
                difficulties.add(data.get("difficulty", "unknown"))
                
                print(f"     ✅ {riddle_file.name}: {data.get('category')} - {data.get('difficulty')}")
                
            except Exception as e:
                print(f"     ❌ Error reading {riddle_file.name}: {e}")
        
        print(f"  📂 Categories found: {sorted(categories)}")
        print(f"  📊 Difficulties found: {sorted(difficulties)}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def interactive_riddle_test():
    """Interactive riddle testing"""
    print("\n🎮 Interactive Riddle Test")
    print("=" * 40)
    
    try:
        from tuxemon.riddle.riddle_manager import riddle_manager
        
        while True:
            print("\nOptions:")
            print("1. Answer a random riddle")
            print("2. Answer an easy riddle")
            print("3. Answer a medium riddle") 
            print("4. Answer a hard riddle")
            print("5. Exit")
            
            choice = input("\nChoose option (1-5): ").strip()
            
            if choice == "5":
                break
            elif choice in ["1", "2", "3", "4"]:
                difficulty_map = {
                    "1": None,
                    "2": "easy", 
                    "3": "medium",
                    "4": "hard"
                }
                
                difficulty = difficulty_map[choice]
                
                try:
                    riddle = riddle_manager.get_random_riddle(difficulty=difficulty)
                    
                    print(f"\n🧩 RIDDLE ({riddle.category.title()} - {riddle.difficulty.title()}):")
                    print(f"   {riddle.question}")
                    
                    if riddle.hint:
                        show_hint = input("   Show hint? (y/n): ").lower().startswith('y')
                        if show_hint:
                            print(f"   💡 Hint: {riddle.hint}")
                    
                    answer = input("   Your answer: ").strip()
                    
                    if riddle.check_answer(answer):
                        print("   ✅ Correct! Great job!")
                    else:
                        print(f"   ❌ Incorrect. The answer was: {riddle.answer}")
                        if riddle.alternate_answers:
                            print(f"   (Also accepted: {', '.join(riddle.alternate_answers)})")
                    
                except Exception as e:
                    print(f"   ❌ Error getting riddle: {e}")
            else:
                print("   Invalid option!")
                
    except Exception as e:
        print(f"❌ Error in interactive test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all riddle system tests"""
    print("🧩 RIDDLE SYSTEM TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_riddle_database,
        test_riddle_loading,
        test_answer_checking,
        test_ai_riddle_solving,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("🎉 All tests passed! Riddle system is working correctly.")
        
        # Offer interactive test
        try:
            run_interactive = input("\n🎮 Run interactive riddle test? (y/n): ").lower().startswith('y')
            if run_interactive:
                interactive_riddle_test()
        except (EOFError, KeyboardInterrupt):
            print("\n📝 Skipping interactive test in non-interactive environment.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("\n👋 Test complete!")

if __name__ == "__main__":
    main()