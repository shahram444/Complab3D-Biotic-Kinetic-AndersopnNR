/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   CONFIG: Sprite data, color palettes, scene timing constants
   ============================================================ */

const CFG = {
  W: 1920, H: 1080,
  TILE: 32,
  PIXEL_SCALE: 4,        // scale for close-up renders
  DURATION: 125,         // total trailer seconds
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
    '....kHHHHHk.....',
    '...kHHHHHHHk....',
    '..kHVVVVVVVHk...',
    '..kVXXVVVXXVk...',
    '..kVXwwVwwXVk...',
    '..kVVwekweVVk...',
    '..kHVVVVVVVHk...',
    '..kkHHkkkHHkk...',
    '..kTTTTTTTTTk...',
    '..kTTTTTTTTTk...',
    '..kTtTTTTTtTk...',
    '...ktTTTTTtk....',
    '....ktttttkk....',
    '.....kkkkk......',
    '......k.k.......',
    '................'
  ],
  methi_right: [
    '................',
    '......kHHHHHk...',
    '.....kHVVVVVHk..',
    '.....kVVVVXXVk..',
    '.....kVVVewXVkk.',
    '.....kHVVVVVHk..',
    '.....kkHHkkHHkk.',
    '.....kTTTTTTTk..',
    '.....kTTTTTTk...',
    '.....kTtTTtTk...',
    '......ktTTtk....',
    '......kttttk....',
    '.......kkkk.....',
    '.........k......',
    '................',
    '................'
  ],
  methi_left: [
    '................',
    '...kHHHHHk......',
    '..kHVVVVVHk.....',
    '..kVXXVVVVk.....',
    '.kkVXweVVVk.....',
    '.kHVVVVVVHk.....',
    '.kkHHkkHHkk.....',
    '.kTTTTTTTTk.....',
    '..kTTTTTTTk.....',
    '..kTtTTTtTk.....',
    '...ktTTTtk......',
    '....kttttk......',
    '.....kkkk.......',
    '......k.........',
    '................',
    '................'
  ],
  methi_eat: [
    '....kHHHHHk.....',
    '...kHHHHHHHk....',
    '..kHVVVVVVVHk...',
    '..kVXXVVVXXVk...',
    '..kVXwwVwwXVk...',
    '..kVVwekweVVk...',
    '..kHVVkkkVVHk...',
    '..kkHkssskHkk...',
    '..kTTTkkkTTTk...',
    '..kTTTTTTTTTk...',
    '..kTtTTTTTtTk...',
    '...ktTTTTTtk....',
    '....ktttttkk....',
    '.....kkkkk......',
    '................',
    '................'
  ],
  methi_glow: [
    '...skHHHHHks....',
    '..skHHHHHHHks...',
    '.skHVVVVVVVHks..',
    '.skVXXVVVXXVks..',
    '.skVXwwVwwXVks..',
    '.skVVwekweVVks..',
    '.skHVVVVVVVHks..',
    '.skkHHkkkHHkks..',
    '.skLTTTTTTTLks..',
    '.skLTTTTTTTLks..',
    '..skLtTTTtLks...',
    '...skLTTTLks....',
    '....skkkkks.....',
    '.....ssssss.....',
    '................',
    '................'
  ],
  methi_hurt: [
    '....kHHHHHk.....',
    '...kHHHHHHHk....',
    '..kHhhhhhhhHk...',
    '..khhkkkhkkhk...',
    '..khhhhhhhhhk...',
    '..khhhhhhhhhk...',
    '..kHhhhhhhhHk...',
    '..kkHHkkkHHkk...',
    '..khhhhhhhhhk...',
    '..khhhhhhhhhk...',
    '..khhhhhhhhhk...',
    '...khhhhhhhhk...',
    '....khhhhhhk....',
    '.....kkkkkk.....',
    '................',
    '................'
  ],
  elder: [
    '....kkkkkk......',
    '...kjjjjjjk.....',
    '..kjJjjjjJjk....',
    '.kjJwwjjwwJjk...',
    '.kjjwejjewjjk...',
    '.kjjjjjjjjjjk...',
    '.kjjjjmjjjjjk...',
    '..kjjjjjjjjk....',
    '..kkjjjjjjkk....',
    '.kqqkjjjjkqqk...',
    '.kqqqjjjjqqqk...',
    '..kqqqqqqqqk....',
    '...kqqqqqqk.....',
    '....kkkkkk......',
    '......k.k.......',
    '................'
  ],
  rival: [
    '...kkkk...',
    '..kzZZzk..',
    '.kzwZwZzk.',
    '.kzeZeZzk.',
    '.kzZZZZzk.',
    '.kzZmZZzk.',
    '..kzZZzk..',
    '...kzzk...',
    '....kk....',
    '..........'
  ],
  sub_o2: [
    '..kkkkkk..',
    '.kiiiiiik.',
    'kiIIIIIIik',
    'kiIIIIIIik',
    'kiIIIIIIik',
    'kiIIIIIIik',
    'kiIIIIIIik',
    'kiiiiiiiik',
    '.kiiiiik..',
    '..kkkkkk..'
  ],
  sub_no3: [
    '....kk....',
    '...kGGk...',
    '..kGGGGk..',
    '.kGGGGGGk.',
    'kGGGGGGGGk',
    'kGGGGGGGGk',
    '.kGGGGGGk.',
    '..kGGGGk..',
    '...kGGk...',
    '....kk....'
  ],
  sub_mn4: [
    '....kk....',
    '...kPPk...',
    '..kPPPPk..',
    'kkPPPPPPkk',
    'kPPPPPPPPk',
    'kPPPPPPPPk',
    'kkPPPPPPkk',
    '..kPPPPk..',
    '...kPPk...',
    '....kk....'
  ],
  sub_fe3: [
    '....kk....',
    '...kook...',
    '..koOOok..',
    '.koOOOOok.',
    'koOOOOOOok',
    'koOOOOOOok',
    '.koOOOOok.',
    '..koOOok..',
    '...kook...',
    '....kk....'
  ],
  sub_so4: [
    '...kkkk...',
    '..kYYYYk..',
    '.kYYYYYYk.',
    'kYYYYYYYYk',
    'kYYYYYYYYk',
    'kYYYYYYYYk',
    'kYYYYYYYYk',
    '.kYYYYYYk.',
    '..kYYYYk..',
    '...kkkk...'
  ],
  sub_ch4: [
    '....kk....',
    '...kRRk...',
    '..kRrrRk..',
    '.kRrrrrRk.',
    '.kRrrrRRk.',
    'kRRrrRRRRk',
    'kRRRRRRRRk',
    '.kRRRRRRk.',
    '..kRRRRk..',
    '...kkkk...'
  ],
  colony: [
    '...kkkkkk...',
    '..kfFFFFFk..',
    '.kfFFFFFFfk.',
    'kfFFFFFFFFFk',
    'kFFFFFFFFFFk',
    'kFFFFFFFFFFk',
    'kFFFFFFFFFFk',
    'kfFFFFFFFfFk',
    '.kfFFFFFFfk.',
    '..kvFFFfvk..',
    '...kkkkkk...',
    '............'
  ]
};

