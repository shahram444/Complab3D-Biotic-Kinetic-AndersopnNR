/**
 * PORELIFE: Microbe Survivor
 * Configuration & Constants
 * Based on CompLaB3D pore-scale reactive transport research
 */

const PL = window.PL || {};

// ─── DISPLAY ────────────────────────────────────────────────
PL.NATIVE_W = 320;
PL.NATIVE_H = 240;
PL.TILE = 16;
PL.COLS = 20;  // visible columns
PL.ROWS = 15;  // visible rows
PL.FPS = 60;

// ─── GAME STATES ────────────────────────────────────────────
PL.STATE = {
    BOOT: 'boot',
    TITLE: 'title',
    STORY: 'story',
    PLAYING: 'playing',
    PAUSED: 'paused',
    LEVEL_INTRO: 'level_intro',
    LEVEL_COMPLETE: 'level_complete',
    DIVISION: 'division',
    GAME_OVER: 'game_over',
    VICTORY: 'victory',
    SCIENCE_POPUP: 'science_popup'
};

// ─── TILE TYPES ─────────────────────────────────────────────
PL.TILES = {
    VOID: 0,
    SOLID: 1,      // Mineral grain (impassable)
    PORE: 2,       // Open pore space (walkable)
    BIOFILM: 3,    // Colony biofilm
    TOXIC: 4,      // Toxic/hazardous zone
    FLOW_FAST: 5,  // Fast flow channel
    INLET: 6,      // Substrate spawner
    OUTLET: 7,     // Level exit
    WALL_TOP: 8,   // Grain top face
    WALL_SIDE: 9   // Grain side face
};

// ─── COLORS / PALETTES ─────────────────────────────────────
PL.PAL = {
    // Universal
    TRANSPARENT: null,
    BLACK: '#000000',
    WHITE: '#e8e8e8',
    GRAY: '#888888',
    DARK_GRAY: '#444444',

    // Paler (microbe)
    PALER_BODY: '#5fcf5f',
    PALER_LIGHT: '#8bef6b',
    PALER_DARK: '#2f8f2f',
    PALER_EYE_W: '#ffffff',
    PALER_EYE_P: '#1a1a2e',
    PALER_GLOW: '#4fff4f',
    PALER_SICK: '#8b8b3b',
    PALER_READY: '#ffff5f',

    // Substrate
    DOC_COLOR: '#ffd700',
    DOC_GLOW: '#ffec80',
    NUTRIENT_COLOR: '#5fc4eb',
    NUTRIENT_GLOW: '#a0e0ff',

    // UI
    UI_BG: '#0a0a1a',
    UI_BORDER: '#3a3a6a',
    UI_TEXT: '#c8c8e8',
    UI_HIGHLIGHT: '#ffd700',
    UI_HEALTH: '#ef4444',
    UI_GROWTH: '#5fcf5f',
    UI_ENERGY: '#5f9fef',
    UI_DANGER: '#ef2020',

    // Title
    TITLE_GLOW: '#4fff4f',
    TITLE_SHADOW: '#0a2f0a'
};

