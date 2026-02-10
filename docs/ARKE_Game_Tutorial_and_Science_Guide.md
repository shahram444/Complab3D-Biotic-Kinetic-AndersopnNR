# ARKE: Guardians of Earth
## Complete Game Tutorial & Science Guide

*An educational game based on CompLaB3D pore-scale biogeochemical reactive transport research*
*University of Georgia*

---

# PART 1: GAME TUTORIAL

## 1.1 What Is This Game?

You play as **ARKE** (from Greek "arkhē" = beginning/origin, the root of "Archaea"), a tiny methanotrophic archaea (a single-celled microorganism) living inside the pore spaces between soil and rock grains deep underground. Your mission: **eat substrates, grow biomass, place colonies, and prevent greenhouse gases (methane CH4 and nitrous oxide N2O) from reaching the atmosphere.**

The game is based on real science from the CompLaB3D research framework, which simulates how microbes grow, consume chemicals, and form biofilms inside porous media at the pore scale.

### How the Pore World Works

The game world represents a cross-section of subsurface porous media:
- **Brown tiles** = Solid grains (rock/soil particles) - you CANNOT pass through these
- **Dark blue/black tiles** = Pore space (water-filled gaps between grains) - this is where you live and move
- **Flow direction** = Water flows **from LEFT (inlet, high pressure) to RIGHT (outlet, low pressure)**, just like in real groundwater systems driven by hydraulic pressure gradients
- **"IN" label** = Inlet on the left edge - where water and nutrients ENTER the pore network (marked with blue pulsing bar and animated arrows)
- **"OUT" label** = Outlet on the right edge - where water EXITS (marked with green pulsing bar)
- **Blue arrows on tiles** = Subtle flow direction indicators showing which way water moves (visible by default; press Q for detailed science overlay)
- **Purple/magenta tiles** = **TOXIC ZONES** - areas with accumulated hydrogen sulfide (H2S) and reactive chemical species (see section 1.8 below)

Substrates (food) primarily **spawn at the inlet** and are **carried by water flow** through the pore network. They cannot pass through solid grains - they follow the open pore channels. This means **following the flow direction leads you to food!**

---

## 1.2 Controls

| Key | Action | Description |
|-----|--------|-------------|
| **Arrow Keys** or **WASD** | Move | Navigate ARKE through pore spaces between grains |
| **SPACE** | Divide | Place a colony when your Growth bar is full |
| **SHIFT** (hold) | Ride Flow | Enter planktonic mode - travel along water flow currents at 2x speed |
| **Q** | Science Mode | Toggle science overlay showing flow arrows and directions |
| **ESC** | Pause | Open the pause menu (Resume / Mute / Quit) |
| **ENTER** | Confirm | Advance dialogue, confirm selections, proceed through screens |
| **M** | Mute/Unmute | Toggle game audio on/off |

### Movement Details

- ARKE moves **tile by tile** through walkable pore spaces (the dark blue areas between brown grains)
- You **cannot** walk through solid grains (brown/dark tiles) or void areas
- Movement speed is **2.5 tiles per second** in normal mode
- In **planktonic mode** (SHIFT held), you ride water currents at **5 tiles per second** (2x multiplier), but it costs a small amount of energy (0.5 per move)

### When to Use SHIFT (Planktonic Mode)

Hold SHIFT when standing on a tile with water flow (indicated by the "[RIDING FLOW]" text in the HUD). This lets you:
- Travel quickly through long pore channels
- Reach distant food sources faster
- Escape from rivals chasing you

**Tip:** The HUD shows "SHIFT: ride flow" when you're standing on a flow tile and can ride it.

### When to Use Q (Science Mode)

Press Q to toggle the **Science Mode overlay**. This shows:
- Blue arrows indicating the direction and speed of water flow on each tile
- Larger/brighter arrows = faster flow
- Use this to plan your route - flow carries substrates, so following flow paths leads to food

**Tip:** Substrates spawn at inlet areas and flow through the pore network. Following the flow leads you to food!

---

## 1.3 Understanding the HUD (Heads-Up Display)

The HUD bar sits at the bottom of the screen and shows all your vital information.

### The Three Bars

```
 +-----------+
 | HP  [====]|  Health Points - your life force
 | EN  [====]|  Energy - fuel for movement
 | GR  [====]|  Growth - biomass accumulation
 +-----------+
```

#### HP Bar (Health Points) - Top Left
- **Maximum:** 100 HP
- **Color coding:**
  - **Green** (>60 HP): Healthy
  - **Yellow** (35-60 HP): Caution
  - **Orange** (15-35 HP): Danger
  - **Red/Flashing** (<15 HP): Critical! Find food immediately!
- **Drain:** You lose **1.5 HP per second** from starvation (your metabolism constantly burns energy)
- **Recovery:** Eating substrates restores HP (amount depends on substrate type)
- **Toxic damage:** Standing in toxic zones (purple/magenta areas) drains **20 HP per second**
- **Death:** When HP reaches 0, ARKE dies. The screen will show "MICROBE LOST"
- **Warning:** When HP drops below 30, the screen edges pulse red and "STARVING!" appears

