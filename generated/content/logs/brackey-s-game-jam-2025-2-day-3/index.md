---
title: Brackey’s Game Jam 2025.2 – Day 3
date: '2025-08-27'
description: A shorter development day still brought coin counters, a bat enemy, and
  a reusable killzone.
url: /brackeys-game-jam-2025-2-day-3/
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

Progress was a little slower today (kids don’t always sync with jam schedules 😅), but I still managed to add some important pieces that bring the game closer to feeling like an actual *game*.

## **What I built today**

- **UI**- Added a counter to display collected coins.
- Added a counter to display banked coins.
- **Enemy**- Added a simple bat enemy to the scene.
- Introduced a killzone mechanic for it.
- **Killzone (Reusable)**- Built a reusable killzone scene: an Area2D node with a script that calls GameState.die().
- Any hazard can now just drop in this kill zone and add a CollisionShape2D to match the hazard size.
- Implemented GameState.die() to reset collected coins to 0.
- Added a “hit” sound effect on death.
- On death, the level resets to the beginning.

## **Reflections**

Today was the first day hazards came online. Even though the system is still basic, just having something that can kill the player suddenly makes the loop more engaging. The reusable kill zone approach also feels like a solid foundation for adding new hazards quickly without duplicating logic.

Tomorrow I’d like to start finishing up the basics: remove the already collected gems from the level when you die and restart. Next up is building an actual level for the Game Jam players to play.

With that I believe I have a good MVP to upload before I start adding more.

Catch you in the next log.