// World-specific palettes
PL.WORLD_PAL = [
    // World 1: Sandy Maze
    {
        name: 'The Sandy Maze',
        subtitle: 'Where Life Begins',
        grain: '#8b6914',
        grainLight: '#c4a35a',
        grainDark: '#5a3921',
        grainAccent: '#dcc07a',
        pore: '#0a1428',
        poreLight: '#142040',
        water: '#1a3c6e',
        waterLight: '#3c6eaa',
        bg: '#060e1e',
        toxic: '#8b3a8b',
        toxicGlow: '#cf5fcf'
    },
    // World 2: Clay Labyrinth
    {
        name: 'The Clay Labyrinth',
        subtitle: 'The Narrowing Dark',
        grain: '#5a4a3a',
        grainLight: '#7a6a5a',
        grainDark: '#3a2a1a',
        grainAccent: '#6a5a4a',
        pore: '#080810',
        poreLight: '#101020',
        water: '#0f1e3c',
        waterLight: '#1a2e4c',
        bg: '#040408',
        toxic: '#6e3a3a',
        toxicGlow: '#af5a5a'
    },
    // World 3: Toxic Veins
    {
        name: 'The Toxic Veins',
        subtitle: 'Survival of the Fittest',
        grain: '#3a3a4a',
        grainLight: '#5a5a6a',
        grainDark: '#2a2a3a',
        grainAccent: '#4a4a5a',
        pore: '#0a0814',
        poreLight: '#140e20',
        water: '#1a1a3c',
        waterLight: '#2e1a4c',
        bg: '#06040e',
        toxic: '#7f1a7f',
        toxicGlow: '#bf3fbf'
    },
    // World 4: Flow Highways
    {
        name: 'The Flow Highways',
        subtitle: 'Racing the Current',
        grain: '#2a3a5a',
        grainLight: '#3a5a8a',
        grainDark: '#1a2a4a',
        grainAccent: '#4a6a9a',
        pore: '#060a1e',
        poreLight: '#0e1430',
        water: '#1a4c8e',
        waterLight: '#3c7abe',
        bg: '#040610',
        toxic: '#8b5a1a',
        toxicGlow: '#cf8a3f'
    }
];

// ─── SCIENCE PARAMETERS (from CompLaB3D) ───────────────────
PL.SCIENCE = {
    mu_max: 1.0,          // Max growth rate [1/s]
    Ks: 1.0e-5,           // Half-saturation [mol/L]
    Y: 0.4,               // Yield coefficient
    k_decay: 1.0e-9,      // Decay rate [1/s]
    B_max: 100.0,          // Max biomass density [kg/m³]
    D_pore: 1.0e-9,       // Diffusion in pore [m²/s]
    D_biofilm: 2.0e-10,   // Diffusion in biofilm [m²/s]
    C_inlet: 0.1,         // Inlet concentration [mol/L]
    viscosity_ratio: 10.0  // Flow resistance in biofilm
};

// ─── GAME BALANCE ───────────────────────────────────────────
PL.BALANCE = {
    // Player
    MOVE_SPEED: 2.0,           // Tiles per second
    MAX_HEALTH: 100,
    MAX_GROWTH: 100,
    HEALTH_DECAY_RATE: 1.2,    // Health lost per second (starvation)
    GROWTH_DECAY_RATE: 0.3,    // Growth lost per second
    TOXIC_DAMAGE: 15,          // Damage per second in toxic zone

    // Substrate
    DOC_HEALTH: 8,
    DOC_GROWTH: 15,
    NUTRIENT_HEALTH: 15,
    NUTRIENT_GROWTH: 5,
    SUBSTRATE_SPEED: 0.8,      // Tiles per second (base flow)
    SUBSTRATE_SPAWN_RATE: 1.5, // Seconds between spawns

    // Colony
    DIVISION_GROWTH_COST: 100, // Growth needed to divide
    COLONY_GOAL_BASE: 5,       // Colonies needed for level 1
    COLONY_PASSIVE_RANGE: 2,   // Tiles range for passive consumption

    // Scoring
    SCORE_SUBSTRATE: 10,
    SCORE_COLONY: 50,
    SCORE_LEVEL: 500,
    SCORE_SCIENCE: 100,
    SCORE_TIME_BONUS: 200,

    // Flow speeds per world
    FLOW_SPEEDS: [0.6, 0.3, 0.5, 1.8],

    // Substrate density per world (spawns per interval)
    SUBSTRATE_DENSITY: [3, 1, 2, 4],

    // Toxic coverage per world (0-1)
    TOXIC_COVERAGE: [0.0, 0.0, 0.25, 0.05]
};

