Tuxemon Riddle Edition
=====================

**A fork of Tuxemon that replaces traditional monster battles with riddle-based combat!**

This is a modified version of the free, open source monster-fighting RPG [Tuxemon](https://github.com/Tuxemon/Tuxemon) that transforms the combat system from technique-based battles into an engaging riddle-solving experience.

[![Build Status](https://travis-ci.org/Tuxemon/Tuxemon.svg?branch=development)](https://travis-ci.org/Tuxemon/Tuxemon)
[![Documentation Status](https://readthedocs.org/projects/tuxemon/badge/?version=latest)](https://tuxemon.readthedocs.io/en/latest/?badge=latest)

![screenshot](https://www.tuxemon.org/images/featurette-01.png)


🧩 Riddle Edition Features
--------------------------

**New Riddle Combat System:**
- **Answer riddles instead of selecting techniques** - solve logic puzzles, brain teasers, and math problems to deal damage
- **20 challenging riddles** across 13 categories: logic, deduction, paradox, mystery, chess, patterns, and more
- **3 difficulty levels** with intelligent scaling based on monster level and type
- **Smart AI opponents** that solve riddles with realistic success rates
- **Interactive riddle UI** with hints, answer validation, and immediate feedback

**Original Tuxemon Features:**
- Game data is all json, easy to modify and extend
- Game maps are created using the Tiled Map Editor  
- Simple game script to write the story
- Dialogs, interactions on map, npc scripting
- Localized in several languages
- Seamless keyboard, mouse, and gamepad input
- Animated maps
- Lots of documentation
- Python code can be modified without a compiler
- CLI interface for live game debugging
- Runs on Windows, Linux, OS X, and some support on Android
- 183 monsters with sprites
- ~~98 techniques to use in battle~~ → **20 logic riddles to solve in combat**
- 221 NPC sprites
- 18 items

## 🎮 How Riddle Combat Works

When you encounter a battle, instead of selecting "Fight" and choosing techniques, you'll see an "Answer Riddle" button. Click it to:

1. **Read the riddle** - Logic puzzles, brain teasers, math problems, and classic riddles
2. **Type your answer** - Case-insensitive with support for alternative answers  
3. **Get instant feedback** - Correct answers damage enemies, wrong answers damage you
4. **Use hints** - Press 'H' during riddles for helpful clues
5. **Think strategically** - Harder riddles deal more damage but are riskier to attempt

### Example Riddles by Difficulty:

**Easy:** "A man lives on the 20th floor of an apartment building. Every morning he takes the elevator down to the ground floor. When he comes home, he takes the elevator to the 10th floor and walks the rest of the way... except on rainy days, when he takes the elevator all the way to the 20th floor. Why?"

**Medium:** "Three friends check into a hotel room that costs $30. They each pay $10. Later, the manager realizes the room only costs $25 and gives the bellhop $5 to return. The bellhop keeps $2 as a tip and gives each friend $1 back. Now each friend paid $9 (totaling $27) and the bellhop kept $2. That's $29. Where did the missing dollar go?"

**Hard:** "You have 12 balls that look identical. 11 weigh the same, but one is either heavier or lighter. You have a balance scale and can use it exactly 3 times. How do you find the different ball and determine if it's heavier or lighter?"


Installation
------------

To try the Riddle Edition, clone this repository and run locally. Requires Python 3.9+ and git.

### Quick Start (All Platforms)

```shell
git clone https://github.com/[your-username]/Tuxemon.git
cd Tuxemon
git checkout riddle
```

### Windows Source

Install the latest version of Python 3 from
[here](https://www.python.org/downloads/)
and the latest version of Git from [here](https://git-scm.com/downloads)

Run:
```shell
py -3 -m pip install -U -r requirements.txt
py -3 run_tuxemon.py
```

### macOS with [uv](https://github.com/astral-sh/uv) (Recommended)

```shell
brew install uv python git sdl sdl2_image sdl2_ttf sdl2_mixer portmidi libvorbis
uv sync
uv run python run_tuxemon.py
```

### Windows Binary

NOTICE: Windows binaries currently do not work (see https://github.com/Tuxemon/Tuxemon/issues/1229)

In the meantime please use the windows source instructions above to run Tuxemon directly from source.


### Flatpak

Check the [web page](https://flathub.org/apps/details/org.tuxemon.Tuxemon) for a complete explanation.

Before installing Tuxemon, make sure you have all the Flatpak [requirements](https://www.flatpak.org/setup/) installed.

*Command line install:*
```shell
flatpak install flathub org.tuxemon.Tuxemon
flatpak run org.tuxemon.Tuxemon
```
*Using Discover (Graphical Software Manager)*

1. Install Discover using your system's package manager. 
2. Once installed, open Discover and search for 'Tuxemon', select the Tuxemon entry and press install.

*Flatpak Nightly Builds*

1. Download Tuxemon.flatpak file from the [Release Latest Build (Development) Section](https://github.com/Tuxemon/Tuxemon/releases/tag/latest).
2. Using your terminal, navigate to the directory where the Tuxemon.flatpak file was downloaded to.
3. Run the following commands:

```shell

flatpak install Tuxemon.flatpak

flatpak run org.tuxemon.Tuxemon

```
Depending on your desktop environment, you may also be able to launch via your start menu.


### Debian/Ubuntu with virtual environment

This is the recommended way to run because it will not modify the
system.
```shell
sudo apt install git python3-venv
git clone https://github.com/[your-username]/Tuxemon.git
cd Tuxemon
git checkout riddle
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -U -r requirements.txt
python3 run_tuxemon.py
```

## 🧪 Testing the Riddle System

The Riddle Edition includes comprehensive testing tools:

### Test Scripts

```shell
# Test the riddle system components
uv run python riddle_system_test.py

# Quick battle test (launches directly into riddle combat)
uv run python quick_battle_test.py

# Full battle test with customizable options
uv run python test_riddle_battle.py --level 15 --monster tux --npc red
```

### In-Game Testing

1. Start the game normally: `uv run python run_tuxemon.py`
2. Press `~` to open the console
3. Type: `trainer_battle npc_test` to start a riddle battle
4. Look for the "Answer Riddle" button instead of "Fight"!

See [RIDDLE_BATTLE_TESTING.md](RIDDLE_BATTLE_TESTING.md) for comprehensive testing instructions.

### Debian/Ubuntu

*Not recommended* because it will change system-installed packages
```shell
sudo apt install python3 python3-pygame python3-pip python3-imaging git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
sudo pip3 install -U -r requirements.txt
python3 run_tuxemon.py
```

*Debian/Ubuntu optional rumble support*

```shell
sudo apt install build-essential
git clone https://github.com/zear/libShake.git
cd libShake/
make BACKEND=LINUX; sudo make install BACKEND=LINUX
```

### Fedora Linux

```shell
sudo dnf install SDL2*-devel freetype-devel libjpeg-devel portmidi-devel python3-devel
git clone https://github.com/Tuxemon/Tuxemon.git
python3 -m venv venv
source venv/bin/activate
cd Tuxemon
python3 -m pip install -U -r requirements.txt
python3 run_tuxemon.py
```

### Arch Linux

An [AUR package](https://aur.archlinux.org/packages/tuxemon-git/) is availible however manual installation is reccomended.

```shell
sudo pacman -S python python-pip python-pillow python-pygame python-pydantic git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
python -m pip install -U -r requirements.txt
python run_tuxemon.py
```


### Smartphones

Android builds are highly experimental. You will have to build Tuxemon yourself
using the script located in the buildconfig folder.
After this you will need to manually install the mods folder via the following instructions.
Connect your device to your computer and make a folder called
"Tuxemon" in "Internal Storage", then copy the mods folder.  Tuxemon
will also need file system permissions, which you can set in your phones
settings.

Caveat Emptor

### Mac OS X (Yosemite)

```shell
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew tap Homebrew/python
brew update
brew install python
brew install sdl sdl_image sdl_ttf portmidi git
brew install sdl_mixer --with-libvorbis
sudo pip install git+https://github.com/pygame/pygame.git
sudo pip install -U -r requirements.txt
git clone https://github.com/Tuxemon/Tuxemon.git
ulimit -n 10000; python run_tuxemon.py
```

### macOS Sequoia with [uv](https://github.com/astral-sh/uv)

```shell
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew update
brew install uv python git sdl sdl2_image sdl2_ttf sdl2_mixer portmidi libvorbis
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
uv sync
uv run python run_tuxemon.py
```

Controls
--------

##### Game Controls
###### You can also set inputs in the options menu or config file
* *Arrow Keys* - Movement
* *Enter* - Select/activate
* *ESC* - Menu/Cancel
* *Shift* - Sprint

##### Debugging

You can enable dev_tools by changing `dev_tools` to `True` in the
`tuxemon.yaml` file:

```
[game]
dev_tools = True
```

These keyboard shortcuts are available with dev tools enabled
* *r* - Reload the map tiles
* *n* - No clip

##### Map Editor

Use *Tiled* map editor: https://www.mapeditor.org/


CLI Interface
--------------

The CLI interface is a very convenient way to debug and develop your
maps. After you enable the CLI interface, you can use the terminal to
enter commands.  You could, for example, give your self potions to
battle, or add a monster directly to your party.  It's also possible to
change game variables directly.  In fact, any action or condition that
is usable in the map can be used with the CLI interface.

### Setting up

You can enable cli by changing `cli_enabled` to `True` in the
`tuxemon.yaml` file:

```
[game]
cli_enabled = True
```

### Commands

- `help [command_name]` — Lists all commands, or specific information on a command.
- `action <action_name> [params]` — Execute EventAction.  Uses same syntax as the map script.
- `test <condition_name> [params]` — Test EventCondition.  Uses same systax as the map script.
- `random_encounter` — Sets you in a wild tuxemon battle, similar to walking in tall grass.
- `trainer_battle <npc_slug>` — Sets you in a trainer battle with specified npc.
- `quit` — Quits the game.
- `whereami` — Prints out the map filename
- `shell` — Starts the Python shell, that you can use to modify the game directly. For advanced users.

### CLI Examples

Get Commands

```
> help
Available Options
=================
action  help  quit  random_encounter  shell  test  trainer_battle  whereami

Enter 'help [command]' for more info.
```

Get help on an action

```
> help action teleport

    Teleport the player to a particular map and tile coordinates.

    Script usage:
        .. code-block::

            teleport <map_name>,<x>,<y>

    Script parameters:
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
```

Test and give an item
```
> test has_item player,potion
False
> action add_item potion,1
> test has_item player,potion
True
```

**NOTE!**  The CLI interface is new and the error messages are not very
helpful. In general, you should be using the commands when the game is
playing, and you are on the world map.


Check out the
[scripting reference](https://tuxemon.readthedocs.io/en/latest/handcrafted/scripting.html) 
for all the available actions and conditions for use with `action` and `test`!


Building
--------

There are many scripts for various builds in the buildconfig folder. 
These are meant to be run from the project root directory, for example,
to build the portable pypy build:

```shell
[user@localhost Tuxemon]$ buildconfig/build_pypy_portable_linux.sh
```

There will be a new directory called build, which will have the package
if everything was successful.

WARNING!  The build scripts are designed to be run in a dedicated VM.
They will add and remove packages and could leave your OS in a bad
state.  You should not use them on your personal computer.  Use in a vm
or container.

License
-------

With the exception of the lib folder which may have its own license, all
code in this project is licenced under [the GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).

GPL v3+

Copyright (C) 2014-2025 William Edwards <shadowapex@gmail.com>,
Benjamin Bean <superman2k5@gmail.com>

This software is distributed under the GNU General Public Licence as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.  See the file
[LICENSE](LICENSE) for the conditions under which this software is made
available.  Tuxemon also contains code from other sources.


## 🔗 About the Original Tuxemon

This Riddle Edition is a fork of the amazing [Tuxemon](https://github.com/Tuxemon/Tuxemon) project. The original Tuxemon is a free, open source monster-fighting RPG that inspired this educational twist on the combat system.

**Original Tuxemon Links:**
* Official website: [tuxemon.org](https://www.tuxemon.org)
* GitHub: [github.com/Tuxemon/Tuxemon](https://github.com/Tuxemon/Tuxemon)
* Matrix: [Tuxemon](https://matrix.to/#/!ktrcrHpgkDOGCQOlxX:matrix.org)
* Discord: [Tuxemon](https://discord.gg/3ZffZwz)
* Reddit: [/r/Tuxemon](https://www.reddit.com/r/tuxemon)
* YouTube: [Tuxemon](https://www.youtube.com/channel/UC6BJ6H7dB2Dpb8wzcYhDU3w)
* Documentation: https://tuxemon.readthedocs.io/en/latest/

**Why a Riddle Edition?**

While the original Tuxemon focuses on traditional monster-battling RPG mechanics, this fork explores how the same engaging world and characters can be used to create an educational experience. By replacing combat techniques with riddles and logic puzzles, players exercise their minds while enjoying the classic RPG adventure.

The riddle system maintains all the strategic depth of the original combat - monster levels affect riddle difficulty, different monster types get different categories of riddles, and there's still the same risk/reward decision-making. But instead of memorizing type matchups and move lists, players develop critical thinking and problem-solving skills.

**Contributing**

This is an experimental fork focused on educational gameplay. For the main Tuxemon project with traditional RPG combat, please visit the [original repository](https://github.com/Tuxemon/Tuxemon). The original Tuxemon team welcomes contributors of all skill levels!
