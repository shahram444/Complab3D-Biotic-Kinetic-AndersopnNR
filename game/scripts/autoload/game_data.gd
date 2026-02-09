extends Node
## Global game data, constants, science parameters, level definitions.
## Based on CompLaB3D pore-scale biogeochemical reactive transport research.

# ── DISPLAY ──────────────────────────────────────────────────────────────────
const TILE := 32
const VIEW_W := 960
const VIEW_H := 540
const COLS := 30
const ROWS := 17

# ── GAME STATES ──────────────────────────────────────────────────────────────
enum State { BOOT, TITLE, NARRATIVE, MISSION_BRIEF, LEVEL_INTRO, PLAYING, PAUSED,
	LEVEL_COMPLETE, SCIENCE_POPUP, GAME_OVER, VICTORY }

# ── TILE TYPES ───────────────────────────────────────────────────────────────
enum Tile { VOID, SOLID, PORE, BIOFILM, TOXIC, FLOW_FAST, INLET, OUTLET }

# ── SUBSTRATE TYPES (Redox Ladder - descending energy yield) ─────────────────
# Based on real thermodynamic free energy of microbial metabolisms
enum Sub { O2, NO3, MN4, FE3, SO4, CH4 }

const SUBSTRATES := {
	Sub.O2:  { "name": "Oxygen",   "formula": "O2",     "color": "#4fa4ff", "glow": "#8fc8ff",
	           "energy": 20, "growth": 15, "dG": -818.0, "desc": "Aerobic respiration" },
	Sub.NO3: { "name": "Nitrate",  "formula": "NO3-",   "color": "#4fdf6f", "glow": "#8fff9f",
	           "energy": 15, "growth": 18, "dG": -649.0, "desc": "Denitrification - prevents N2O" },
	Sub.MN4: { "name": "Manganese","formula": "Mn(IV)", "color": "#cf6fff", "glow": "#df9fff",
	           "energy": 12, "growth": 12, "dG": -558.0, "desc": "Manganese reduction" },
	Sub.FE3: { "name": "Iron",     "formula": "Fe(III)","color": "#ef8f3f", "glow": "#ffbf7f",
	           "energy": 10, "growth": 10, "dG": -334.0, "desc": "Iron reduction" },
	Sub.SO4: { "name": "Sulfate",  "formula": "SO42-",  "color": "#dfdf3f", "glow": "#ffffaf",
	           "energy": 6,  "growth": 8,  "dG": -152.0, "desc": "Sulfate reduction" },
	Sub.CH4: { "name": "Methane",  "formula": "CH4",    "color": "#ff4f4f", "glow": "#ff9f7f",
	           "energy": 3,  "growth": 25, "dG": -31.0,  "desc": "Methanotrophy - prevents warming!" },
}

# ── SCIENCE PARAMETERS (from CompLaB3D) ─────────────────────────────────────
const SCIENCE := {
	"mu_max": 1.0,         # Max specific growth rate [1/s]
	"Ks": 1.0e-5,          # Half-saturation constant [mol/L]
	"Y": 0.4,              # Yield coefficient [-]
	"k_decay": 1.0e-9,     # Decay rate [1/s]
	"B_max": 100.0,        # Max biomass density [kg/m3]
	"D_pore": 1.0e-9,      # Diffusion coeff in pore [m2/s]
	"D_biofilm": 2.0e-10,  # Diffusion in biofilm [m2/s]
	"visc_ratio": 10.0,    # Viscosity ratio in biofilm
}

# ── GAME BALANCE ─────────────────────────────────────────────────────────────
const BAL := {
	"move_speed": 2.5,        # Tiles per second (normal movement)
	"flow_ride_mult": 2.0,    # Speed multiplier when riding flow
	"max_health": 100.0,
	"max_energy": 100.0,
	"max_growth": 100.0,
	"health_decay": 1.5,      # HP lost per second (starvation)
	"energy_decay": 0.8,      # Energy lost per second
	"toxic_damage": 20.0,     # Damage per second in toxic zone
	"division_cost": 100.0,   # Growth needed to divide
	"substrate_speed": 0.6,   # Base flow speed for substrates
	"substrate_spawn": 1.2,   # Seconds between spawns
	"score_eat": 10,
	"score_colony": 100,
	"score_level": 1000,
	"score_methane": 25,      # Bonus for eating CH4
	"score_no3": 15,          # Bonus for eating NO3 (prevents N2O)
}