#### EN Bar (Energy) - Middle Left
- **Maximum:** 100 Energy
- **Drain:** You lose **0.8 Energy per second** passively
- **Recovery:** Eating substrates restores Energy (half the substrate's energy value)
- **Planktonic cost:** Each flow-riding move costs 0.5 Energy
- **Purpose:** Energy fuels your ability to keep moving. When depleted, you still move but are running on fumes

#### GR Bar (Growth) - Bottom Left
- **Maximum:** 100 Growth (the "division cost")
- **No decay:** Unlike HP and Energy, Growth does NOT drain over time - biomass stays!
- **Filling:** Each substrate you eat adds to your Growth bar (different amounts per type)
- **When full:** The bar flashes **yellow/green** and the text "SPACE!" appears
- **SPACE to divide:** Press SPACE when Growth is full to place a colony
- **After division:** Growth resets to 0 and you start accumulating again

### Other HUD Elements

| Element | Location | Description |
|---------|----------|-------------|
| **Colony: X/Y** | Center-left | How many colonies you've placed vs. the level goal |
| **Score** | Top-right | Your current point total |
| **CH4: X** | Right side | Number of methane molecules eaten (climate impact!) |
| **Lv X** | Bottom-right | Current level number |
| **[SCIENCE: Q]** | Center | Shown when Science Mode is active |
| **[RIDING FLOW]** | Center | Shown when riding a water current |
| **Redox Ladder** | Center area | Shows available substrates and their energy values |
| **Minimap** | Bottom-right corner | Bird's-eye view of the level map with your position (blinking dot) |

### Minimap Legend
- **Brown dots:** Solid grains
- **Purple dots:** Toxic zones
- **Green dots:** Biofilm/colonies you've placed
- **Bright green dot:** Outlet
- **White/teal blinking dot:** Your position (ARKE)

---

## 1.4 How Biomass Division Works

Division is the core mechanic - it's how you win levels!

### Step by Step:

1. **Eat substrates** - Move over floating colored particles to consume them
2. **Watch the GR bar fill** - Each substrate adds Growth points:
   - CH4 (Methane, red): +25 Growth (most growth per eat!)
   - NO3 (Nitrate, green): +18 Growth
   - O2 (Oxygen, blue): +15 Growth
   - Mn(IV) (Manganese, purple): +12 Growth
   - Fe(III) (Iron, orange): +10 Growth
   - SO4 (Sulfate, yellow): +8 Growth
3. **GR bar reaches 100** - The bar flashes yellow, "SPACE!" text appears
4. **Press SPACE** - ARKE divides! A new colony cell is placed on an adjacent pore tile
5. **Colony placement logic:**
   - The game finds adjacent walkable pore tiles
   - If no direct neighbors are free, it searches 2 tiles away
   - It picks the spot furthest from solid walls (best position for biofilm growth)
   - The tile permanently becomes **biofilm** (green) on the map
6. **Growth resets to 0** - Start eating again for the next colony!

### Colony Effects:
- Colonies passively eat nearby substrates (2% chance per frame when a substrate is within 1.5 tiles)
- Colonies appear as green biofilm tiles on the minimap
- Colonies are permanent - they don't die or disappear
- **Each colony placed = +100 score points**

### Winning a Level:
- Each level has a **colony goal** (shown as "Colony: X/Y" in the HUD)
- When you place enough colonies, the level is complete!
- You'll see your stats and then a Science Discovery popup

---

## 1.5 Substrates (Food) - The Redox Ladder

Substrates are the colored floating particles you eat. They follow the real-world **redox ladder** - a ranking of microbial energy sources by thermodynamic yield.

| Substrate | Formula | Color | Energy | Growth | dG (kJ/mol) | Real Process |
|-----------|---------|-------|--------|--------|-------------|--------------|
| Oxygen | O2 | Blue | +20 | +15 | -818 | Aerobic respiration |
| Nitrate | NO3- | Green | +15 | +18 | -649 | Denitrification (prevents N2O!) |
| Manganese | Mn(IV) | Purple | +12 | +12 | -558 | Manganese reduction |
| Iron | Fe(III) | Orange | +10 | +10 | -334 | Iron reduction |
| Sulfate | SO42- | Yellow | +6 | +8 | -152 | Sulfate reduction |
| Methane | CH4 | Red | +5 | +25 | -31 | Methanotrophy (saves the planet!) |

### Why Does Energy vs Growth Differ? (The Real Science)

This is scientifically accurate! Here's why:
- **Energy** represents the thermodynamic free energy (dG) of the metabolic reaction. O2 yields -818 kJ/mol (most energy), while anaerobic methane oxidation yields only -31 kJ/mol (least energy). This determines how much "fuel" you get.
- **Growth** represents biomass yield - how much of the substrate is incorporated into new cell material. CH4 is a **carbon source** (C1 compound) that methanotrophic archaea directly assimilate into biomass through formaldehyde pathways. So CH4 gives the MOST biomass growth (+25) even though its energy yield is lowest.
- **O2** is an electron acceptor, not a carbon source. It gives lots of energy but doesn't directly provide carbon for building new cells, so growth is moderate (+15).
- **NO3** is balanced because denitrification both provides decent energy AND prevents toxic N2O accumulation, supporting healthy growth.

### Key Strategy:
- **O2 gives the most energy** (keeps you alive longest) but moderate growth
- **CH4 gives the most growth** (fills your division bar fastest) but low energy - eat it when your HP is safe
- **NO3 is the best all-rounder** - good energy AND good growth, plus it prevents N2O emissions
- In deeper levels, high-energy substrates (O2) disappear - you must survive on lower-energy options
- **Balance is key:** eat CH4 for growth when HP is above 50, switch to high-energy substrates when HP drops

### Scoring Bonuses:
- Eating any substrate: **+10 points**
- Eating CH4 (methane): **+25 bonus points** (you're saving the climate!)
- Eating NO3 (nitrate): **+15 bonus points** (you're preventing N2O!)

---

## 1.6 Rival Microbes

Rivals are **red enemy bacteria** marked with a flashing **"!"** above them. They are smart competitors:
- **Sense nearby substrates** (within 6 tiles) and actively move toward food
- **Track your position** - when you're close (within 8 tiles), they may move toward your area to compete for the same food zone
- **Follow water flow** - they ride currents to reach food, just like real planktonic bacteria
- **Get hungrier over time** - the longer they go without eating, the more aggressively they seek food (up to 75% seek rate)
- **Steal your food** - they eat any substrate they touch, and flash red when eating
- Cannot be killed or interacted with - you must **outcompete** them

### Strategies Against Rivals:
- Move fast - reach substrates before rivals sense them
- Use planktonic mode (SHIFT) to cover ground quickly and outpace rivals
- Don't chase a rival into a dead-end pore
- Rivals tend to follow flow - try exploring side channels they miss
- Focus on areas the rival isn't visiting
- Rivals don't target you specifically - they wander randomly

---

## 1.7 Hazards

### Toxic Zones (Purple/Magenta Tiles) - YES, They Are Real!

Toxic zones represent areas where **reactive chemical species accumulate** in the subsurface. This is real geochemistry:

- **Hydrogen Sulfide (H2S):** Produced by sulfate-reducing bacteria. H2S is toxic to most cells - it inhibits cytochrome c oxidase and damages cell membranes. In methane seep environments, H2S concentrations can reach lethal levels.
- **Reactive Oxygen Species (ROS):** At interfaces between oxic and anoxic zones, chemical reactions produce superoxide and hydroxyl radicals that damage DNA and proteins.
- **Heavy Metals:** Near hydrothermal vents, dissolved metals (Cu, Zn, Pb) in superheated fluid are toxic to microbes at high concentrations.

**In the game:**
- Deal **20 damage per second** while standing on them
- Appear in Chapters 3-5 (Methane Seeps, Permafrost Edge, Hydrothermal Realm)
- Shown as **purple/magenta tiles with pulsing borders and rising toxic particles**
- Marked as purple dots on the minimap
- The HUD shows a **toxic zone legend** (purple square + "TOXIC (H2S)") when the level has toxic zones
- **Avoid them!** Or cross very quickly if you must - 20 HP/sec is devastating

### Starvation
- HP drains at 1.5/sec even when standing still
- The screen edges pulse red when HP drops below 30
- "STARVING!" warning appears
- If HP reaches 0: game over (press ENTER to retry the level)

### Dead-End Pores
- Some pore channels have no exit - if you wander in, you waste time and health
- Use the minimap and Science Mode (Q) to plan routes
- Follow flow paths - they generally lead somewhere productive

---

## 1.8 Visual Indicators on Characters

### ARKE (Your Character)
- **Teal/cyan glow:** Pulsing teal highlight rectangle around you - always visible
- **White corner brackets:** Four white L-shaped markers at each corner
- **Floating white arrow:** Bouncing arrow above your head
- **Yellow glow:** When Growth bar is full and ready to divide
- **Blue glow:** When riding a flow current (SHIFT held)
- **Red flash:** When health is critical (<25 HP)
- **Dark inner background:** Behind the sprite for contrast against the dark pore water

### Rivals (Enemy Microbes)
- **Red glow:** Pulsing red highlight rectangle
- **Red corner brackets:** Four red L-shaped markers at each corner
- **"!" indicator:** Flashing red exclamation mark above their head
- **Red flash:** When they eat a substrate

### Colonies (Your Biofilm)
- Green biofilm tiles permanently placed on the map
- Visible on the minimap as small green dots

---

## 1.9 Game Flow

```
BOOT SCREEN
    |
TITLE SCREEN (Press ENTER)
    |
OPENING NARRATIVE (Cutscene: Elder explains the mission)
    |
  +---> MISSION BRIEFING (Elder explains this specific level)
  |         |
  |     LEVEL INTRO (Chapter title, environment info, controls reminder)
  |         |
  |     PLAYING (Navigate, eat, grow, divide, avoid hazards)
  |         |
  |     LEVEL COMPLETE (Stats shown)
  |         |
  |     SCIENCE DISCOVERY (Real science fact about the level)
  |         |
  +-----+  (Next level starts)
        |
    VICTORY (After completing all 10 levels)
```

### If You Die:
```
PLAYING --> GAME OVER (Press ENTER) --> Retry same level
```

### Pause Menu (ESC):
```
  Resume   - Continue playing
  Mute     - Toggle sound
  Quit     - Return to title screen
```

---

# PART 2: CHAPTER & LEVEL WALKTHROUGH

## Chapter 1: The Soil Frontier
*"Where Life Begins"*

### Environment
Shallow soil beneath a meadow. Warm brown grains, dark blue pore water. Oxygen seeps from the surface, nitrate flows through root zones, and methane bubbles up from decomposing organic matter. The most hospitable environment for a young archaea.

### Level 1: First Breath
| Parameter | Value |
|-----------|-------|
| Map Size | 30 x 20 tiles |
| Goal | Place 3 colonies |
| Porosity | 70% (lots of open space) |
| Substrates | O2 (blue), NO3 (green), CH4 (red) |
| Flow Speed | 0.6 (moderate) |
| Food Density | 4 (abundant) |
| Toxic Zones | None |
| Rivals | None |

**Strategy:** This is the tutorial level. No enemies, no toxins, wide open pores. Focus on learning the controls. Eat everything you see. O2 gives the most energy to keep you alive, CH4 fills your growth bar fastest. Place 3 colonies and move on.

**Tips:**
- Follow the flow direction (use Q to see arrows) to find where substrates accumulate
- Don't wander into dead-end pore channels
- When the GR bar is full and flashing, press SPACE immediately

### Level 2: Roots of Life
| Parameter | Value |
|-----------|-------|
| Map Size | 35 x 22 tiles |
| Goal | Place 5 colonies |
| Porosity | 65% |
| Substrates | O2, NO3, CH4 |
| Flow Speed | 0.7 |
| Food Density | 4 |
| Toxic Zones | None |
| Rivals | 1 |

**Strategy:** Your first rival appears! One red bacterium wanders the pores eating your food. Move quickly to secure substrates before the rival. The map is slightly tighter (65% porosity) with slightly faster flow. Use SHIFT to ride currents and outpace the rival.

**Tips:**
- The rival wanders randomly - don't chase it, just outeat it
- The map is bigger now; use the minimap to orient yourself
- Try planktonic mode (SHIFT) for the first time on flow tiles

---

## Chapter 2: The Deep Sediment
*"Darkness Below"*

### Environment
Ocean floor sediment hundreds of meters below the waves. Very dark grains and nearly black pore water. Light never reaches here. Oxygen is gone. The passages are narrower and food is scarce. Diffusion dominates transport.

### Level 3: Into the Depths
| Parameter | Value |
|-----------|-------|
| Map Size | 35 x 25 tiles |
| Goal | Place 4 colonies |
| Porosity | 50% (tight passages) |
| Substrates | NO3 (green), Fe(III) (orange), CH4 (red) |
| Flow Speed | 0.3 (slow) |
| Food Density | 3 (scarce) |
| Toxic Zones | None |
| Rivals | 2 |

**Strategy:** No more oxygen! You must survive on nitrate, iron, and methane - lower energy sources. The pores are narrow (50% porosity), flow is slow, and food is scarce. Two rivals compete for limited resources. Be efficient with every move.

**Tips:**
- NO3 is your best energy source here (+15 energy)
- CH4 has the most growth (+25) - prioritize it when your HP is decent
- With slow flow (0.3), substrates don't move far from spawn points
- The narrow passages mean less room to maneuver around rivals

### Level 4: The Hungry Dark
| Parameter | Value |
|-----------|-------|
| Map Size | 40 x 28 tiles |
| Goal | Place 6 colonies |
| Porosity | 45% (very tight) |
| Substrates | NO3, Mn(IV) (purple), Fe(III) (orange), CH4 (red) |
| Flow Speed | 0.25 (very slow) |
| Food Density | 2 (very scarce) |
| Toxic Zones | None |
| Rivals | 3 |

**Strategy:** The tightest, darkest level yet. 45% porosity means half the map is solid grain. Manganese (purple) is now available. Three rivals compete for meager food (density 2). This is a survival challenge - every molecule matters.

**Tips:**
- Manganese (Mn(IV), purple) gives +12 energy and +12 growth - decent balanced option
- Food density 2 means very few substrates spawn each cycle
- Use the minimap heavily - narrow passages can trap you
- Plan routes carefully; backtracking wastes precious health

---

## Chapter 3: The Methane Seeps
*"Rivers of Fire"*

### Environment
Active methane vents in fractured rock. Purple-dark grains with deep violet pore water. Methane erupts from below. Toxic zones appear for the first time - reactive chemical species that damage cell membranes.

### Level 5: The Methane Vents
| Parameter | Value |
|-----------|-------|
| Map Size | 35 x 22 tiles |
| Goal | Place 5 colonies |
| Porosity | 60% |
| Substrates | SO4 (yellow), CH4 (red) |
| Flow Speed | 0.5 |
| Food Density | 5 (abundant) |
| Toxic Zones | 15% of pore tiles |
| Rivals | 2 |

**Strategy:** Welcome to the methane seeps! Only sulfate and methane are available. Sulfate gives poor energy (+6) but CH4 gives massive growth (+25). Food is abundant (density 5) but **toxic zones** now cover 15% of pore tiles. Avoid the purple/magenta tiles!

**Tips:**
- Toxic zones deal 20 damage/sec - cross them quickly or find alternate routes
- CH4 is abundant here and gives the most growth
- SO4 (yellow) is your only real energy source at +6 - eat lots of it
- Check the minimap for purple dots marking toxic zones

### Level 6: Vent Guardians
| Parameter | Value |
|-----------|-------|
| Map Size | 40 x 25 tiles |
| Goal | Place 8 colonies |
| Porosity | 55% |
| Substrates | SO4, CH4, Fe(III) |
| Flow Speed | 0.6 |
| Food Density | 5 |
| Toxic Zones | 20% |
| Rivals | 3 |

**Strategy:** Bigger map, higher goal (8 colonies), more toxic zones (20%), and 3 rivals. Iron (Fe(III)) is now available too, giving better energy than sulfate. Build 8 colonies to create a biofilm wall against rising greenhouse gases.

**Tips:**
- Fe(III) gives +10 energy vs SO4's +6 - prioritize orange particles when HP is low
- 8 colonies means filling the GR bar 8 times - stay alive long enough!
- Toxic zones cover 1 in 5 pore tiles - plan routes around them on the minimap

---

## Chapter 4: The Permafrost Edge
*"The Melting World"*

### Environment
Warming temperatures thaw ancient ice. Light blue-gray grains, icy blue pore water. Trapped methane erupts in massive pulses. The flow is fast and chaotic.

### Level 7: Thawing Grounds
| Parameter | Value |
|-----------|-------|
| Map Size | 40 x 25 tiles |
| Goal | Place 6 colonies |
| Porosity | 55% |
| Substrates | O2 (blue), NO3 (green), CH4 (red) |
| Flow Speed | 0.8 (fast) |
| Food Density | 6 (very abundant) |
| Toxic Zones | 10% |
| Rivals | 3 |

**Strategy:** Oxygen returns! The thawing permafrost has opened connections to the surface. Food is very abundant (density 6) and flow is fast (0.8). Use SHIFT to ride the rapid currents. Some toxic zones exist (10%) but manageable.

**Tips:**
- Fast flow (0.8) makes planktonic mode (SHIFT) extremely effective
- O2 is back - eat blue particles to maintain high HP
- Substrates move quickly with the flow - intercept them along flow paths
- 3 rivals are competitive but abundant food compensates

### Level 8: The Great Thaw
| Parameter | Value |
|-----------|-------|
| Map Size | 45 x 28 tiles |
| Goal | Place 8 colonies |
| Porosity | 50% |
| Substrates | NO3, SO4, CH4 |
| Flow Speed | 1.0 (very fast) |
| Food Density | 6 |
| Toxic Zones | 15% |
| Rivals | 4 |

**Strategy:** The biggest map yet with the fastest flow. No oxygen - nitrate is your best energy source. Flow speed 1.0 means substrates fly through the pore network. 4 rivals compete. The thaw is accelerating - build 8 colonies to create a biofilm barrier.

**Tips:**
- Flow speed 1.0 is the fastest yet - substrates move quickly, use SHIFT to keep up
- 4 rivals mean fierce competition - efficiency is key
- NO3 (+15 energy, +18 growth) is your most important substrate here
- The larger map (45x28) means more area to cover - use the minimap and flow riding

---

## Chapter 5: The Hydrothermal Realm
*"Earth's Furnace"*

### Environment
Deep ocean vents blast superheated fluid through mineral chimneys. Very dark, almost black grains with deep red-tinged pore water. The most extreme environment. The full redox ladder operates here in centimeters of sediment.

### Level 9: The Abyss
| Parameter | Value |
|-----------|-------|
| Map Size | 45 x 25 tiles |
| Goal | Place 8 colonies |
| Porosity | 55% |
| Substrates | SO4, Fe(III), Mn(IV), CH4 |
| Flow Speed | 1.2 (extreme) |
| Food Density | 4 |
| Toxic Zones | 20% |
| Rivals | 4 |

**Strategy:** The deep ocean vents. Most of the redox ladder is available (sulfate, iron, manganese, methane). Flow is extreme (1.2) - substrates rush through at high speed. Toxic zones are dangerous (20%). 4 rivals compete in this hostile environment.

**Tips:**
- You have 4 substrate types - eat everything, but prioritize Mn(IV) and Fe(III) for energy
- Extreme flow means SHIFT is almost mandatory for efficient travel
- Toxic zones cover 20% of the map - they are everywhere, plan carefully
- This is the second-to-last level - stay focused

### Level 10: Earth's Last Stand
| Parameter | Value |
|-----------|-------|
| Map Size | 50 x 30 tiles |
| Goal | Place 12 colonies! |
| Porosity | 50% |
| Substrates | SO4, Fe(III), Mn(IV), CH4, NO3 |
| Flow Speed | 1.5 (maximum!) |
| Food Density | 5 |
| Toxic Zones | 25% |
| Rivals | 5 |

**Strategy:** THE FINAL LEVEL. The largest map (50x30), the most colonies needed (12!), the fastest flow (1.5!), the most toxic zones (25%), and 5 rivals! All substrates except O2 are available. This is the ultimate test of everything you've learned.

**Tips:**
- 12 colonies means filling the GR bar 12 separate times
- 5 rivals are relentless - you must outpace them all
- 25% toxic zones means 1 in 4 pore tiles is deadly
- Use every tool: SHIFT for speed, Q for flow mapping, minimap for navigation
- CH4 (+25 growth) fills the GR bar fastest - prioritize it when HP allows
- NO3 returns here - it's your best balanced option (+15 energy, +18 growth)
- **Victory awaits when all 12 colonies are placed!**

---

## 1.10 Scoring System

| Action | Points |
|--------|--------|
| Eat any substrate | +10 |
| Eat CH4 (methane) | +25 bonus |
| Eat NO3 (nitrate) | +15 bonus |
| Place a colony | +100 |
| Complete a level | +1,000 |

Your total score accumulates across all levels and is displayed at victory.

---

# PART 3: THE SCIENCE BEHIND THE GAME

## 3.1 The Redox Ladder - Energy for Life Without Sunlight

### In the Game
The colored substrates (O2, NO3, Mn(IV), Fe(III), SO4, CH4) are ranked by energy yield. Higher-energy substrates keep you alive longer but are rarer in deep environments.

### The Real Science
All life needs energy. On Earth's surface, photosynthesis converts sunlight into chemical energy. But underground, there is no light. Subsurface microorganisms harvest energy through **chemolithotrophy** - oxidizing and reducing chemicals.

The **redox ladder** (also called the thermodynamic ladder or electron tower) ranks available electron acceptors by the free energy released when coupled with an electron donor:

| Electron Acceptor | Half-reaction | dG (kJ/mol) | Environment |
|---|---|---|---|
| O2 (oxygen) | O2 + 4H+ + 4e- -> 2H2O | -818 | Near surface, oxygenated |
| NO3- (nitrate) | 2NO3- + 12H+ + 10e- -> N2 + 6H2O | -649 | Shallow subsurface |
| Mn(IV) | MnO2 + 4H+ + 2e- -> Mn2+ + 2H2O | -558 | Transition zones |
| Fe(III) | Fe(OH)3 + 3H+ + e- -> Fe2+ + 3H2O | -334 | Deeper sediment |
| SO42- (sulfate) | SO42- + 10H+ + 8e- -> H2S + 4H2O | -152 | Marine sediment |
| CO2/CH4 | CO2 + 8H+ + 8e- -> CH4 + 2H2O | -31 | Deepest, most reduced |

Microbes preferentially use the **highest-energy** electron acceptor available. As you go deeper underground, oxygen is consumed first, then nitrate, then manganese, then iron, then sulfate. This creates distinct **biogeochemical zones** in sediment - which is exactly what the game's 5 chapters represent!

**Reference Image:** Search for "redox ladder biogeochemistry" or "electron tower microbiology" for diagrams showing this thermodynamic ranking. The classic reference is:
- Bethke et al. (2011) "The thermodynamic ladder in geomicrobiology" - *American Journal of Science*
- Konhauser (2007) *Introduction to Geomicrobiology* - Chapter 5, Fig 5.1

---

## 3.2 Methanotrophy - Earth's Invisible Climate Shield

### In the Game (Chapters 3-5)
Eating CH4 (red particles) gives the least energy (+3) but the most growth (+25) and bonus score (+25). The Elder tells you: "Every molecule of CH4 you eat prevents global warming!"

### The Real Science
**Methanotrophs** are microorganisms that consume methane (CH4) as their carbon and energy source. Methane is a greenhouse gas approximately **80 times more potent** than CO2 over a 20-year period.

The aerobic reaction:
```
CH4 + 2O2 -> CO2 + 2H2O      (dG = -818 kJ/mol)
```

The anaerobic reaction (in deep sediment, without oxygen):
```
CH4 + SO42- -> HCO3- + HS- + H2O    (Anaerobic Oxidation of Methane, AOM)
```

Without methanotrophs, atmospheric methane concentrations would be **10-100 times higher** than current levels. These microorganisms filter approximately **~90% of all oceanic methane** before it reaches the water column and atmosphere.

**Key fact:** Subsurface microbes process approximately **600 Tg (teragrams) of CH4 per year** globally.

**Reference Images:**
- NOAA methane cycle diagram: Search "NOAA global methane budget diagram"
- Knittel & Boetius (2009) "Anaerobic Oxidation of Methane" - *Annual Review of Microbiology* - contains excellent diagrams of AOM consortia
- Reeburgh (2007) "Oceanic Methane Biogeochemistry" - *Chemical Reviews* - Figure 1 (global methane budget)

---

## 3.3 Denitrification - Preventing N2O Emissions

### In the Game (All Chapters)
Eating NO3- (green particles) gives good energy (+15) and growth (+18), plus a bonus "+15 pts" for preventing N2O. The science popup explains: "Without denitrifiers, nitrous oxide would accumulate."

### The Real Science
**Denitrification** is the microbial process that converts nitrate (NO3-) to harmless nitrogen gas (N2):

```
2NO3- + 10e- + 12H+ -> N2 + 6H2O
```

This is critically important because the intermediate product, **nitrous oxide (N2O)**, is a greenhouse gas approximately **300 times more potent** than CO2. Complete denitrification converts N2O to harmless N2. Incomplete denitrification releases N2O to the atmosphere.

Factors affecting complete vs. incomplete denitrification:
- **Oxygen levels:** High O2 inhibits denitrification, leading to N2O release
- **Carbon availability:** Low organic carbon = incomplete denitrification = more N2O
- **pH:** Acidic conditions inhibit the N2O reductase enzyme, releasing N2O
- **Pore connectivity:** In the game (and reality), microbes in well-connected pores receive more nutrients, supporting complete denitrification

**Reference Images:**
- IPCC nitrogen cycle diagrams: Search "nitrogen cycle soil N2O emissions diagram"
- Butterbach-Bahl et al. (2013) "Nitrous oxide emissions from soils" - *Nature Climate Change*
- Seitzinger et al. (2006) "Denitrification across landscapes and waterscapes" - *Ecological Applications*

---

## 3.4 Pore-Scale Reactive Transport (The Game World)

### In the Game
You navigate through a 2D maze of grain particles and pore spaces. Water flows through channels, carrying substrates. Dead-end pores starve you. Flow paths bring food.

### The Real Science
The game world is based on **pore-scale reactive transport modeling** from the CompLaB3D framework. In real soil and rock:

- **Porosity** is the fraction of volume that is pore space (void between grains). In the game, this directly controls how much walkable space exists (70% in Level 1 down to 45% in Level 4).
- **Grain size** affects pore throat diameter and connectivity. Larger grains = larger pores = easier transport.
- **Flow** through pore channels is governed by the **Navier-Stokes equations** at the pore scale, or approximated by **Darcy's law** at larger scales.
- **Advection** (flow-carried transport) dominates in well-connected channels.
- **Diffusion** (random molecular movement) is the only transport in dead-end pores.

The **Peclet number** (Pe = uL/D) determines which dominates:
- Pe >> 1: Advection dominates (fast flow, like in Chapters 4-5)
- Pe << 1: Diffusion dominates (slow/no flow, like in Chapter 2)

In the game, this manifests as:
- Fast flow levels (Chapters 4-5): Substrates zoom through channels; use SHIFT to ride
- Slow flow levels (Chapter 2): Substrates barely move; must hunt them carefully

**Reference Images:**
- CompLaB3D simulation outputs: Pore-scale velocity fields in 3D grain packs
- Blunt et al. (2013) "Pore-scale imaging and modelling" - *Advances in Water Resources*
- Steefel et al. (2015) "Reactive transport codes for subsurface environmental simulation" - *Computational Geosciences*

---

## 3.5 Monod Kinetics - Why Position Matters

### In the Game
Microbes near flow paths get more food. Dead-end pores mean starvation. The tutorial hints tell you to keep moving and stay near substrates.

### The Real Science
Microbial growth rate follows the **Monod equation**:

```
mu = mu_max * C / (Ks + C)
```

Where:
- **mu** = specific growth rate [1/s]
- **mu_max** = maximum growth rate (1.0 in the game's SCIENCE parameters)
- **C** = substrate concentration [mol/L]
- **Ks** = half-saturation constant (1.0e-5 in the game)

When substrate concentration is high (C >> Ks), growth is at maximum. When C is low (C << Ks), growth nearly stops. At C = Ks, growth is exactly half the maximum rate.

This is why **position within the pore network matters enormously** for microbial survival. Cells near flow inlets receive a constant supply of fresh substrate (high C), while cells in dead-end pores must rely on slow diffusion (low C).

In the game, this translates to:
- Stay near flow channels = abundant food = fast growth
- Wander into dead ends = starvation = death

**Reference Images:**
- Monod growth curve: Search "Monod equation microbial growth curve diagram"
- Rittmann & McCarty (2001) *Environmental Biotechnology* - Chapter 3 (classic reference)
- The CompLaB3D framework uses mu_max = 1.0 1/s, Ks = 1.0e-5 mol/L, Yield Y = 0.4

---

## 3.6 Biofilm Formation & Cellular Automata

### In the Game
When ARKE divides (SPACE), a colony is placed on an adjacent pore tile. The tile becomes permanent biofilm (green). Colonies passively consume nearby substrates. The goal is to build a network of colonies across the pore space.

### The Real Science
**Biofilms** are structured communities of microorganisms attached to surfaces and enclosed in a self-produced matrix of extracellular polymeric substances (EPS). In subsurface environments, biofilms:

- Grow on grain surfaces within pore spaces
- Can clog pore throats, redirecting flow
- Create microenvironments with different chemistry
- Persist for long periods once established

The game uses a **Cellular Automata (CA) model** for colony placement, based on the CompLaB3D approach:

1. When biomass density exceeds **B_max (100 kg/m3)**, excess biomass is pushed to neighboring pore voxels
2. A **distance field** guides growth toward open pore space
3. This produces realistic, branching biofilm patterns

In CompLaB3D specifically:
- Biofilm diffusion coefficient: D_biofilm = 2.0e-10 m2/s (5x slower than pore water!)
- Viscosity ratio in biofilm: 10x (flow is resisted)
- Decay rate: k_decay = 1.0e-9 1/s (very slow - biofilms are persistent)

**Reference Images:**
- Biofilm SEM images: Search "biofilm scanning electron microscopy pore scale"
- Picioreanu et al. (1998) "Mathematical modelling of biofilm structure" - pioneering CA biofilm model
- CompLaB3D documentation: Cellular Automata biomass spreading algorithm

---

## 3.7 Chapter-by-Chapter Science Connections

### Chapter 1: The Soil Frontier (Shallow Soil)
**Real-world analog:** Topsoil beneath grasslands and meadows, 0-30 cm depth

The soil is the most biologically active zone on Earth. In the top few centimeters:
- Oxygen diffuses from the atmosphere
- Root exudates provide organic carbon
- Nitrate from fertilizer or nitrogen fixation percolates through
- Methane from decomposing organic matter (methanogenesis) bubbles upward

**Key process:** Aerobic methane oxidation in the oxic zone consumes much of the upward-migrating CH4 before it reaches the atmosphere. This is your Level 1-2 experience.

**Reference:** Keiluweit et al. (2017) "Anaerobic microsites have an unaccounted role in soil carbon stabilization" - *Nature Communications*

### Chapter 2: The Deep Sediment (Ocean Floor)
**Real-world analog:** Marine sediment, 1-100 meters below seafloor (mbsf)

Below the ocean floor, conditions become progressively anoxic (oxygen-free). The classic biogeochemical zonation appears:
- 0-5 cm: Oxygen zone (aerobic)
- 5-50 cm: Nitrate/manganese zone
- 50-200 cm: Iron reduction zone
- 200+ cm: Sulfate reduction zone
- Deepest: Methanogenesis zone

In the game, Chapter 2 removes O2 and gives you NO3, Fe(III), and CH4 - representing the transition to anoxic conditions.

**Reference:** D'Hondt et al. (2004) "Distributions of microbial activities in deep subseafloor sediments" - *Science*

### Chapter 3: The Methane Seeps (Active Vents)
**Real-world analog:** Cold methane seeps and mud volcanoes on continental margins

At methane seeps, CH4-rich fluid migrates upward from deep reservoirs. The **sulfate-methane transition zone (SMTZ)** is where upward-diffusing methane meets downward-diffusing sulfate:

```
CH4 + SO42- -> HCO3- + HS- + H2O
```

This **Anaerobic Oxidation of Methane (AOM)** is performed by consortia of anaerobic methanotrophic archaea (ANME) and sulfate-reducing bacteria (SRB). They form characteristic aggregate structures visible under microscopy.

In the game, Chapter 3 gives you only SO4 and CH4 - representing the SMTZ where these two substrates are the primary energy sources. Toxic zones represent the highly reactive chemical species (H2S, reactive oxygen species) produced at these interfaces.

**Reference:**
- Boetius et al. (2000) "A marine microbial consortium apparently mediating anaerobic oxidation of methane" - *Nature*
- Orphan et al. (2001) "Methane-consuming archaea revealed by directly coupled isotopic and phylogenetic analysis" - *Science*

### Chapter 4: The Permafrost Edge (Thawing Arctic)
**Real-world analog:** Active layer of thawing permafrost in Arctic tundra

Arctic permafrost stores approximately **1,500 gigatons of carbon** - twice the amount currently in the atmosphere. As global temperatures rise, permafrost thaws and microbes decompose this ancient organic matter, releasing CO2 and CH4.

The **permafrost carbon feedback** is one of the most concerning positive feedback loops in climate science:
1. Warming -> permafrost thaws
2. Microbes decompose stored carbon -> CO2 + CH4 released
3. Greenhouse gases cause more warming
4. More permafrost thaws -> repeat

But **methanotrophic microbes in the thaw layer** act as a biological filter, consuming 20-60% of produced methane before it reaches the atmosphere. Your colonies in Chapter 4 represent this critical filter.

In the game, the fast flow (0.8-1.0) represents the rapid water movement through thawing soils, and the abundant CH4 represents the massive methane pulses from decomposing permafrost carbon.

**Reference:**
- Schuur et al. (2015) "Climate change and the permafrost carbon feedback" - *Nature*
- Turetsky et al. (2020) "Carbon release through abrupt permafrost thaw" - *Nature Geoscience*
- Dean et al. (2018) "Methane feedbacks to the global climate system in a warmer world" - *Reviews of Geophysics*

### Chapter 5: The Hydrothermal Realm (Deep-Sea Vents)
**Real-world analog:** Mid-ocean ridge hydrothermal vent systems, 2,000-4,000 m depth

Deep-sea hydrothermal vents release superheated fluid (300-400C) rich in reduced chemicals: H2S, Fe2+, Mn2+, CH4, and H2. These chemicals fuel entire ecosystems without any sunlight.

**Chemosynthesis** replaces photosynthesis as the base of the food web:
- Sulfur-oxidizing bacteria oxidize H2S
- Iron-oxidizing bacteria oxidize Fe2+
- Methanotrophs consume CH4
- These microbes support tube worms, clams, shrimp, and other vent fauna

The full redox ladder operates within centimeters of sediment near vents, creating extreme chemical gradients. In the game, Chapter 5 gives you the full suite of substrates (SO4, Fe(III), Mn(IV), CH4, NO3) and the fastest flow (1.2-1.5), representing the extreme conditions of hydrothermal vent environments.

**Reference:**
- Sievert & Vetriani (2012) "Chemoautotrophy at deep-sea vents" - *Oceanography*
- Kelley et al. (2005) "A serpentinite-hosted ecosystem: The Lost City Hydrothermal Field" - *Science*
- Martin et al. (2008) "Hydrothermal vents and the origin of life" - *Nature Reviews Microbiology*

---

## 3.8 Diffusion vs. Advection in Pore Spaces

### In the Game
Substrates float through pore channels carried by flow. In slow-flow levels (Chapter 2), they barely move. In fast-flow levels (Chapter 4-5), they zoom past. The SHIFT key switches you between sessile (attached, slow) and planktonic (free-floating, fast) modes.

### The Real Science
Transport of dissolved species in porous media occurs through two mechanisms:

**Advection:** Transport by bulk fluid flow
```
J_adv = v * C
```
Where v is fluid velocity and C is concentration. This is directional and fast.

**Diffusion:** Transport by random molecular motion (Brownian motion)
```
J_diff = -D * dC/dx     (Fick's First Law)
```
Where D is the diffusion coefficient. This is omnidirectional and slow.

The **Peclet number** determines which dominates:
```
Pe = v * L / D
```
- **Pe >> 1:** Advection dominates (fast flow channels in the game)
- **Pe << 1:** Diffusion dominates (dead-end pores, deep sediment)

CompLaB3D parameters:
- Pore diffusion coefficient: D_pore = 1.0e-9 m2/s
- Biofilm diffusion coefficient: D_biofilm = 2.0e-10 m2/s (5x slower due to EPS matrix)

This explains why in the game:
- Colonies near flow paths thrive (high Pe, advection delivers food)
- Colonies in dead-end pores starve (low Pe, only slow diffusion)
- Biofilm itself slows diffusion (viscosity ratio = 10x)

**Reference:**
- Bear (1972) *Dynamics of Fluids in Porous Media* - foundational textbook
- Steefel et al. (2005) "Reactive transport modeling" - *Reviews in Mineralogy and Geochemistry*

---

## 3.9 The CompLaB3D Framework

This game is based on the **CompLaB3D** (Computational Laboratory in 3D) research framework developed at the University of Georgia. CompLaB3D simulates:

1. **Pore-scale fluid flow** through realistic 3D grain packs using Navier-Stokes equations
2. **Reactive transport** of dissolved chemical species (advection + diffusion + reaction)
3. **Microbial growth** using Monod kinetics coupled with the redox ladder
4. **Biofilm formation** using Cellular Automata spreading algorithms
5. **Multi-species interactions** including competition for substrates

Key parameters used in the game (from CompLaB3D):

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Max growth rate | mu_max | 1.0 | 1/s |
| Half-saturation | Ks | 1.0e-5 | mol/L |
| Yield coefficient | Y | 0.4 | - |
| Decay rate | k_decay | 1.0e-9 | 1/s |
| Max biomass | B_max | 100 | kg/m3 |
| Pore diffusion | D_pore | 1.0e-9 | m2/s |
| Biofilm diffusion | D_biofilm | 2.0e-10 | m2/s |
| Viscosity ratio | - | 10 | - |

---

## 3.10 Image References & Further Reading

### Recommended Diagrams to Search For

1. **"Redox ladder biogeochemistry electron tower"** - Shows the thermodynamic ranking of electron acceptors
2. **"Pore scale reactive transport simulation"** - 3D visualizations of flow and reaction in grain packs
3. **"Biofilm pore scale microscopy"** - SEM images of biofilm growth in porous media
4. **"Sulfate methane transition zone SMTZ diagram"** - Cross-section of AOM at methane seeps
5. **"Permafrost carbon feedback loop diagram"** - Climate feedback cycle
6. **"Hydrothermal vent chimney cross section"** - Chemical gradients at deep-sea vents
7. **"Monod growth kinetics curve"** - Growth rate vs. substrate concentration
8. **"Darcy flow porous media diagram"** - Flow through granular media
9. **"Cellular automata biofilm model"** - CA biofilm spreading algorithm visualization
10. **"Global methane budget diagram NOAA"** - Sources and sinks of atmospheric methane

### Key Scientific Papers

1. Bethke, C.M. et al. (2011). "The thermodynamic ladder in geomicrobiology." *American Journal of Science*, 311(3), 183-210.
2. Boetius, A. et al. (2000). "A marine microbial consortium apparently mediating anaerobic oxidation of methane." *Nature*, 407, 623-626.
3. D'Hondt, S. et al. (2004). "Distributions of microbial activities in deep subseafloor sediments." *Science*, 306(5705), 2216-2221.
4. Knittel, K. & Boetius, A. (2009). "Anaerobic Oxidation of Methane: Progress with an Unknown Process." *Annual Review of Microbiology*, 63, 311-334.
5. Schuur, E.A.G. et al. (2015). "Climate change and the permafrost carbon feedback." *Nature*, 520, 171-179.
6. Reeburgh, W.S. (2007). "Oceanic methane biogeochemistry." *Chemical Reviews*, 107(2), 486-513.
7. Steefel, C.I. et al. (2015). "Reactive transport codes for subsurface environmental simulation." *Computational Geosciences*, 19(3), 445-478.
8. Picioreanu, C. et al. (1998). "Mathematical modelling of biofilm structure with a hybrid differential-discrete cellular automaton approach." *Biotechnology and Bioengineering*, 58, 101-116.
9. Rittmann, B.E. & McCarty, P.L. (2001). *Environmental Biotechnology: Principles and Applications.* McGraw-Hill.
10. Konhauser, K. (2007). *Introduction to Geomicrobiology.* Blackwell Publishing.

### Textbooks for Deeper Learning

- **Geomicrobiology:** Konhauser (2007) *Introduction to Geomicrobiology*
- **Reactive Transport:** Steefel et al. (2005) in *Reviews in Mineralogy and Geochemistry*
- **Biofilm Science:** Flemming et al. (2016) "Biofilms: an emergent form of bacterial life" - *Nature Reviews Microbiology*
- **Climate Science:** IPCC AR6 Working Group I Report (2021) - Chapter 5: Global Carbon and Other Biogeochemical Cycles

---

*ARKE: Guardians of Earth is an educational game demonstrating that the invisible world of subsurface microorganisms plays a critical role in regulating Earth's climate. Every colony you build represents a real biological defense mechanism against greenhouse gas emissions.*

*Developed based on CompLaB3D research at the University of Georgia.*
