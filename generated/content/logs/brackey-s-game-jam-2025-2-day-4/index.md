---
title: Brackey’s Game Jam 2025.2 – Day 4
date: '2025-08-28'
description: 'End gates give the game a goal: bank enough gems to finish the level,
  or risk losing the run.'
url: /brackeys-game-jam-2025-2-day-4/
topics:
- build-log
projects:
- Alien Miner
aliases: []
params:
  kind: log
---

Day 4 brought a big breakthrough: the game finally has a *point*. Until now, you could collect gems, bank them, and even die but there wasn’t a real **goal**. That changed with the introduction of **end gates**.

Now, to finish a level you’ll need to bank a required amount of gems. If you die and lose your collection, it’s no longer just a slap on the wrist, it could mean failing the run. Suddenly, the “risk it for the biscuit” theme clicks into place.

## **What I built today**

- **On Death**- The player now respawns at the starting position.
- Achieved by injecting the Player node into the global GameState, letting the KillZone call die() directly.
- This also means collected coins remain hidden after death, without needing to reload the scene.
- **Assets**- Added a background layer to give the game view more depth.
- Adjusted UI colors/layout to make sure text stays visible against the background.
- **End Gate**- Added an end gate as the new level goal.
- Requires banking a set number of coins to open.
- Integrated with the UI via a new **notification label** that tells the player how many more coins they need to bank.
- **UI**- Reworked layout so counters and notifications fit logically together.
- Added notification label for context-sensitive messages (e.g., end gate requirements).

## **Notes**

- Injecting the Player node into GameState not only solved respawning but also sets up future **checkpoints**. That will make later levels less punishing.
- Adding the **end gate** solved the missing piece of the game loop. There’s now a real reason to collect, bank, and survive.

## **What’s next?**

- Build the **first full level**.
- Make the current enemy move (instead of just hovering).
- Experiment with adding a second enemy type.

## **Reflections**

The project has gone from “sandbox of mechanics” to “actual game structure.” With hazards, banking, and end gates all in place, I finally feel confident calling this an MVP loop. Next step is to package it into a level that shows off the theme.

Catch you in the next log.