# ── LEVEL DEFINITIONS ────────────────────────────────────────────────────────
const LEVELS := [
	# Level 1: The Soil Frontier (tutorial - no rivals)
	{ "env": 0, "w": 30, "h": 20, "goal": 3, "porosity": 0.70, "grain": [2,3],
	  "subs": [Sub.O2, Sub.NO3, Sub.CH4], "flow": 0.6, "density": 4,
	  "toxic": 0.0, "rivals": 0, "title": "First Breath" },
	{ "env": 0, "w": 35, "h": 22, "goal": 5, "porosity": 0.65, "grain": [2,4],
	  "subs": [Sub.O2, Sub.NO3, Sub.CH4], "flow": 0.7, "density": 4,
	  "toxic": 0.0, "rivals": 1, "title": "Roots of Life" },

	# Level 2: Deep Sediment
	{ "env": 1, "w": 35, "h": 25, "goal": 4, "porosity": 0.50, "grain": [1,2],
	  "subs": [Sub.NO3, Sub.FE3, Sub.CH4], "flow": 0.3, "density": 3,
	  "toxic": 0.0, "rivals": 2, "title": "Into the Depths" },
	{ "env": 1, "w": 40, "h": 28, "goal": 6, "porosity": 0.45, "grain": [1,3],
	  "subs": [Sub.NO3, Sub.MN4, Sub.FE3, Sub.CH4], "flow": 0.25, "density": 2,
	  "toxic": 0.0, "rivals": 3, "title": "The Hungry Dark" },

	# Level 3: Methane Seeps
	{ "env": 2, "w": 35, "h": 22, "goal": 5, "porosity": 0.60, "grain": [2,4],
	  "subs": [Sub.SO4, Sub.CH4], "flow": 0.5, "density": 5,
	  "toxic": 0.15, "rivals": 2, "title": "The Methane Vents" },
	{ "env": 2, "w": 40, "h": 25, "goal": 8, "porosity": 0.55, "grain": [2,3],
	  "subs": [Sub.SO4, Sub.CH4, Sub.FE3], "flow": 0.6, "density": 5,
	  "toxic": 0.20, "rivals": 3, "title": "Vent Guardians" },

	# Level 4: Permafrost Edge
	{ "env": 3, "w": 40, "h": 25, "goal": 6, "porosity": 0.55, "grain": [2,5],
	  "subs": [Sub.O2, Sub.NO3, Sub.CH4], "flow": 0.8, "density": 6,
	  "toxic": 0.10, "rivals": 3, "title": "Thawing Grounds" },
	{ "env": 3, "w": 45, "h": 28, "goal": 8, "porosity": 0.50, "grain": [3,5],
	  "subs": [Sub.NO3, Sub.SO4, Sub.CH4], "flow": 1.0, "density": 6,
	  "toxic": 0.15, "rivals": 4, "title": "The Great Thaw" },

	# Level 5: Hydrothermal Realm (final)
	{ "env": 4, "w": 45, "h": 25, "goal": 8, "porosity": 0.55, "grain": [2,4],
	  "subs": [Sub.SO4, Sub.FE3, Sub.MN4, Sub.CH4], "flow": 1.2, "density": 4,
	  "toxic": 0.20, "rivals": 4, "title": "The Abyss" },
	{ "env": 4, "w": 50, "h": 30, "goal": 12, "porosity": 0.50, "grain": [2,5],
	  "subs": [Sub.SO4, Sub.FE3, Sub.MN4, Sub.CH4, Sub.NO3], "flow": 1.5, "density": 5,
	  "toxic": 0.25, "rivals": 5, "title": "Earth's Last Stand" },
]

