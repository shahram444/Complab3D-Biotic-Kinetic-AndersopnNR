/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   CONFIG: Sprite data, color palettes, scene timing, narration
   ============================================================ */

const CFG = {
  W: 1920, H: 1080,
  TILE: 32,
  PIXEL_SCALE: 4,
  DURATION: 160,         // extended for new scenes
  FPS: 60
};

/* ── COLOR PALETTE (exact match from game sprite_factory.gd) ── */
const PAL = {
  '.': null,
  'k': '#000000', 'w': '#ffffff', 'W': '#cccccc',
  'a': '#888888', 'A': '#444444',
  't': '#1a8a7a', 'T': '#2acfaf', 'L': '#5fffdf',
  'd': '#0a5a4a', 'D': '#084038',
  'b': '#7a5a2a', 'B': '#a48a5a', 'n': '#4a3a1a', 'N': '#c4a060',
  'u': '#1a3a60', 'U': '#3060a0', 'c': '#50b0c0', 'C': '#80d0e0',
  'o': '#ef8f3f', 'O': '#ffbf7f', 'y': '#dfdf3f', 'Y': '#ffffaf',
  'r': '#ff4f4f', 'R': '#ff9f7f', 'g': '#4fdf6f', 'G': '#8fff9f',
  'p': '#cf6fff', 'P': '#df9fff', 'i': '#4fa4ff', 'I': '#8fc8ff',
  'V': '#40c8d8', 'H': '#7888a0', 'X': '#90e8f0',
  'e': '#1a1a2e', 's': '#ffff5f', 'h': '#ff6644', 'm': '#0a6a5a',
  'f': '#3a7a5a', 'F': '#5aaa7a', 'v': '#2a5a4a',
  'j': '#1a1aa0', 'J': '#4848d0', 'q': '#5030a0', 'Q': '#7050c0',
  'z': '#b03030', 'Z': '#e06060'
};