/* ── ENVIRONMENT PALETTES (exact from game) ── */
const ENV_PAL = [
  { name: 'The Soil Frontier', sub: 'Where Life Begins',
    grain: '#7a5a2a', grain_l: '#a48a5a', grain_d: '#4a3a1a', grain_a: '#c4a060',
    pore: '#0c1420', pore_l: '#142030', water: '#1a3a60', water_l: '#3060a0',
    bg: '#060c18', toxic: '#8a3a8a', toxic_g: '#c060c0' },
  { name: 'The Deep Sediment', sub: 'Darkness Below',
    grain: '#4a3a2a', grain_l: '#6a5a4a', grain_d: '#2a1a0a', grain_a: '#5a4a3a',
    pore: '#060608', pore_l: '#0c0c14', water: '#0a1428', water_l: '#142038',
    bg: '#030306', toxic: '#6a2a2a', toxic_g: '#a04040' },
  { name: 'The Methane Seeps', sub: 'Rivers of Fire',
    grain: '#3a3040', grain_l: '#5a5060', grain_d: '#2a2030', grain_a: '#4a4050',
    pore: '#0a0610', pore_l: '#140c1c', water: '#1a1438', water_l: '#2a1a48',
    bg: '#06040a', toxic: '#7a1a6a', toxic_g: '#b040a0' },
  { name: 'The Permafrost Edge', sub: 'The Melting World',
    grain: '#5a6a7a', grain_l: '#8a9aaa', grain_d: '#3a4a5a', grain_a: '#aabaca',
    pore: '#080c14', pore_l: '#0c1420', water: '#1a3050', water_l: '#3a5a8a',
    bg: '#040810', toxic: '#4a7a3a', toxic_g: '#70b050' },
  { name: 'The Hydrothermal Realm', sub: 'Earth\'s Furnace',
    grain: '#2a2a3a', grain_l: '#4a4a5a', grain_d: '#1a1a2a', grain_a: '#3a3a4a',
    pore: '#0a0608', pore_l: '#14080c', water: '#281418', water_l: '#3a1a20',
    bg: '#060304', toxic: '#8a4a1a', toxic_g: '#c07030' }
];