# ── ENVIRONMENT PALETTES ─────────────────────────────────────────────────────
const ENV_PAL := [
	# 0: Soil Frontier
	{ "name": "The Soil Frontier", "sub": "Where Life Begins",
	  "grain": "#7a5a2a", "grain_l": "#a48a5a", "grain_d": "#4a3a1a", "grain_a": "#c4a060",
	  "pore": "#0c1420", "pore_l": "#142030", "water": "#1a3a60", "water_l": "#3060a0",
	  "bg": "#060c18", "toxic": "#8a3a8a", "toxic_g": "#c060c0" },
	# 1: Deep Sediment
	{ "name": "The Deep Sediment", "sub": "Darkness Below",
	  "grain": "#4a3a2a", "grain_l": "#6a5a4a", "grain_d": "#2a1a0a", "grain_a": "#5a4a3a",
	  "pore": "#060608", "pore_l": "#0c0c14", "water": "#0a1428", "water_l": "#142038",
	  "bg": "#030306", "toxic": "#6a2a2a", "toxic_g": "#a04040" },
	# 2: Methane Seeps
	{ "name": "The Methane Seeps", "sub": "Rivers of Fire",
	  "grain": "#3a3040", "grain_l": "#5a5060", "grain_d": "#2a2030", "grain_a": "#4a4050",
	  "pore": "#0a0610", "pore_l": "#140c1c", "water": "#1a1438", "water_l": "#2a1a48",
	  "bg": "#06040a", "toxic": "#7a1a6a", "toxic_g": "#b040a0" },
	# 3: Permafrost Edge
	{ "name": "The Permafrost Edge", "sub": "The Melting World",
	  "grain": "#5a6a7a", "grain_l": "#8a9aaa", "grain_d": "#3a4a5a", "grain_a": "#aabaca",
	  "pore": "#080c14", "pore_l": "#0c1420", "water": "#1a3050", "water_l": "#3a5a8a",
	  "bg": "#040810", "toxic": "#4a7a3a", "toxic_g": "#70b050" },
	# 4: Hydrothermal Realm
	{ "name": "The Hydrothermal Realm", "sub": "Earth's Furnace",
	  "grain": "#2a2a3a", "grain_l": "#4a4a5a", "grain_d": "#1a1a2a", "grain_a": "#3a3a4a",
	  "pore": "#0a0608", "pore_l": "#14080c", "water": "#281418", "water_l": "#3a1a20",
	  "bg": "#060304", "toxic": "#8a4a1a", "toxic_g": "#c07030" },
]

# ── CUTSCENE DIALOGUE (visual novel style) ──────────────────────────────────
# speaker: "ELDER" = Archaeon Prime (mentor), "METHI" = player, "" = narration
const CUTSCENE := [
	{"speaker": "", "text": "Deep within the pore space...\nbetween grains of ancient rock..."},
	{"speaker": "ELDER", "text": "Young one... wake up."},
	{"speaker": "METHI", "text": "W-where am I? What is this place?"},
	{"speaker": "ELDER", "text": "You are in the subsurface. Between\ngrains of soil, far from light.\nThis is our world."},
	{"speaker": "ELDER", "text": "I am ARCHAEON PRIME.\nElder of the methanotrophic archaea.\nI have guarded these pores for eons."},
	{"speaker": "METHI", "text": "Why is everything so dark?\nWhat's happening?"},
	{"speaker": "ELDER", "text": "Methane. CH4. A greenhouse gas\n80 times more powerful than CO2.\nIt rises from the deep below."},
	{"speaker": "ELDER", "text": "And N2O... nitrous oxide.\n300 times more dangerous than CO2.\nThey seep from thawing soil."},
	{"speaker": "ELDER", "text": "For billions of years, we microbes\nhave consumed these gases.\nWe are Earth's invisible shield."},
	{"speaker": "METHI", "text": "What must I do?"},
	{"speaker": "ELDER", "text": "Eat substrates. Grow your biomass.\nWhen your growth bar fills -\npress SPACE to DIVIDE!"},
	{"speaker": "ELDER", "text": "Place colonies across the pore network.\nBuild a biofilm to filter the gas.\nThat is the Cellular Automata way."},
	{"speaker": "ELDER", "text": "But beware... rival microbes roam\nthese pores. They will steal\nyour nutrients."},
	{"speaker": "ELDER", "text": "And the pore geometry itself is\nyour enemy. Dead-end pores\nmean starvation and death."},
	{"speaker": "METHI", "text": "I won't let Earth down."},
	{"speaker": "ELDER", "text": "Remember the redox ladder:\nO2 gives most energy, CH4 the least.\nBut eating CH4 saves the planet!"},
	{"speaker": "ELDER", "text": "Now go, young one.\nThe Soil Frontier awaits.\nEarth's fate is in your pseudopods."},
]