/* ── SPRITE DATA (exact from game) ── */
const SPRITES = {
  methi_down: [
    '....kHHHHHk.....','...kHHHHHHHk....','..kHVVVVVVVHk...','..kVXXVVVXXVk...',
    '..kVXwwVwwXVk...','..kVVwekweVVk...','..kHVVVVVVVHk...','..kkHHkkkHHkk...',
    '..kTTTTTTTTTk...','..kTTTTTTTTTk...','..kTtTTTTTtTk...','...ktTTTTTtk....',
    '....ktttttkk....','.....kkkkk......','......k.k.......','................'
  ],
  methi_right: [
    '................','......kHHHHHk...','.....kHVVVVVHk..','.....kVVVVXXVk..',
    '.....kVVVewXVkk.','.....kHVVVVVHk..','.....kkHHkkHHkk.','.....kTTTTTTTk..',
    '.....kTTTTTTk...','.....kTtTTtTk...','......ktTTtk....','......kttttk....',
    '.......kkkk.....','.........k......','................','................'
  ],
  methi_left: [
    '................','...kHHHHHk......','..kHVVVVVHk.....','..kVXXVVVVk.....',
    '.kkVXweVVVk.....','.kHVVVVVVHk.....','.kkHHkkHHkk.....','.kTTTTTTTTk.....',
    '..kTTTTTTTk.....','..kTtTTTtTk.....','...ktTTTtk......','....kttttk......',
    '.....kkkk.......','......k.........','................','................'
  ],
  methi_eat: [
    '....kHHHHHk.....','...kHHHHHHHk....','..kHVVVVVVVHk...','..kVXXVVVXXVk...',
    '..kVXwwVwwXVk...','..kVVwekweVVk...','..kHVVkkkVVHk...','..kkHkssskHkk...',
    '..kTTTkkkTTTk...','..kTTTTTTTTTk...','..kTtTTTTTtTk...','...ktTTTTTtk....',
    '....ktttttkk....','.....kkkkk......','................','................'
  ],
  methi_glow: [
    '...skHHHHHks....','..skHHHHHHHks...','.skHVVVVVVVHks..','.skVXXVVVXXVks..',
    '.skVXwwVwwXVks..','.skVVwekweVVks..','.skHVVVVVVVHks..','.skkHHkkkHHkks..',
    '.skLTTTTTTTLks..','.skLTTTTTTTLks..','..skLtTTTtLks...','...skLTTTLks....',
    '....skkkkks.....','.....ssssss.....','................','................'
  ],
  methi_hurt: [
    '....kHHHHHk.....','...kHHHHHHHk....','..kHhhhhhhhHk...','..khhkkkhkkhk...',
    '..khhhhhhhhhk...','..khhhhhhhhhk...','..kHhhhhhhhHk...','..kkHHkkkHHkk...',
    '..khhhhhhhhhk...','..khhhhhhhhhk...','..khhhhhhhhhk...','...khhhhhhhhk...',
    '....khhhhhhk....','.....kkkkkk.....','................','................'
  ],
  elder: [
    '....kkkkkk......','...kjjjjjjk.....','..kjJjjjjJjk....','.kjJwwjjwwJjk...',
    '.kjjwejjewjjk...','.kjjjjjjjjjjk...','.kjjjjmjjjjjk...','..kjjjjjjjjk....',
    '..kkjjjjjjkk....','.kqqkjjjjkqqk...','.kqqqjjjjqqqk...','..kqqqqqqqqk....',
    '...kqqqqqqk.....','....kkkkkk......','......k.k.......','................'
  ],
  rival: [
    '...kkkk...','..kzZZzk..','.kzwZwZzk.','.kzeZeZzk.','.kzZZZZzk.',
    '.kzZmZZzk.','..kzZZzk..','...kzzk...','....kk....','..........'
  ],
  sub_o2:  ['..kkkkkk..','.kiiiiiik.','kiIIIIIIik','kiIIIIIIik','kiIIIIIIik','kiIIIIIIik','kiIIIIIIik','kiiiiiiiik','.kiiiiik..','..kkkkkk..'],
  sub_no3: ['....kk....','...kGGk...','..kGGGGk..','.kGGGGGGk.','kGGGGGGGGk','kGGGGGGGGk','.kGGGGGGk.','..kGGGGk..','...kGGk...','....kk....'],
  sub_mn4: ['....kk....','...kPPk...','..kPPPPk..','kkPPPPPPkk','kPPPPPPPPk','kPPPPPPPPk','kkPPPPPPkk','..kPPPPk..','...kPPk...','....kk....'],
  sub_fe3: ['....kk....','...kook...','..koOOok..','.koOOOOok.','koOOOOOOok','koOOOOOOok','.koOOOOok.','..koOOok..','...kook...','....kk....'],
  sub_so4: ['...kkkk...','..kYYYYk..','.kYYYYYYk.','kYYYYYYYYk','kYYYYYYYYk','kYYYYYYYYk','kYYYYYYYYk','.kYYYYYYk.','..kYYYYk..','...kkkk...'],
  sub_ch4: ['....kk....','...kRRk...','..kRrrRk..','.kRrrrrRk.','.kRrrrRRk.','kRRrrRRRRk','kRRRRRRRRk','.kRRRRRRk.','..kRRRRk..','...kkkk...'],
  colony: ['...kkkkkk...','..kfFFFFFk..','.kfFFFFFFfk.','kfFFFFFFFFFk','kFFFFFFFFFFk','kFFFFFFFFFFk','kFFFFFFFFFFk','kfFFFFFFFfFk','.kfFFFFFFfk.','..kvFFFfvk..','...kkkkkk...','............']
};

/* ── ENVIRONMENT PALETTES (exact from game) ── */
const ENV_PAL = [
  { name: 'The Soil Frontier', sub: 'Where Life Begins', depth: '0 - 2 meters',
    grain: '#7a5a2a', grain_l: '#a48a5a', grain_d: '#4a3a1a', grain_a: '#c4a060',
    pore: '#0c1420', pore_l: '#142030', water: '#1a3a60', water_l: '#3060a0',
    bg: '#060c18', toxic: '#8a3a8a', toxic_g: '#c060c0' },
  { name: 'The Deep Sediment', sub: 'Darkness Below', depth: '100 - 500 meters',
    grain: '#4a3a2a', grain_l: '#6a5a4a', grain_d: '#2a1a0a', grain_a: '#5a4a3a',
    pore: '#060608', pore_l: '#0c0c14', water: '#0a1428', water_l: '#142038',
    bg: '#030306', toxic: '#6a2a2a', toxic_g: '#a04040' },
  { name: 'The Methane Seeps', sub: 'Rivers of Fire', depth: '200 - 1000 meters',
    grain: '#3a3040', grain_l: '#5a5060', grain_d: '#2a2030', grain_a: '#4a4050',
    pore: '#0a0610', pore_l: '#140c1c', water: '#1a1438', water_l: '#2a1a48',
    bg: '#06040a', toxic: '#7a1a6a', toxic_g: '#b040a0' },
  { name: 'The Permafrost Edge', sub: 'The Melting World', depth: '1 - 50 meters (Arctic)',
    grain: '#5a6a7a', grain_l: '#8a9aaa', grain_d: '#3a4a5a', grain_a: '#aabaca',
    pore: '#080c14', pore_l: '#0c1420', water: '#1a3050', water_l: '#3a5a8a',
    bg: '#040810', toxic: '#4a7a3a', toxic_g: '#70b050' },
  { name: 'The Hydrothermal Realm', sub: 'Earth\'s Furnace', depth: '2000 - 4000 meters',
    grain: '#2a2a3a', grain_l: '#4a4a5a', grain_d: '#1a1a2a', grain_a: '#3a3a4a',
    pore: '#0a0608', pore_l: '#14080c', water: '#281418', water_l: '#3a1a20',
    bg: '#060304', toxic: '#8a4a1a', toxic_g: '#c07030' }
];