/* ── SUBSTRATE INFO ── */
const SUBSTRATES = {
  O2:  { name: 'Oxygen',    color: '#4fa4ff', glow: '#8fc8ff', sprite: 'sub_o2' },
  NO3: { name: 'Nitrate',   color: '#4fdf6f', glow: '#8fff9f', sprite: 'sub_no3' },
  MN4: { name: 'Manganese',  color: '#cf6fff', glow: '#df9fff', sprite: 'sub_mn4' },
  FE3: { name: 'Iron',      color: '#ef8f3f', glow: '#ffbf7f', sprite: 'sub_fe3' },
  SO4: { name: 'Sulfate',   color: '#dfdf3f', glow: '#ffffaf', sprite: 'sub_so4' },
  CH4: { name: 'Methane',   color: '#ff4f4f', glow: '#ff9f7f', sprite: 'sub_ch4' }
};

/* ── SCENE TIMELINE (seconds) ── */
const TIMELINE = {
  BLACK_OPEN:      { start: 0,   end: 5 },
  PIXEL_AWAKEN:    { start: 5,   end: 12 },
  ELDER_CALLS:     { start: 12,  end: 22 },
  WORLD_REVEAL:    { start: 22,  end: 38 },
  RIVALS_THREAT:   { start: 38,  end: 50 },
  POWER_GROW:      { start: 50,  end: 65 },
  JOURNEY_MONTAGE: { start: 65,  end: 82 },
  EARTH_STAKES:    { start: 82,  end: 95 },
  TITLE_REVEAL:    { start: 95,  end: 108 },
  CLOSING:         { start: 108, end: 125 }
};

/* ── NARRATION SCRIPT ── */
const NARRATION = [
  { t: 1.0,  dur: 3.5, text: 'Deep beneath the surface...', style: 'whisper' },
  { t: 6.0,  dur: 3.0, text: 'Between grains of ancient rock...', style: 'whisper' },
  { t: 10.0, dur: 2.5, text: 'Something stirs.', style: 'whisper' },

  { t: 13.0, dur: 3.0, speaker: 'ELDER', text: 'Awaken, young one.' },
  { t: 16.5, dur: 3.5, speaker: 'ELDER', text: 'The Earth calls for you.' },
  { t: 20.5, dur: 2.0, speaker: 'ARKE',  text: 'What... is this place?' },

  { t: 23.0, dur: 4.0, text: 'A WORLD INVISIBLE TO THE NAKED EYE', style: 'title' },
  { t: 28.0, dur: 3.0, text: 'Five realms. One mission.', style: 'subtitle' },
  { t: 32.0, dur: 3.0, text: 'From sunlit soil...', style: 'subtitle' },
  { t: 35.5, dur: 3.0, text: '...to the depths of fire.', style: 'subtitle' },

  { t: 39.0, dur: 3.0, speaker: 'ELDER', text: 'Beware the rivals.' },
  { t: 42.5, dur: 3.5, speaker: 'ELDER', text: 'They hunger for what you need to survive.' },
  { t: 46.5, dur: 3.5, text: 'COMPETE. OR PERISH.', style: 'impact' },

  { t: 51.0, dur: 2.5, text: 'CONSUME.', style: 'impact' },
  { t: 54.0, dur: 2.5, text: 'GROW.', style: 'impact' },
  { t: 57.0, dur: 2.5, text: 'MULTIPLY.', style: 'impact' },
  { t: 60.0, dur: 4.0, speaker: 'ELDER', text: 'Build the biofilm. Become the shield.' },

  { t: 66.0, dur: 3.5, text: 'THE SOIL FRONTIER', style: 'chapter' },
  { t: 69.5, dur: 3.0, text: 'THE DEEP SEDIMENT', style: 'chapter' },
  { t: 72.5, dur: 3.0, text: 'THE METHANE SEEPS', style: 'chapter' },
  { t: 75.5, dur: 3.0, text: 'THE PERMAFROST EDGE', style: 'chapter' },
  { t: 78.5, dur: 3.5, text: 'THE HYDROTHERMAL REALM', style: 'chapter' },

  { t: 83.0, dur: 4.0, speaker: 'ELDER', text: '600 trillion grams of methane. Every year.' },
  { t: 87.5, dur: 3.5, speaker: 'ELDER', text: 'Without us... the planet burns.' },
  { t: 91.5, dur: 3.0, speaker: 'ARKE', text: 'I won\'t let Earth down.' },

  { t: 96.0, dur: 5.0, text: 'ARKE', style: 'logo' },
  { t: 101.5, dur: 4.0, text: 'GUARDIANS OF EARTH', style: 'logo_sub' },
  { t: 106.0, dur: 3.0, text: 'The Invisible Shield', style: 'tagline' },

  { t: 110.0, dur: 3.0, text: '10 Levels  •  5 Worlds  •  Real Science', style: 'features' },
  { t: 114.0, dur: 4.0, text: 'COMING SOON', style: 'coming' },
  { t: 119.0, dur: 5.0, text: 'Based on CompLaB3D Research\nUniversity of Georgia', style: 'credit' }
];