# ── WORLD INTRO TEXTS ────────────────────────────────────────────────────────
const WORLD_INTROS := [
	{ "title": "CHAPTER 1", "sub": "The Soil Frontier",
	  "text": "Shallow soil beneath a meadow.\nOxygen seeps from above. Nitrate flows\nthrough the root zone. Methane bubbles up\nfrom decomposing organic matter.\n\nA good place to learn the ways\nof microbial life.\n\nArrows/WASD: Move\nSHIFT: Ride flow (planktonic)\nSPACE: Divide\nQ: Science Mode" },
	{ "title": "CHAPTER 2", "sub": "The Deep Sediment",
	  "text": "Ocean floor sediment. Hundreds of meters\nbelow the waves. Light never reaches here.\nOxygen is gone. Only iron and manganese\nremain as electron acceptors.\n\nFood is scarce. Every molecule counts.\nDiffusion dominates transport." },
	{ "title": "CHAPTER 3", "sub": "The Methane Seeps",
	  "text": "Active methane vents push CH4 through\nfractured rock. Sulfate mingles with\nthe rising gas. Toxic zones where\nreactive species damage cells.\n\nThis is where methanotrophs shine.\nConsume the methane. Save the climate." },
	{ "title": "CHAPTER 4", "sub": "The Permafrost Edge",
	  "text": "Warming temperatures thaw ancient ice.\nTrapped methane erupts in massive pulses.\nThe flow is fast and chaotic.\n\nThis is urgent. Every molecule of CH4\nthat escapes warms the planet further.\nCatch it before it rises." },
	{ "title": "CHAPTER 5", "sub": "The Hydrothermal Realm",
	  "text": "Deep ocean vents blast superheated fluid\nthrough mineral chimneys. Extreme chemistry.\nSulfate, iron, manganese - the full\nredox ladder in one place.\n\nOnly the strongest colonies survive here.\nThis is your final stand." },
]