/* ── SUBSTRATE INFO ── */
const SUBSTRATES = {
  O2:  { name: 'Oxygen',    color: '#4fa4ff', glow: '#8fc8ff', sprite: 'sub_o2' },
  NO3: { name: 'Nitrate',   color: '#4fdf6f', glow: '#8fff9f', sprite: 'sub_no3' },
  MN4: { name: 'Manganese', color: '#cf6fff', glow: '#df9fff', sprite: 'sub_mn4' },
  FE3: { name: 'Iron',      color: '#ef8f3f', glow: '#ffbf7f', sprite: 'sub_fe3' },
  SO4: { name: 'Sulfate',   color: '#dfdf3f', glow: '#ffffaf', sprite: 'sub_so4' },
  CH4: { name: 'Methane',   color: '#ff4f4f', glow: '#ff9f7f', sprite: 'sub_ch4' }
};

/* ── CHARACTER INFO (for close-up intros) ── */
const CHARACTERS = {
  ARKE: {
    sprite: 'methi_down', name: 'A R K E',
    title: 'Methanotrophic Archaeon',
    desc: 'A single-celled organism born to consume\ngreenhouse gases and protect the planet.',
    color: '#2acfaf', glow: '#5fffdf'
  },
  ELDER: {
    sprite: 'elder', name: 'ARCHAEON PRIME',
    title: 'Elder of the Methanotrophs',
    desc: 'Ancient guardian of the subsurface.\nBillions of years of wisdom.',
    color: '#4848d0', glow: '#7050c0'
  },
  RIVAL: {
    sprite: 'rival', name: 'THE RIVALS',
    title: 'Competing Bacteria',
    desc: 'They hunger. They hunt.\nThey will steal everything you need.',
    color: '#e06060', glow: '#ff4444'
  }
};

/* ── EARTH CROSS-SECTION DATA (scientifically accurate depths) ── */
const EARTH_LAYERS = [
  { name: 'Atmosphere',  color: '#4488cc', y: 0.02, h: 0.03 },
  { name: 'Surface',     color: '#4a8a3a', y: 0.05, h: 0.02 },
  { name: 'Soil',        color: '#7a5a2a', y: 0.07, h: 0.08, env: 0 },
  { name: 'Permafrost',  color: '#8a9aaa', y: 0.12, h: 0.05, env: 3 },
  { name: 'Sediment',    color: '#4a3a2a', y: 0.15, h: 0.15, env: 1 },
  { name: 'Ocean Floor', color: '#1a2a4a', y: 0.30, h: 0.20 },
  { name: 'Methane Seeps', color: '#3a3040', y: 0.40, h: 0.10, env: 2 },
  { name: 'Deep Crust',  color: '#2a2a3a', y: 0.50, h: 0.20 },
  { name: 'Hydrothermal', color: '#4a2020', y: 0.65, h: 0.10, env: 4 },
  { name: 'Mantle',      color: '#8a3020', y: 0.75, h: 0.25 }
];

/* ── SCENE TIMELINE (seconds) — extended with new scenes ── */
const TIMELINE = {
  BLACK_OPEN:       { start: 0,    end: 5 },
  PIXEL_AWAKEN:     { start: 5,    end: 12 },
  ARKE_CLOSEUP:     { start: 12,   end: 20 },
  ELDER_CLOSEUP:    { start: 20,   end: 27 },
  ELDER_CALLS:      { start: 27,   end: 38 },
  EARTH_CROSS:      { start: 38,   end: 63 },
  RIVAL_CLOSEUP:    { start: 63,   end: 69 },
  RIVALS_THREAT:    { start: 69,   end: 81 },
  POWER_GROW:       { start: 81,   end: 96 },
  JOURNEY_MONTAGE:  { start: 96,   end: 113 },
  EARTH_STAKES:     { start: 113,  end: 126 },
  TITLE_REVEAL:     { start: 126,  end: 139 },
  CLOSING:          { start: 139,  end: 160 }
};