// ─── LEVEL DEFINITIONS ─────────────────────────────────────
PL.LEVELS = [
    // World 1: Sandy Maze
    { world: 0, mapW: 30, mapH: 20, colonyGoal: 3,  porosity: 0.65, grainSize: [2,3], title: 'First Light', scienceIdx: 0 },
    { world: 0, mapW: 35, mapH: 22, colonyGoal: 5,  porosity: 0.60, grainSize: [2,4], title: 'The Flow Begins', scienceIdx: 1 },
    { world: 0, mapW: 40, mapH: 25, colonyGoal: 7,  porosity: 0.55, grainSize: [3,5], title: 'Spreading Roots', scienceIdx: 2 },
    // World 2: Clay Labyrinth
    { world: 1, mapW: 35, mapH: 25, colonyGoal: 4,  porosity: 0.40, grainSize: [1,2], title: 'Into the Dark', scienceIdx: 3 },
    { world: 1, mapW: 40, mapH: 28, colonyGoal: 6,  porosity: 0.35, grainSize: [1,3], title: 'Scarce Provisions', scienceIdx: 4 },
    { world: 1, mapW: 45, mapH: 30, colonyGoal: 8,  porosity: 0.30, grainSize: [1,2], title: 'The Long Hunger', scienceIdx: 5 },
    // World 3: Toxic Veins
    { world: 2, mapW: 35, mapH: 22, colonyGoal: 5,  porosity: 0.50, grainSize: [2,4], title: 'Poisoned Ground', scienceIdx: 6 },
    { world: 2, mapW: 40, mapH: 25, colonyGoal: 7,  porosity: 0.45, grainSize: [2,3], title: 'Toxic Maze', scienceIdx: 7 },
    { world: 2, mapW: 45, mapH: 28, colonyGoal: 10, porosity: 0.45, grainSize: [2,4], title: 'No Safe Haven', scienceIdx: 8 },
    // World 4: Flow Highways
    { world: 3, mapW: 40, mapH: 22, colonyGoal: 6,  porosity: 0.55, grainSize: [3,5], title: 'The Rush', scienceIdx: 9 },
    { world: 3, mapW: 50, mapH: 25, colonyGoal: 8,  porosity: 0.50, grainSize: [3,6], title: 'Against the Current', scienceIdx: 10 },
    { world: 3, mapW: 55, mapH: 30, colonyGoal: 12, porosity: 0.50, grainSize: [2,5], title: 'The Final Colony', scienceIdx: 11 }
];

// ─── STORY / SCIENCE TEXTS ──────────────────────────────────
PL.INTRO_STORY = [
    "Deep beneath the surface...",
    "where sunlight never reaches...",
    "in the microscopic maze between",
    "mineral grains and sediment...",
    "",
    "...life persists.",
    "",
    "Tiny water-filled channels connect",
    "a hidden world of pores and tunnels.",
    "",
    "Nutrients flow through these passages,",
    "carried by invisible currents.",
    "",
    "You are PALER.",
    "A single microbe.",
    "Born in the dark.",
    "",
    "To survive, you must eat.",
    "To grow, you must explore.",
    "To thrive... you must COLONIZE.",
    "",
    "Will you spread life across",
    "the hidden world?",
    "",
    "      [PRESS ENTER]"
];