# ── SCIENCE FACTS ────────────────────────────────────────────────────────────
const SCIENCE_FACTS := [
	{ "title": "The Redox Ladder",
	  "text": "Microbes harvest energy by transferring electrons\nfrom donors to acceptors. The 'redox ladder' ranks\nthese reactions by energy yield:\n\n  O2       -> 818 kJ/mol  (most energy)\n  NO3-     -> 649 kJ/mol\n  Mn(IV)   -> 558 kJ/mol\n  Fe(III)  -> 334 kJ/mol\n  SO42-    -> 152 kJ/mol\n  CO2/CH4  ->  31 kJ/mol  (least energy)\n\nMicrobes prefer the highest available energy source." },
	{ "title": "Methanotrophy",
	  "text": "Methanotrophs consume methane (CH4) before\nit reaches the atmosphere. Without them,\natmospheric CH4 would be 10-100x higher.\n\n  CH4 + 2O2 -> CO2 + 2H2O\n\nThey are Earth's methane filter,\noperating in soils, wetlands, and ocean\nsediments worldwide." },
	{ "title": "Denitrification",
	  "text": "Denitrifying microbes convert nitrate (NO3-)\nto harmless nitrogen gas (N2).\n\n  2NO3- + 10e- + 12H+ -> N2 + 6H2O\n\nWithout them, nitrous oxide (N2O) - a\ngreenhouse gas 300x stronger than CO2 -\nwould accumulate in the atmosphere." },
	{ "title": "Diffusion vs Advection",
	  "text": "Nutrients reach microbes two ways:\n\n  Advection: carried by flowing water\n    (fast, directional)\n  Diffusion: random molecular motion\n    (slow, spreads in all directions)\n\nThe Peclet number (Pe = uL/D) tells us\nwhich dominates. In deep sediments,\nPe << 1: diffusion rules." },
	{ "title": "Monod Kinetics",
	  "text": "Microbial growth follows the Monod equation:\n\n  mu = mu_max * C / (Ks + C)\n\nWhen substrate C >> Ks: growth is maximal\nWhen C << Ks: growth nearly stops\nAt C = Ks: growth is half-maximum\n\nThis is why position matters - cells\nnear flow paths get more food." },
	{ "title": "Biofilm Formation (CA)",
	  "text": "When biomass exceeds B_max (100 kg/m3),\nexcess is pushed to neighboring pores.\nThis Cellular Automata model creates\nrealistic biofilm growth patterns.\n\nIn CompLaB3D, a distance field guides\ngrowth toward open pore space,\nmimicking real biofilm expansion." },
	{ "title": "Anaerobic Methane Oxidation",
	  "text": "In oxygen-free zones, archaea partner\nwith sulfate-reducing bacteria:\n\n  CH4 + SO42- -> HCO3- + HS- + H2O\n\nThis 'anaerobic oxidation of methane'\n(AOM) consumes ~90% of oceanic methane\nbefore it reaches the water column." },
	{ "title": "Permafrost Carbon Feedback",
	  "text": "Arctic permafrost stores ~1,500 Gt carbon.\nAs it thaws, microbes decompose this\norganic matter, releasing CH4 and CO2.\n\nBut methanotrophs in the thaw layer\nact as a biological filter, consuming\nmuch of this methane before release.\n\nYour colonies ARE that filter." },
	{ "title": "Hydrothermal Vent Chemistry",
	  "text": "Deep-sea vents release fluids at 300-400C\nrich in H2S, Fe2+, Mn2+, and CH4.\n\nChemosynthetic microbes harvest energy\nfrom these chemicals, forming the base\nof entire ecosystems without sunlight.\n\nThe full redox ladder operates here\nin centimeters of sediment." },
	{ "title": "You Are Earth's Climate Shield",
	  "text": "Subsurface microbes process ~600 Tg CH4/yr,\npreventing most geological methane from\nreaching the atmosphere.\n\nWithout microbial methane consumption,\nEarth's temperature would be\nsignificantly higher.\n\nEvery colony you built represents\na real climate defense mechanism.\n\nCongratulations, Guardian of Earth." },
]