/* ── NARRATION SCRIPT — longer durations for readability ── */
const NARRATION = [
  // BLACK OPEN
  { t: 1.0,  dur: 4.0, text: 'Deep beneath the surface...', style: 'whisper' },
  // PIXEL AWAKEN
  { t: 6.0,  dur: 4.0, text: 'Between grains of ancient rock...', style: 'whisper' },
  { t: 10.5, dur: 2.5, text: 'Something stirs.', style: 'whisper' },

  // ARKE CLOSEUP
  { t: 13.5, dur: 6.0, text: 'A R K E', style: 'logo' },
  { t: 15.0, dur: 4.5, text: 'Methanotrophic Archaeon', style: 'tagline' },

  // ELDER CLOSEUP
  { t: 21.0, dur: 5.5, text: 'ARCHAEON PRIME', style: 'chapter' },
  { t: 23.0, dur: 4.0, text: 'Elder of the Methanotrophs', style: 'tagline' },

  // ELDER CALLS — longer holds
  { t: 28.0, dur: 5.0, speaker: 'ELDER', text: 'Awaken, young one.\nThe Earth calls for you.' },
  { t: 33.5, dur: 4.5, speaker: 'ARKE',  text: 'What... is this place?' },

  // EARTH CROSS-SECTION — each world intro
  { t: 39.0, dur: 5.0, text: 'A WORLD INVISIBLE\nTO THE NAKED EYE', style: 'title' },
  { t: 44.0, dur: 4.5, text: 'THE SOIL FRONTIER\nDepth: 0 - 2 meters', style: 'chapter' },
  { t: 48.5, dur: 4.5, text: 'THE DEEP SEDIMENT\nDepth: 100 - 500 meters', style: 'chapter' },
  { t: 53.0, dur: 4.0, text: 'THE METHANE SEEPS\nDepth: 200 - 1000 meters', style: 'chapter' },
  { t: 57.0, dur: 3.5, text: 'THE PERMAFROST EDGE\nArctic: 1 - 50 meters', style: 'chapter' },
  { t: 60.5, dur: 3.5, text: 'THE HYDROTHERMAL REALM\nDepth: 2000 - 4000 meters', style: 'chapter' },

  // RIVAL CLOSEUP
  { t: 64.0, dur: 5.0, text: 'THE RIVALS', style: 'impact' },

  // RIVALS THREAT
  { t: 70.0, dur: 5.0, speaker: 'ELDER', text: 'Beware the rivals.\nThey hunger for what you need.' },
  { t: 76.0, dur: 4.5, text: 'COMPETE. OR PERISH.', style: 'impact' },

  // POWER GROW
  { t: 82.0, dur: 4.0, text: 'CONSUME.', style: 'impact' },
  { t: 86.0, dur: 4.0, text: 'GROW.', style: 'impact' },
  { t: 90.0, dur: 4.0, text: 'MULTIPLY.', style: 'impact' },
  { t: 93.0, dur: 4.5, speaker: 'ELDER', text: 'Build the biofilm.\nBecome the shield.' },

  // JOURNEY MONTAGE — chapter names stay on longer
  { t: 97.0,  dur: 3.5, text: 'THE SOIL FRONTIER', style: 'chapter' },
  { t: 100.5, dur: 3.0, text: 'THE DEEP SEDIMENT', style: 'chapter' },
  { t: 103.5, dur: 3.0, text: 'THE METHANE SEEPS', style: 'chapter' },
  { t: 106.5, dur: 3.0, text: 'THE PERMAFROST EDGE', style: 'chapter' },
  { t: 109.5, dur: 3.5, text: 'THE HYDROTHERMAL REALM', style: 'chapter' },

  // EARTH STAKES
  { t: 114.0, dur: 5.0, speaker: 'ELDER', text: '600 trillion grams of methane.\nEvery year.' },
  { t: 119.5, dur: 4.0, speaker: 'ELDER', text: 'Without us... the planet burns.' },
  { t: 123.5, dur: 3.5, speaker: 'ARKE', text: 'I won\'t let Earth down.' },

  // TITLE REVEAL
  { t: 127.0, dur: 6.0, text: 'ARKE', style: 'logo' },
  { t: 133.0, dur: 4.5, text: 'GUARDIANS OF EARTH', style: 'logo_sub' },
  { t: 137.0, dur: 3.0, text: 'The Invisible Shield', style: 'tagline' },

  // CLOSING
  { t: 141.0, dur: 5.0, text: '10 Levels  •  5 Worlds  •  Real Science', style: 'features' },
  { t: 147.0, dur: 5.0, text: 'COMING SOON', style: 'coming' },
  { t: 153.0, dur: 6.0, text: 'Based on CompLaB3D Research\nUniversity of Georgia', style: 'credit' }
];
