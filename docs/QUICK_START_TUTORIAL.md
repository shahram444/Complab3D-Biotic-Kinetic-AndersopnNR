# ARKE: Guardians of Earth - Quick Start

## What is this game?

You play as **ARKE**, a tiny archaeon (microbe) living inside the pore spaces between soil grains deep underground. Your mission: eat substrates, grow colonies, and prevent greenhouse gases from escaping into the atmosphere. Everything in this game is based on real pore-scale reactive transport science from CompLaB3D research.

---

## Controls

| Key | Action |
|-----|--------|
| **Arrow Keys / WASD** | Move through pore spaces |
| **SPACE** | Divide and place a colony (when Growth bar is full) |
| **SHIFT** | Ride the flow current (planktonic mode - moves faster) |
| **Q** | Toggle Science Mode (shows flow data and tile info) |
| **M** | Mute/unmute sound |
| **ESC / P** | Pause |
| **ENTER** | Confirm / advance dialogue |

---

## HUD Bars Explained

| Bar | Color | What it means |
|-----|-------|---------------|
| **HP** | Green/Yellow/Red | Your health. Drops over time from starvation. Eat to restore! |
| **EN** | Blue | Energy stored from eating. Powers your movement |
| **GR** | Green | Growth progress. When full, press SPACE to divide! |

When the **GR bar** fills up and flashes yellow, you're ready to place a colony. Press **SPACE** near an open pore tile.

---

## How to Play

1. **Move** through the pore channels (blue/dark areas between brown grains)
2. **Eat substrates** by touching the colored floating orbs:
   - Red = CH4 (methane) - low energy, but saves the planet!
   - Blue = O2 (oxygen) - highest energy
   - Green = NO3 (nitrate) - good energy
   - Orange = Fe3+ (iron) - moderate energy
   - Yellow = SO4 (sulfate) - low energy
   - Purple = Mn4+ (manganese) - moderate energy
3. **Stay alive** - your HP drops over time. Keep eating!
4. **Grow** - eating fills your Growth bar
5. **Divide** - press SPACE when Growth is full to place a biofilm colony
6. **Complete the level** - place enough colonies to reach the goal

---

## Tips

- **Follow the flow** - substrates enter from the LEFT (inlet) and flow RIGHT (outlet). Stay near the left side for more food
- **Avoid purple toxic zones** - they drain your health fast (H2S damage)
- **Watch for rivals** - red microbes compete for the same food. Move fast!
- **Use SHIFT wisely** - riding the flow is fast but you can't steer well
- **Press Q** - Science Mode shows flow speeds, tile types, and level data

---

## Chapters

| Chapter | Environment | Challenge |
|---------|------------|-----------|
| 1. Soil Frontier | Open soil pores | Learn basics, oxygen available |
| 2. Deep Sediment | Tight maze tunnels | No oxygen, use nitrate/iron |
| 3. Methane Seeps | Vent channels | Toxic zones, lots of CH4 |
| 4. Permafrost Edge | Wide fast channels | Fast flow, urgent methane capture |
| 5. Hydrothermal Realm | Complex chambers | All hazards, final challenge |

---

## The Science

This game simulates real processes studied in CompLaB3D research at the University of Georgia:

- **Pore-scale transport**: Water flows through spaces between soil grains, carrying nutrients
- **Redox ladder**: Microbes use different electron acceptors (O2 > NO3 > Mn > Fe > SO4 > CH4) ranked by energy yield
- **Methanotrophy**: Archaea consume methane before it reaches the atmosphere as a greenhouse gas
- **Biofilm growth**: Microbial colonies expand using Cellular Automata rules
- **Monod kinetics**: Growth rate depends on substrate concentration

Every colony you build represents a real climate defense mechanism that prevents greenhouse gas emissions.