# ── MISSION BRIEFINGS (Elder speaks before each level) ───────────────────────
# Each entry is an array of dialogue lines from the Elder for that level index
const MISSION_BRIEFS := [
	# Level 0: First Breath
	[
		{"speaker": "ELDER", "text": "Your first mission, young one.\nThis is the Soil Frontier -\nshallow soil beneath a meadow."},
		{"speaker": "ELDER", "text": "Oxygen flows from above.\nEat substrates to survive.\nPlace 3 colonies to secure this zone."},
		{"speaker": "METHI", "text": "I'm ready, Archaeon Prime!"},
	],
	# Level 1: Roots of Life
	[
		{"speaker": "ELDER", "text": "You've grown stronger.\nBut now a rival microbe lurks\nin these pores. Be vigilant."},
		{"speaker": "ELDER", "text": "It will steal your food.\nMove fast, eat faster.\nPlace 5 colonies this time."},
	],
	# Level 2: Into the Depths
	[
		{"speaker": "ELDER", "text": "We descend into the Deep Sediment.\nOxygen cannot reach here.\nOnly iron and nitrate remain."},
		{"speaker": "ELDER", "text": "The passages are narrow and dark.\nTwo rivals hunt these corridors.\nConserve your energy carefully."},
		{"speaker": "METHI", "text": "No oxygen? How do I survive?"},
		{"speaker": "ELDER", "text": "Use the redox ladder, child.\nNitrate and iron will sustain you.\nAnd never stop eating methane!"},
	],
	# Level 3: The Hungry Dark
	[
		{"speaker": "ELDER", "text": "Deeper still. The sediment\ntightens around us.\nThree rivals compete for scraps."},
		{"speaker": "ELDER", "text": "Manganese joins your options now.\nBut food is scarce - every\nmolecule matters here."},
	],
	# Level 4: The Methane Vents
	[
		{"speaker": "ELDER", "text": "Now we enter the Methane Seeps!\nCH4 erupts from volcanic vents below.\nThis is where our kind truly shines."},
		{"speaker": "ELDER", "text": "Beware the toxic zones - they\nburn through your cell membrane.\nAvoid the purple areas!"},
		{"speaker": "METHI", "text": "The methane... I can feel it rising."},
		{"speaker": "ELDER", "text": "Consume it! Every molecule of CH4\nyou eat prevents global warming.\nYou are Earth's climate shield!"},
	],
	# Level 5: Vent Guardians
	[
		{"speaker": "ELDER", "text": "The vents grow stronger.\nMore methane, more toxins,\nmore rivals. Stay focused."},
		{"speaker": "ELDER", "text": "Place 8 colonies to build\na biofilm wall against\nthe rising greenhouse gases."},
	],
	# Level 6: Thawing Grounds
	[
		{"speaker": "ELDER", "text": "The Permafrost Edge... the ice\nis melting. Ancient carbon\nunlocks after millennia."},
		{"speaker": "ELDER", "text": "The flow here is fast and chaotic.\nUse SHIFT to ride the currents.\nIt will save your energy."},
		{"speaker": "METHI", "text": "The water moves so fast here!"},
		{"speaker": "ELDER", "text": "The melting permafrost releases\n1,500 gigatons of trapped carbon.\nWe are the last line of defense."},
	],
	# Level 7: The Great Thaw
	[
		{"speaker": "ELDER", "text": "This is critical. The thaw\naccelerates. Four rivals compete.\nMethane pulses are massive."},
		{"speaker": "ELDER", "text": "Build 8 colonies. Create a\nbiofilm barrier. The planet's\nfuture depends on us."},
	],
	# Level 8: The Abyss
	[
		{"speaker": "ELDER", "text": "The Hydrothermal Realm.\nDeep ocean vents blast superheated\nfluid through mineral chimneys."},
		{"speaker": "ELDER", "text": "The full redox ladder is here -\nsulfate, iron, manganese, methane.\nUse everything available to you."},
		{"speaker": "METHI", "text": "It's so hot... and hostile."},
		{"speaker": "ELDER", "text": "Only the strongest archaea\nsurvive here. But you have\ngrown beyond my expectations."},
	],
	# Level 9: Earth's Last Stand
	[
		{"speaker": "ELDER", "text": "This is it. The final stand.\nEvery greenhouse gas that escapes\nthese vents warms the planet."},
		{"speaker": "ELDER", "text": "Five rivals. Toxic zones everywhere.\n12 colonies needed to seal\nthe vent network permanently."},
		{"speaker": "METHI", "text": "I won't let you down, Elder."},
		{"speaker": "ELDER", "text": "You have become a true Guardian\nof Earth. Now show the world\nwhat one archaea can do!"},
	],
]

# ── RUNTIME STATE ────────────────────────────────────────────────────────────
var current_state: State = State.BOOT
var current_level: int = 0
var total_score: int = 0
var methane_prevented: float = 0.0
var n2o_prevented: float = 0.0
var game_time: float = 0.0

func get_level_def() -> Dictionary:
	if current_level < LEVELS.size():
		return LEVELS[current_level]
	return LEVELS[0]

func get_env_pal() -> Dictionary:
	var env = get_level_def().get("env", 0)
	if env < ENV_PAL.size():
		return ENV_PAL[env]
	return ENV_PAL[0]
