---
title: 'Learning Godot: My First Deep Dive into GDScript'
date: '2025-08-23'
description: A first look at GDScript through Brackeys’ tutorial, exploring the syntax
  and workflow behind Godot.
url: /learning-godot-my-first-deep-dive-into-gdscript/
topics:
- build-log
- dev-notes
projects: []
aliases: []
params:
  kind: log
  type:
  - '[[Build Log]]'
  - '[[Dev Notes]]'
---

This week I wrapped up Brackeys’ [*How to program in Godot - GDScript tutorial*](https://www.youtube.com/watch?v=e1zJS31tr88), a one-hour overview that breaks down how Godot’s scripting language works under the hood. It’s not a full tutorial in the “build a game” sense, but it was a perfect starting point for me to get comfortable with the syntax and workflow.

### **What stood out to me**

- **Python-like syntax**: GDScript feels approachable if you’ve worked in Python before. Indentation matters, and the language is designed to be clean and fast to read. As someone who's interested in learning Python, this feels like a good in-between step.
- **Everything is a Node**: Classes/scripts are tied directly to Godot’s node system, which makes game logic feel closely connected to the scene tree. On the other hand it feels like building reusable components can get complicated rather fast. I still need to dive deeper into this part.
- **Signals & Groups**: These stood out as powerful built-ins for handling events and communication between nodes without creating spaghetti code.
- **Export variables**: Being able to expose script values directly in the editor is going to save a lot of tweaking time. I still need to get a feel for when to export and when to keep things script-side.

### **My takeaways**

What I liked most is how much Godot encourages you to think modularly. The combination of nodes + scripts means you’re essentially building with Lego bricks. Attach a little behavior here, connect it with a signal there, and suddenly you’ve got gameplay.

I’m still early in this journey, but finishing this intro gave me a clear mental map of what GDScript can do and how it does it. As someone who already programs for a living, this makes it easier to get started with the Engine.

### **What’s next**

As said in [the previous post](/first-steps-into-game-development/) I'll be entering [Brackeys Game Jam 2025.2](https://itch.io/jam/brackeys-14) which starts tomorrow Sunday August 24th.

I'll probably set up a Trello board to keep track of the things I need and want to do for the game. That way I can start brainstorming as soon as the theme is revealed.

I also found another [Ultimate introduction to Godot 4](https://www.youtube.com/watch?v=nAh_Kx5Zh5Q) tutorial that seems highly praised. I'll probably dip into specific sections when I need them, while keeping my main focus on building for the jam.

Catch you in the next log.
