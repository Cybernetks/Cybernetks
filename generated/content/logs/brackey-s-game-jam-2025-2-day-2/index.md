---
title: Brackey’s Game Jam 2025.2 – Day 2
date: '2025-08-26'
description: Moving beyond tutorials and experimenting directly with Godot as the
  game starts to take shape.
url: /brackeys-game-jam-2025-2-day-2/
topics:
- build-log
projects:
- Alien Miner
aliases: []
params:
  kind: log
  type:
  - '[[Project - Alien Miner]]'
  - '[[Build Log]]'
---

Today felt like a turning point. Instead of following tutorials step by step, I started leaning on the docs and experimenting more with Godot directly. That shift made things click faster, I’m building *my game*, not just replaying Brackeys.

One neat discovery: using await lets me finish playing a sound before freeing up the node. Combine that with toggling sprite visibility and you can keep longer sounds around without the visuals lingering. I also learned that slightly randomizing pitch on repeat sounds makes them less annoying when triggered often, small trick, big impact.

## **What I built today**

- **Gems & Coins**- Added both with pickup animations.
- Each has its own pickup sound.
- Each has their own value.
- **Banker NPC**- Animates when you come close (power up) and when you leave (power down).
- Plays matching sounds for popping in/out.
- Shows a “Press E to bank” label when active.
- **Game**- Added a looping soundtrack.
- **Player**- Jump sound effect added.
- **GameState.gd (singleton)**- AutoLoaded script to track unbanked vs banked values.
- Coins and gems update the collected counter on pickup.
- Banked values update when interacting with the banker.
- Signals make it easy to update UI as events happen.
- No scene needed, it’s just a script that runs globally.

## **What's next?**

Next up is adding some UI to display the actual collected and banked coins. After that I will start working on "Hazards": at least 1 enemy and a death animation. If I can get these parts finished I should have everything I need to start building a decent level to play the game.

Depending on time, I'd also like to add a simple menu and maybe a second level.

## **Reflections**

It feels good to see the systems starting to connect: collectibles, banker, counters, and sounds all feeding into one loop. No hazards yet, so it’s not really a *game* — but the skeleton is standing, and that’s the hardest part.

Catch you in the next log.