PL.SCIENCE_FACTS = [
    { title: "Advection", text: "In porous media, water flow carries dissolved nutrients through connected pore channels. This process, called advection, is the main delivery system for microbial food.\n\nIn CompLaB3D, we solve:\n  dC/dt + u·nablaC = D·nabla²C\n\nFlow velocity 'u' drives nutrient transport." },
    { title: "Monod Kinetics", text: "Microbes don't eat at a constant rate. Growth follows the Monod equation:\n\n  mu = mu_max × C/(Ks + C)\n\nWhen food (C) is abundant, growth approaches maximum (mu_max). When scarce, growth slows dramatically.\n\nKs = " + (1e-5) + " mol/L in our model." },
    { title: "Colony Spreading", text: "When a microbe grows beyond its capacity (B > B_max), excess biomass is pushed to neighboring pore spaces. This is our Cellular Automata (CA) model of biofilm expansion.\n\nIn CompLaB3D, we use distance fields to guide growth toward open pore space." },
    { title: "Diffusion Limitation", text: "In tight clay-like pores, water barely flows. Nutrients must reach microbes by diffusion alone — random molecular movement.\n\nDiffusion is MUCH slower than advection:\n  D_pore = 1×10⁻⁹ m²/s\n  vs. flow speeds of ~10⁻⁴ m/s" },
    { title: "Substrate Limitation", text: "Even with perfect flow, microbes can exhaust local nutrients faster than they're replenished. This creates 'substrate-limited' zones.\n\nAt C << Ks, growth rate drops to near zero. Many microbes in nature live in this hungry state." },
    { title: "Yield Coefficient", text: "Not all food becomes biomass. The yield coefficient Y = 0.4 means only 40% of consumed substrate converts to cell mass.\n\nThe rest is used for energy (respiration) and produces CO2:\n  dB/dt = mu × B\n  dC/dt = -mu × B / Y" },
    { title: "Geochemical Gradients", text: "Underground environments have zones of different chemistry. pH, oxygen, and toxic metals create boundaries.\n\nMicrobes can only thrive in specific geochemical windows. Toxic zones in the game represent real chemical barriers to life." },
    { title: "Redox Boundaries", text: "Where oxidizing and reducing fluids meet, chemical energy is released. These redox fronts are hotspots for microbial activity.\n\nBut they're also dangerous: reactive species like free radicals can damage cells. A double-edged sword." },
    { title: "Biofilm Resistance", text: "Biofilm colonies are more resistant than individual cells. The extracellular matrix protects against toxins and flow shear.\n\nIn CompLaB3D, biofilm regions have:\n  - 5× lower diffusion\n  - 10× higher viscosity\n  - Protected core cells" },
    { title: "Preferential Flow", text: "In heterogeneous porous media, water doesn't flow uniformly. It follows the path of least resistance, creating 'preferential flow paths'.\n\nSome pores get abundant flow (and nutrients), while others are stagnant. This creates spatial inequality for microbes." },
    { title: "Peclet Number", text: "The Peclet number (Pe) balances advection vs. diffusion:\n  Pe = u×L / D\n\nPe >> 1: flow dominates (nutrients rush past)\nPe << 1: diffusion dominates (nutrients spread slowly)\nPe ~ 1: balanced transport\n\nOur model uses Pe = 1.0" },
    { title: "Biogeochemical Coupling", text: "In real subsurface systems, biology, chemistry, and flow are deeply coupled:\n\n- Microbes change chemistry (consume O2, produce CO2)\n- Chemistry changes minerals (dissolution, precipitation)\n- Minerals change flow (porosity evolution)\n\nThis is the full cycle CompLaB3D simulates.\n\nCongratulations — you've experienced pore-scale reactive transport!" }
];

PL.WORLD_INTROS = [
    { title: "WORLD 1", subtitle: "The Sandy Maze", text: "Loose sand grains form wide channels.\nWater flows freely, carrying nutrients.\nA good place to learn... and grow.\n\nControls:\n  Arrows/WASD  Move\n  SPACE        Divide (when ready)\n  Q            Science Mode\n  M            Mute" },
    { title: "WORLD 2", subtitle: "The Clay Labyrinth", text: "Dense clay minerals pack tightly together.\nChannels narrow. Flow slows to a crawl.\nNutrients are rare. Every bite counts.\n\nDiffusion dominates here.\nPlan your path carefully." },
    { title: "WORLD 3", subtitle: "The Toxic Veins", text: "Strange chemical gradients cut through\nthe pore space. Some zones glow with\ndangerous reactive compounds.\n\nAvoid the purple zones.\nThey represent hostile geochemistry." },
    { title: "WORLD 4", subtitle: "The Flow Highways", text: "Wide channels with powerful currents.\nNutrients rush past at high speed.\nCatch them before they're gone.\n\nPreferential flow paths dominate.\nPosition is everything." }
];

// ─── KEY BINDINGS ───────────────────────────────────────────
PL.KEYS = {
    UP: ['ArrowUp', 'KeyW'],
    DOWN: ['ArrowDown', 'KeyS'],
    LEFT: ['ArrowLeft', 'KeyA'],
    RIGHT: ['ArrowRight', 'KeyD'],
    ACTION: ['Space'],
    CONFIRM: ['Enter'],
    PAUSE: ['KeyP', 'Escape'],
    SCIENCE: ['KeyQ'],
    MUTE: ['KeyM']
};

window.PL = PL;
