# 🧩 Riddle Battle Testing Guide

This guide explains how to test the new riddle-based combat system in Tuxemon.

## Quick Start

### Option 1: Automated Test Script
```bash
# Run the comprehensive test script
python test_riddle_battle.py

# Or with custom options
python test_riddle_battle.py --level 15 --monster tux --npc red
```

### Option 2: Quick Battle Test
```bash
# Instant battle setup
python quick_battle_test.py
```

### Option 3: Manual Testing in Game
```bash
# Start the game normally
uv run python run_tuxemon.py

# Then use the console (~ key) to start a battle:
trainer_battle npc_test
```

## What to Test

### 🎯 Core Riddle System
- [ ] **Answer Riddle Button**: Verify "Fight" is replaced with "Answer Riddle"
- [ ] **Riddle Display**: Check that riddles appear with proper formatting
- [ ] **Answer Input**: Test typing answers and submitting with ENTER
- [ ] **Hint System**: Press 'H' to toggle hints during riddles
- [ ] **Correct Answers**: Verify correct answers deal damage to enemy
- [ ] **Wrong Answers**: Verify wrong answers damage your monster
- [ ] **Case Sensitivity**: Test that answers work regardless of case
- [ ] **Alternative Answers**: Test alternate accepted answers (e.g., "4" vs "four")

### 🤖 AI Behavior
- [ ] **AI Riddle Turns**: Verify AI takes riddle-based turns
- [ ] **Success Rates**: Check AI succeeds/fails at realistic rates
- [ ] **Level Scaling**: Higher level monsters should be better at riddles
- [ ] **Type Bonuses**: Different monster types should prefer different riddle categories

### 🎮 Battle Flow
- [ ] **Turn Order**: Riddle turns should follow normal combat order
- [ ] **Damage Calculation**: Riddle damage should scale with difficulty
- [ ] **Victory/Defeat**: Battles should end normally when a side wins
- [ ] **Other Options**: Item, Swap, Run/Forfeit should still work

### 🧠 Riddle Categories & Difficulty
- [ ] **Math Riddles**: Test addition, subtraction, multiplication, word problems
- [ ] **Logic Riddles**: Test reasoning and puzzle riddles
- [ ] **Wordplay Riddles**: Test language and word-based riddles
- [ ] **Easy Difficulty**: Level 1-10 monsters should get easy riddles
- [ ] **Medium Difficulty**: Level 11-25 monsters should get medium riddles
- [ ] **Hard Difficulty**: Level 26+ monsters should get hard riddles

### 🎨 UI/UX Testing
- [ ] **Riddle Window**: Check layout and readability
- [ ] **Input Field**: Verify cursor and text input work properly
- [ ] **Feedback Messages**: Check correct/incorrect answer feedback
- [ ] **Transition Smoothness**: Verify smooth transitions between states
- [ ] **Escape Handling**: ESC should cancel riddles (counts as wrong)

## Testing Scenarios

### Scenario 1: Basic Functionality
1. Start a battle against `npc_test`
2. Click "Answer Riddle"
3. Answer correctly and verify damage to enemy
4. Answer incorrectly and verify damage to self
5. Use hint system
6. Complete the battle

### Scenario 2: Different Difficulty Levels
1. Test with Level 5 monster (should get easy riddles)
2. Test with Level 15 monster (should get medium riddles)  
3. Test with Level 30 monster (should get hard riddles)
4. Verify appropriate difficulty scaling

### Scenario 3: Monster Type Bonuses
1. Use Metal/Earth type monster (should get more math riddles)
2. Use Aether/Wood type monster (should get more logic/wordplay riddles)
3. Verify type-appropriate riddle selection

### Scenario 4: AI Intelligence
1. Battle multiple opponents with different levels
2. Observe AI success rates (should vary by level)
3. Verify AI doesn't always succeed or always fail
4. Check that AI behavior feels realistic

### Scenario 5: Edge Cases
1. Test very long answers
2. Test empty answers
3. Test special characters
4. Test rapid ESC/ENTER presses
5. Test hint toggling during answer input

## Available Test Commands

### Battle Test Script Options
```bash
# List available monsters
python test_riddle_battle.py --list-monsters

# List available NPCs  
python test_riddle_battle.py --list-npcs

# Custom battle setup
python test_riddle_battle.py --monster tux --level 20 --npc red --enemy-level 18
```

### In-Game Console Commands
```
# Open console with ~ key, then use:
trainer_battle <npc_name>      # Start battle with specific NPC
create_npc <npc> <x> <y>       # Create NPC at coordinates
start_battle <npc>             # Start battle with existing NPC
remove_npc <npc>               # Remove NPC after battle
```

## Common Issues & Solutions

### ❌ "No riddles found" Error
- **Cause**: Riddle database not loaded properly
- **Solution**: Check that riddle JSON files exist in `mods/tuxemon/db/riddle/`

### ❌ "Animation not found" Error  
- **Cause**: Riddle techniques reference invalid animations
- **Solution**: Animations set to `null` in riddle technique files

### ❌ Translation Errors
- **Cause**: Missing translations for riddle UI elements
- **Solution**: Compile translations with `msgfmt base.po -o base.mo`

### ❌ AI Not Using Riddles
- **Cause**: AI still using old technique system
- **Solution**: Verify `riddle_ai.py` is imported and used in `ai.py`

### ❌ Input Not Working
- **Cause**: Event handling issues in riddle state
- **Solution**: Check that `process_event` method handles keyboard input properly

## Expected Behavior

✅ **Working System Should Show**:
- "Answer Riddle" button instead of "Fight"
- Riddles appropriate to monster level and type
- Smooth input and feedback
- Realistic AI riddle-solving behavior
- Proper damage calculation based on riddle difficulty
- Normal battle flow with riddle-based turns

✅ **Performance Characteristics**:
- Easy riddles: ~80-90% player success rate
- Medium riddles: ~60-70% player success rate  
- Hard riddles: ~40-50% player success rate
- AI success rates scale with monster level (30% to 90%)

## Reporting Issues

When reporting bugs, please include:
1. What you were testing
2. What you expected to happen
3. What actually happened
4. Console error messages (if any)
5. Monster levels and types involved
6. Steps to reproduce the issue

Happy testing! 🎮🧩