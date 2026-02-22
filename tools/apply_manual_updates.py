#!/usr/bin/env python3
"""
Apply pixel-perfect game-sprite images to all manual HTML sections.
Replaces organic SVG illustrations with scaled-up renderings of actual pixel art
from sprite_factory.gd, and tile-grid screenshots using real ENV_PAL colors.
"""

import sys, os, random

# Add tools to path
sys.path.insert(0, os.path.dirname(__file__))
from update_manual_images import (
    s2svg, world_grid, PAL, ENV_PAL,
    METHI_DOWN, METHI_UP, METHI_LEFT, METHI_RIGHT,
    METHI_EAT, METHI_GLOW, METHI_HURT, METHI_DIE,
    ELDER, RIVAL_BASE, COLONY,
    SUB_O2, SUB_NO3, SUB_MN4, SUB_FE3, SUB_SO4, SUB_CH4
)

DOCS = os.path.join(os.path.dirname(__file__), '..', 'docs', 'manual_sections')


def gen_03_characters():
    """Generate updated 03_characters.html with pixel-perfect game sprites."""

    # Generate all needed SVGs
    arke_portrait = s2svg(METHI_DOWN, 11, 180, 180)
    arke_up = s2svg(METHI_UP, 5, 80, 80)
    arke_down = s2svg(METHI_DOWN, 5, 80, 80)
    arke_left = s2svg(METHI_LEFT, 5, 80, 80)
    arke_right = s2svg(METHI_RIGHT, 5, 80, 80)
    arke_eat = s2svg(METHI_EAT, 5, 80, 80)
    arke_glow = s2svg(METHI_GLOW, 5, 80, 80)
    arke_hurt = s2svg(METHI_HURT, 5, 80, 80)
    arke_die = s2svg(METHI_DIE, 5, 80, 80)
    elder_portrait = s2svg(ELDER, 8, 128, 128)
    rival_portrait = s2svg(RIVAL_BASE, 12, 120, 120)
    colony_portrait = s2svg(COLONY, 10, 120, 120)

    html = f'''<!-- Section 03: Characters -->
<div class="page" id="characters" style="page-break-after: always;">
  <h1 class="section-number">SECTION 2</h1>
  <h1 class="section-title">Characters</h1>

  <p style="font-size:9pt; color:#666; margin-bottom:8px; font-style:italic;">
    All character art below is the actual pixel art from the game, rendered at high resolution.
  </p>

  <!-- ARKE Character Card -->
  <div class="char-card">
    <div class="char-sprite" style="width:180px; height:180px; background:#0a1428; border-radius:4px; display:flex; align-items:center; justify-content:center;">
      {arke_portrait}
    </div>
    <div class="char-info">
      <div class="char-name" style="color:#2a8a8a;">ARKE</div>
      <div class="char-desc">
        A young <strong>methanotrophic archaeon</strong>&mdash;a single-celled organism that
        feeds on dissolved chemicals in underground water. ARKE is Earth's front-line defender
        against greenhouse gas emissions, capable of consuming methane and other substrates
        to grow biomass and reproduce through binary fission (division). With a translucent
        sci-fi visor/helmet and teal body, ARKE navigates the dark pore spaces guided by
        chemical gradients.
      </div>
      <div class="char-stats">
        TYPE: Player Character &bull; SIZE: 32&times;32px (16&times;16 sprite, 2&times; scaled) &bull; SPEED: 2.5 tiles/sec (5.0 in planktonic mode)
      </div>
    </div>
  </div>

  <!-- ARKE Directional Sprites -->
  <div style="background:#0a1428; border:2px solid #3a3a4a; border-radius:4px; padding:12px; margin:10px 0;">
    <h3 style="font-size:9pt; margin-bottom:8px; color:#ccc;">ARKE Sprite Sheet &mdash; Actual Game Pixel Art</h3>
    <div style="display:flex; justify-content:space-around; align-items:center; flex-wrap:wrap; gap:4px;">

      <!-- UP -->
      <div style="text-align:center;">
        {arke_up}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#888;margin-top:2px;">UP</div>
      </div>

      <!-- DOWN -->
      <div style="text-align:center;">
        {arke_down}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#888;margin-top:2px;">DOWN</div>
      </div>

      <!-- LEFT -->
      <div style="text-align:center;">
        {arke_left}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#888;margin-top:2px;">LEFT</div>
      </div>

      <!-- RIGHT -->
      <div style="text-align:center;">
        {arke_right}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#888;margin-top:2px;">RIGHT</div>
      </div>

      <!-- EATING -->
      <div style="text-align:center;">
        {arke_eat}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#3a8a3a;margin-top:2px;">EATING</div>
      </div>

      <!-- GLOW (DIVIDE READY) -->
      <div style="text-align:center;">
        {arke_glow}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#aa8a20;margin-top:2px;">DIVIDE!</div>
      </div>
    </div>
  </div>

  <!-- ARKE State Sprites -->
  <div style="background:#0a1428; border:2px solid #3a3a4a; border-radius:4px; padding:12px; margin:10px 0;">
    <h3 style="font-size:9pt; margin-bottom:8px; color:#ccc;">ARKE State Sprites</h3>
    <div style="display:flex; justify-content:space-around; align-items:center; flex-wrap:wrap; gap:8px;">
      <div style="text-align:center;">
        {arke_hurt}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#ff6644;margin-top:2px;">HURT</div>
      </div>
      <div style="text-align:center;">
        {arke_die}
        <div style="font-family:'Press Start 2P',monospace;font-size:6pt;color:#888;margin-top:2px;">DEATH</div>
      </div>
    </div>
  </div>

  <!-- ARKE Vital Stats -->
  <h2>ARKE's Vital Stats</h2>
  <div style="background:white; padding:12px 16px; border:2px solid #3a3a4a; border-radius:4px;">
    <div class="bar-display">
      <span class="bar-label" style="color:#44df5f;">HP</span>
      <div class="bar-track"><div class="bar-fill hp" style="width:100%"></div></div>
      <span style="font-family:'Space Mono',monospace;font-size:8pt;width:40px;text-align:right;">100</span>
    </div>
    <p style="font-size:9pt;margin:2px 0 10px 36px;color:#555; line-height:1.5;">
      <strong>Health</strong> &mdash; Drains at <strong>1.5 per second</strong> constantly due to
      cellular maintenance costs (basal metabolism). At full health (100), you have approximately
      <strong>67 seconds</strong> before death if you eat nothing. When HP drops below
      <strong>30</strong>, screen edges flash red and <strong>"STARVING!"</strong> text appears.
      At 0, game over.
    </p>

    <div class="bar-display">
      <span class="bar-label" style="color:#5fa0f0;">EN</span>
      <div class="bar-track"><div class="bar-fill en" style="width:100%"></div></div>
      <span style="font-family:'Space Mono',monospace;font-size:8pt;width:40px;text-align:right;">100</span>
    </div>
    <p style="font-size:9pt;margin:2px 0 10px 36px;color:#555; line-height:1.5;">
      <strong>Energy</strong> &mdash; Drains at <strong>0.8 per second</strong>. Powers planktonic
      mode (SHIFT key). Each flow-riding move costs <strong>0.5 additional energy</strong>. When EN
      reaches 0, you cannot ride flow and are stuck at normal speed
      (<strong>2.5 tiles/sec</strong> instead of <strong>5.0</strong>).
    </p>

    <div class="bar-display">
      <span class="bar-label" style="color:#5ff050;">GR</span>
      <div class="bar-track"><div class="bar-fill gr" style="width:100%"></div></div>
      <span style="font-family:'Space Mono',monospace;font-size:8pt;width:40px;text-align:right;">100</span>
    </div>
    <p style="font-size:9pt;margin:2px 0 0 36px;color:#555; line-height:1.5;">
      <strong>Growth</strong> &mdash; Does <strong>NOT</strong> decay! This is key&mdash;every substrate
      you eat permanently increases GR. When GR reaches exactly <strong>100</strong>, your body glows
      yellow and you can press <strong>SPACE</strong> to divide. Growth persists even if your HP
      is critically low, so a clutch division is always possible.
    </p>
  </div>

  <p class="page-number left">4</p>
</div>

<!-- Characters page 2: Elder, Rivals -->
<div class="page" id="characters2" style="page-break-after: always;">
  <h2>Elder Archaeon Prime</h2>

  <!-- Elder Character Card -->
  <div class="char-card">
    <div class="char-sprite" style="width:128px; height:128px; background:#0a0a28; border-radius:4px; display:flex; align-items:center; justify-content:center;">
      {elder_portrait}
    </div>
    <div class="char-info">
      <div class="char-name" style="color:#4848d0;">ELDER ARCHAEON PRIME</div>
      <div class="char-desc">
        An ancient archaeon who has guarded the subsurface for eons. With a deep blue body
        and purple lower membrane, the Elder's appearance reflects eons of deep-Earth survival.
        The Elder serves as your mentor, providing mission briefings
        before each level and teaching you the science behind your abilities. Appears during
        cutscenes and narrative sequences.
      </div>
      <div class="char-stats">
        TYPE: Mentor / NPC &bull; SIZE: 16&times;16 sprite &bull; APPEARS: Cutscenes &amp; Briefings
      </div>
    </div>
  </div>

  <h2>Rival Microbes</h2>

  <!-- Rival Character Card -->
  <div class="char-card">
    <div class="char-sprite" style="width:120px; height:120px; background:#1a0a0a; border-radius:4px; display:flex; align-items:center; justify-content:center;">
      {rival_portrait}
    </div>
    <div class="char-info">
      <div class="char-name" style="color:#cc3333;">RIVAL MICROBE</div>
      <div class="char-desc">
        Competing bacteria that hunt for the same substrates as you. Rivals are
        <strong>invulnerable</strong>&mdash;you cannot kill or damage them. They don't
        attack you directly, but they consume food aggressively, creating deadly
        scarcity. With their compact red bodies and white sensor spots, they are efficient
        hunters that use sophisticated decision-making algorithms to find food.
        The more rivals in a level, the harder it becomes to survive.
      </div>
      <div class="char-stats">
        TYPE: Enemy (Competitor) &bull; SIZE: 20&times;20px (10&times;10 sprite, 2&times; scaled) &bull;
        SPEED: 2.5 tiles/sec &bull; SENSE: 12 tiles
      </div>
    </div>
  </div>

  <p class="page-number right">5</p>
</div>

<!-- Characters page 3: How Rivals Sense and Hunt -->
<div class="page" id="characters3" style="page-break-after: always;">
  <h2>How Rivals Sense and Hunt</h2>

  <p style="font-size:10pt; line-height:1.5; margin-bottom:12px;">
    Every <strong>0.4 seconds</strong> (the decision interval), each rival microbe evaluates its
    surroundings and chooses an action from its decision tree. Understanding this algorithm is
    critical to outmaneuvering them.
  </p>

  <!-- Decision Tree Diagram -->
  <div style="background:white; border:2px solid #3a3a4a; border-radius:4px; padding:12px; margin:8px 0;">
    <svg width="100%" height="240" viewBox="0 0 600 240" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="dt-root-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#cc4444"/><stop offset="100%" stop-color="#8a2222"/>
        </linearGradient>
        <linearGradient id="dt-food-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#5aa06a"/><stop offset="100%" stop-color="#3a7a4a"/>
        </linearGradient>
        <linearGradient id="dt-track-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#d09050"/><stop offset="100%" stop-color="#a06830"/>
        </linearGradient>
        <linearGradient id="dt-flow-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#5080c0"/><stop offset="100%" stop-color="#3860a0"/>
        </linearGradient>
        <linearGradient id="dt-wander-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#999"/><stop offset="100%" stop-color="#666"/>
        </linearGradient>
        <filter id="dt-shadow" x="-5%" y="-5%" width="110%" height="120%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="2"/><feOffset dx="1" dy="2"/>
          <feComposite in2="SourceAlpha" operator="out"/>
          <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <!-- Root node -->
      <rect x="230" y="8" width="140" height="36" rx="18" fill="url(#dt-root-grad)" filter="url(#dt-shadow)"/>
      <text x="300" y="30" text-anchor="middle" font-family="'Inter',sans-serif" font-weight="700" font-size="11" fill="white">RIVAL DECISION</text>
      <text x="300" y="40" text-anchor="middle" font-family="'Space Mono',monospace" font-size="7" fill="#ffcccc">every 0.4 sec</text>
      <!-- Arrows -->
      <path d="M260,44 C220,60 140,60 100,80" fill="none" stroke="#5aa06a" stroke-width="2"/>
      <path d="M280,44 C265,65 240,70 235,80" fill="none" stroke="#d09050" stroke-width="2"/>
      <path d="M320,44 C335,65 360,70 365,80" fill="none" stroke="#5080c0" stroke-width="2"/>
      <path d="M340,44 C380,60 460,60 500,80" fill="none" stroke="#999" stroke-width="2"/>
      <polygon points="100,80 96,74 104,74" fill="#5aa06a"/>
      <polygon points="235,80 231,74 239,74" fill="#d09050"/>
      <polygon points="365,80 361,74 369,74" fill="#5080c0"/>
      <polygon points="500,80 496,74 504,74" fill="#999"/>
      <!-- Seek Food -->
      <rect x="20" y="82" width="160" height="34" rx="12" fill="url(#dt-food-grad)" filter="url(#dt-shadow)"/>
      <text x="100" y="100" text-anchor="middle" font-family="'Inter',sans-serif" font-weight="700" font-size="10" fill="white">SEEK FOOD</text>
      <text x="100" y="112" text-anchor="middle" font-family="'Space Mono',monospace" font-size="7" fill="#d0ffd0">45-75% priority</text>
      <rect x="20" y="122" width="160" height="60" rx="6" fill="#f0f8f2" stroke="#5aa06a" stroke-width="1"/>
      <text x="100" y="136" text-anchor="middle" font-size="8" fill="#333">Scans 12-tile radius.</text>
      <text x="100" y="148" text-anchor="middle" font-size="8" fill="#333">Moves toward nearest</text>
      <text x="100" y="160" text-anchor="middle" font-size="8" fill="#333">substrate. Prefers high</text>
      <text x="100" y="172" text-anchor="middle" font-size="8" fill="#333">energy (O2 > NO3 > ...).</text>
      <!-- Track Player -->
      <rect x="190" y="82" width="130" height="34" rx="12" fill="url(#dt-track-grad)" filter="url(#dt-shadow)"/>
      <text x="255" y="100" text-anchor="middle" font-family="'Inter',sans-serif" font-weight="700" font-size="10" fill="white">TRACK ARKE</text>
      <text x="255" y="112" text-anchor="middle" font-family="'Space Mono',monospace" font-size="7" fill="#ffeedd">15% priority</text>
      <rect x="190" y="122" width="130" height="60" rx="6" fill="#faf5f0" stroke="#d09050" stroke-width="1"/>
      <text x="255" y="136" text-anchor="middle" font-size="8" fill="#333">Detects ARKE within</text>
      <text x="255" y="148" text-anchor="middle" font-size="8" fill="#333">10 tiles. Moves to</text>
      <text x="255" y="160" text-anchor="middle" font-size="8" fill="#333">player's area to</text>
      <text x="255" y="172" text-anchor="middle" font-size="8" fill="#333">compete for food.</text>
      <!-- Ride Flow -->
      <rect x="330" y="82" width="130" height="34" rx="12" fill="url(#dt-flow-grad)" filter="url(#dt-shadow)"/>
      <text x="395" y="100" text-anchor="middle" font-family="'Inter',sans-serif" font-weight="700" font-size="10" fill="white">RIDE FLOW</text>
      <text x="395" y="112" text-anchor="middle" font-family="'Space Mono',monospace" font-size="7" fill="#d0e0ff">40% on flow tiles</text>
      <rect x="330" y="122" width="130" height="60" rx="6" fill="#f0f2fa" stroke="#5080c0" stroke-width="1"/>
      <text x="395" y="136" text-anchor="middle" font-size="8" fill="#333">On flow tiles, rides</text>
      <text x="395" y="148" text-anchor="middle" font-size="8" fill="#333">current at 2x speed.</text>
      <text x="395" y="160" text-anchor="middle" font-size="8" fill="#333">Reaches food-rich</text>
      <text x="395" y="172" text-anchor="middle" font-size="8" fill="#333">areas downstream.</text>
      <!-- Wander -->
      <rect x="470" y="82" width="110" height="34" rx="12" fill="url(#dt-wander-grad)" filter="url(#dt-shadow)"/>
      <text x="525" y="100" text-anchor="middle" font-family="'Inter',sans-serif" font-weight="700" font-size="10" fill="white">WANDER</text>
      <text x="525" y="112" text-anchor="middle" font-family="'Space Mono',monospace" font-size="7" fill="#ddd">fallback</text>
      <rect x="470" y="122" width="110" height="60" rx="6" fill="#f4f4f4" stroke="#999" stroke-width="1"/>
      <text x="525" y="136" text-anchor="middle" font-size="8" fill="#333">Random walkable</text>
      <text x="525" y="148" text-anchor="middle" font-size="8" fill="#333">tile. Prefers current</text>
      <text x="525" y="160" text-anchor="middle" font-size="8" fill="#333">direction (momentum)</text>
      <text x="525" y="172" text-anchor="middle" font-size="8" fill="#333">for patrol behavior.</text>
      <!-- Legend -->
      <rect x="20" y="200" width="560" height="30" rx="6" fill="#f8f4ea" stroke="#ccc" stroke-width="1"/>
      <text x="30" y="220" font-family="'Space Mono',monospace" font-size="7" fill="#888">PRIORITY ORDER:</text>
      <circle cx="140" cy="215" r="6" fill="url(#dt-food-grad)"/>
      <text x="155" y="219" font-size="8" fill="#333">Highest (food)</text>
      <text x="220" y="219" font-size="8" fill="#888">&#8594;</text>
      <circle cx="250" cy="215" r="6" fill="url(#dt-flow-grad)"/>
      <text x="265" y="219" font-size="8" fill="#333">Flow (if on tile)</text>
      <text x="350" y="219" font-size="8" fill="#888">&#8594;</text>
      <circle cx="380" cy="215" r="6" fill="url(#dt-track-grad)"/>
      <text x="395" y="219" font-size="8" fill="#333">Track player</text>
      <text x="470" y="219" font-size="8" fill="#888">&#8594;</text>
      <circle cx="500" cy="215" r="6" fill="url(#dt-wander-grad)"/>
      <text x="515" y="219" font-size="8" fill="#333">Wander (fallback)</text>
    </svg>
  </div>

  <h3 style="margin-top:12px;">1. Seek Food (45-75% Priority)</h3>
  <p style="font-size:9.5pt; line-height:1.5;">
    The rival calculates <strong>Manhattan distance</strong> to every substrate within
    <strong>12 tiles</strong>. It moves one tile toward the nearest substrate. If multiple
    substrates are equidistant, it prefers the one with the highest energy value
    (<strong>O<sub>2</sub> &gt; NO<sub>3</sub><sup>-</sup> &gt; Mn &gt; Fe &gt;
    SO<sub>4</sub><sup>2-</sup> &gt; CH<sub>4</sub></strong>). The seek probability
    increases when the rival hasn't eaten recently.
  </p>

  <h3>2. Track Player (15% Priority)</h3>
  <p style="font-size:9.5pt; line-height:1.5;">
    If ARKE is within <strong>10 tiles</strong>, the rival has a <strong>15% chance</strong>
    per decision cycle to move toward the player's position. They move to
    <em>your area</em> because you're likely near food, creating
    <strong>competition zones</strong>.
  </p>

  <h3>3. Ride Flow (40% on Flow Tiles)</h3>
  <p style="font-size:9.5pt; line-height:1.5;">
    On flow tiles, rivals have a <strong>40% chance</strong> to enter
    planktonic mode at <strong>2x speed</strong>. This lets
    them quickly reach substrate-rich areas downstream.
  </p>

  <h3>4. Wander (Fallback)</h3>
  <p style="font-size:9.5pt; line-height:1.5;">
    If no food detected, no player nearby, and not on flow, the rival picks a random
    walkable adjacent tile. They <strong>prefer their current
    direction</strong> (momentum), creating patrol-like behavior.
  </p>

  <p class="page-number left">6</p>
</div>

<!-- Characters page 4: Key Facts About Rivals, Biofilm Colonies -->
<div class="page" id="characters4" style="page-break-after: always;">
  <h2>Key Facts About Rivals</h2>

  <div class="info-box warning" style="margin-top:8px;">
    <div class="info-box-title" style="color:#cc3333;">CRITICAL RIVAL INFORMATION</div>
    <table style="font-size:9.5pt;">
      <tr>
        <td style="width:30%; font-weight:700; color:#8a2a2a;">Invulnerable</td>
        <td>Rivals are <strong>INVULNERABLE</strong>&mdash;you cannot kill, damage, or block them.
            There is no combat mechanic. Your only strategy is to outmaneuver them.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#8a2a2a;">Instant Consumption</td>
        <td>Rivals consume substrates <strong>instantly on contact</strong>, just like you.
            If a rival reaches a substrate first, it's gone permanently.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#8a2a2a;">Equal Speed</td>
        <td>Rivals move at <strong>2.5 tiles/sec</strong>&mdash;the same speed as you in
            normal (benthic) mode. Your only speed advantage is planktonic mode (SHIFT).</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#8a2a2a;">Toxic Immunity</td>
        <td>Rivals do <strong>NOT</strong> take damage from toxic zones. Different species
            have different chemical tolerances.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#8a2a2a;">Scaling Count</td>
        <td>Each level has <strong>0-5 rivals</strong>. Level 1: 0 rivals. Level 10: 5 rivals.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#8a2a2a;">Food Competition</td>
        <td>With <strong>5 rivals</strong>, you get roughly <strong>1/6</strong> of all food.</td>
      </tr>
    </table>
  </div>

  <h2>Biofilm Colonies</h2>

  <!-- Colony Character Card -->
  <div class="char-card">
    <div class="char-sprite" style="width:120px; height:120px; background:#0a1a10; border-radius:4px; display:flex; align-items:center; justify-content:center;">
      {colony_portrait}
    </div>
    <div class="char-info">
      <div class="char-name" style="color:#3a7a5a;">BIOFILM COLONY</div>
      <div class="char-desc">
        When ARKE divides, a permanent biofilm colony is placed on the map. Colonies are clusters
        of daughter cells embedded in a protective extracellular matrix&mdash;the biofilm. They are
        stationary sentinels that <strong>passively consume</strong> nearby substrates. Each colony
        placed earns <strong>+100 points</strong> and counts toward the level goal.
      </div>
      <div class="char-stats">
        TYPE: Stationary Ally &bull; SIZE: 24&times;24px (12&times;12 sprite, 2&times; scaled) &bull;
        FEED RANGE: 1.5 tiles &bull; PERMANENT &bull; INDESTRUCTIBLE
      </div>
    </div>
  </div>

  <!-- Colony Mechanics -->
  <div class="info-box tip" style="margin-top:10px;">
    <div class="info-box-title" style="color:#3a8a4a;">COLONY MECHANICS IN DETAIL</div>
    <table style="font-size:9.5pt;">
      <tr>
        <td style="width:30%; font-weight:700; color:#3a7a5a;">Placement</td>
        <td>Colonies are placed <strong>automatically</strong> on the best adjacent pore tile when
            you press SPACE at GR=100. The game selects the tile furthest from grain walls.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#3a7a5a;">Feeding Radius</td>
        <td>Each colony has a passive feeding radius of <strong>1.5 tiles</strong>.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#3a7a5a;">Consumption Rate</td>
        <td>Colonies consume substrates with <strong>2% probability per frame</strong> within range.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#3a7a5a;">Permanence</td>
        <td>Colonies are <strong>permanent and indestructible</strong>. Rivals cannot destroy them.</td>
      </tr>
      <tr>
        <td style="font-weight:700; color:#3a7a5a;">Strategic Note</td>
        <td>Colony feeding removes food from the map, which also <strong>reduces rival food</strong>.
            Place colonies strategically along rival patrol routes to starve them out.</td>
      </tr>
    </table>
  </div>

  <p class="page-number right">7</p>
</div>
'''
    return html


def gen_07_worlds():
    """Generate updated 07_worlds.html with tile-grid game screenshots."""

    w_soil = world_grid(0, gw=20, gh=15, ts=10, seed=42, por=0.65,
                        subs=["O2","NO3","CH4"])
    w_deep = world_grid(1, gw=20, gh=15, ts=10, seed=55, por=0.50,
                        maze=True, subs=["NO3","Fe","CH4"], rivals=2)
    w_methane = world_grid(2, gw=20, gh=15, ts=10, seed=77, por=0.58,
                           toxic=True, vents=True, subs=["SO4","CH4","Fe"], rivals=2)
    w_perma = world_grid(3, gw=20, gh=12, ts=10, seed=88,
                         layered=True, toxic=True, subs=["O2","NO3","CH4"], rivals=3)
    w_hydro = world_grid(4, gw=20, gh=15, ts=10, seed=99, por=0.50,
                         toxic=True, vents=True, subs=["SO4","Fe","Mn","CH4"], rivals=4)

    html = f'''<!-- Section 07: Worlds & Environments -->
<div class="page" id="worlds" style="page-break-after:always;">
  <h1 class="section-number">SECTION 6</h1>
  <h1 class="section-title">Worlds & Environments</h1>

  <p>
    ARKE's journey spans <strong>5 unique environments</strong> across <strong>10 levels</strong>,
    each inspired by real subsurface ecosystems studied by the CompLaB3D research team.
    All screenshots below use the actual game tile colors and procedural generation style.
  </p>

  <!-- CHAPTER 1: THE SOIL FRONTIER -->
  <div style="background:white; border:2px solid #7a5a2a; border-radius:8px; padding:14px; margin:12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div style="display:flex; gap:16px; align-items:flex-start;">
      <div style="flex-shrink:0;">
        {w_soil}
      </div>
      <div style="flex:1;">
        <div style="font-family:'Press Start 2P',monospace; font-size:9pt; color:#7a5a2a; margin-bottom:4px;">
          CHAPTER 1: THE SOIL FRONTIER
        </div>
        <div style="font-size:9pt; color:#888; margin-bottom:6px;">Levels 1-2 &bull; Environment 0</div>
        <p style="font-size:9.5pt; line-height:1.45;">
          Shallow soil with wide-open pore spaces between rounded rock grains. Water flows gently,
          carrying abundant nutrients including <strong>oxygen</strong>. The safest environment&mdash;
          perfect for learning the basics of movement, feeding, and division.
        </p>
        <div style="font-size:8.5pt; color:#555; margin-top:5px; line-height:1.5;">
          <strong>Porosity:</strong> 65-70% (very open)<br>
          <strong>Substrates:</strong> O<sub>2</sub>, NO<sub>3</sub>, CH<sub>4</sub><br>
          <strong>Hazards:</strong> None (Lv1) / 1 rival (Lv2)<br>
          <strong>Flow Speed:</strong> 0.3&times; (gentle)
        </div>
      </div>
    </div>
  </div>

  <!-- CHAPTER 2: THE DEEP SEDIMENT -->
  <div style="background:white; border:2px solid #4a3a2a; border-radius:8px; padding:14px; margin:12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div style="display:flex; gap:16px; align-items:flex-start;">
      <div style="flex-shrink:0;">
        {w_deep}
      </div>
      <div style="flex:1;">
        <div style="font-family:'Press Start 2P',monospace; font-size:9pt; color:#4a3a2a; margin-bottom:4px;">
          CHAPTER 2: THE DEEP SEDIMENT
        </div>
        <div style="font-size:9pt; color:#888; margin-bottom:6px;">Levels 3-4 &bull; Environment 1</div>
        <p style="font-size:9.5pt; line-height:1.45;">
          Deep beneath the ocean floor. No oxygen here! Narrow, maze-like corridors carved through
          compacted sediment. Flow is sluggish and food is scarce. <strong>Navigation skill</strong>
          becomes critical as dead ends can trap you.
        </p>
        <div style="font-size:8.5pt; color:#555; margin-top:5px; line-height:1.5;">
          <strong>Porosity:</strong> 45-50% (tight, maze-like)<br>
          <strong>Substrates:</strong> NO<sub>3</sub>, Fe(III), Mn(IV), CH<sub>4</sub> (no O<sub>2</sub>!)<br>
          <strong>Hazards:</strong> 2-3 rivals, slow flow, dead ends<br>
          <strong>Flow Speed:</strong> 0.4&times; (sluggish)
        </div>
      </div>
    </div>
  </div>

  <!-- CHAPTER 3: THE METHANE SEEPS -->
  <div style="background:white; border:2px solid #6a3060; border-radius:8px; padding:14px; margin:12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div style="display:flex; gap:16px; align-items:flex-start;">
      <div style="flex-shrink:0;">
        {w_methane}
      </div>
      <div style="flex:1;">
        <div style="font-family:'Press Start 2P',monospace; font-size:9pt; color:#b040a0; margin-bottom:4px;">
          CHAPTER 3: THE METHANE SEEPS
        </div>
        <div style="font-size:9pt; color:#888; margin-bottom:6px;">Levels 5-6 &bull; Environment 2</div>
        <p style="font-size:9.5pt; line-height:1.45;">
          Methane bubbles up through vertical vent channels. <strong>Toxic H<sub>2</sub>S zones</strong>
          appear for the first time! Purple-tinted world with abundant CH<sub>4</sub> but
          dangerous terrain.
        </p>
        <div style="font-size:8.5pt; color:#555; margin-top:5px; line-height:1.5;">
          <strong>Porosity:</strong> 55-60% (moderate)<br>
          <strong>Substrates:</strong> SO<sub>4</sub>, CH<sub>4</sub>, Fe(III)<br>
          <strong>Hazards:</strong> 15-20% toxic zones, 2-3 rivals<br>
          <strong>Flow Speed:</strong> 0.5&times; (moderate)
        </div>
      </div>
    </div>
  </div>

  <p class="page-number left">11</p>
</div>

<!-- Worlds page 2 -->
<div class="page" id="worlds2" style="page-break-after:always;">

  <!-- CHAPTER 4: THE PERMAFROST EDGE -->
  <div style="background:white; border:2px solid #5a6a7a; border-radius:8px; padding:14px; margin:12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div style="display:flex; gap:16px; align-items:flex-start;">
      <div style="flex-shrink:0;">
        {w_perma}
      </div>
      <div style="flex:1;">
        <div style="font-family:'Press Start 2P',monospace; font-size:9pt; color:#5a6a7a; margin-bottom:4px;">
          CHAPTER 4: THE PERMAFROST EDGE
        </div>
        <div style="font-size:9pt; color:#888; margin-bottom:6px;">Levels 7-8 &bull; Environment 3</div>
        <p style="font-size:9.5pt; line-height:1.45;">
          Thawing permafrost releases ancient carbon. <strong>Fast horizontal flow channels</strong>
          between ice layers demand mastery of <strong>SHIFT (flow riding)</strong>. Substrates
          race past at high speed.
        </p>
        <div style="font-size:8.5pt; color:#555; margin-top:5px; line-height:1.5;">
          <strong>Porosity:</strong> 50-55% (wide horizontal, narrow vertical)<br>
          <strong>Substrates:</strong> O<sub>2</sub> (Lv7), NO<sub>3</sub>, SO<sub>4</sub>, CH<sub>4</sub><br>
          <strong>Hazards:</strong> 10-15% toxic, 3-4 rivals, fast flow<br>
          <strong>Flow Speed:</strong> 0.8-1.0&times; (rapid)
        </div>
      </div>
    </div>
  </div>

  <!-- CHAPTER 5: THE HYDROTHERMAL REALM -->
  <div style="background:white; border:2px solid #cc3333; border-radius:8px; padding:14px; margin:12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div style="display:flex; gap:16px; align-items:flex-start;">
      <div style="flex-shrink:0;">
        {w_hydro}
      </div>
      <div style="flex:1;">
        <div style="font-family:'Press Start 2P',monospace; font-size:9pt; color:#cc3333; margin-bottom:4px;">
          CHAPTER 5: THE HYDROTHERMAL REALM
        </div>
        <div style="font-size:9pt; color:#888; margin-bottom:6px;">Levels 9-10 &bull; Environment 4</div>
        <p style="font-size:9.5pt; line-height:1.45;">
          The deepest, most extreme environment. Chaotic chamber-and-tunnel geology near
          hydrothermal vents. <strong>Maximum toxic coverage (25%)</strong>, extreme flow,
          and <strong>5 rivals</strong>. <strong>This is the final challenge.</strong>
        </p>
        <div style="font-size:8.5pt; color:#555; margin-top:5px; line-height:1.5;">
          <strong>Porosity:</strong> 40-50% (chambers + tunnels)<br>
          <strong>Substrates:</strong> SO<sub>4</sub>, Fe(III), Mn(IV), CH<sub>4</sub>, NO<sub>3</sub> (Lv10)<br>
          <strong>Hazards:</strong> 20-25% toxic, 4-5 rivals, extreme flow<br>
          <strong>Flow Speed:</strong> 1.2-1.5&times; (violent)
        </div>
      </div>
    </div>
  </div>

  <!-- Journey Overview -->
  <h2>Journey Overview</h2>
  <div style="background:white; border:2px solid #3a3a4a; border-radius:8px; padding:14px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <svg width="100%" height="90" viewBox="0 0 520 90" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="jo-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.2)"/>
        </filter>
      </defs>
      <text x="260" y="10" text-anchor="middle" font-size="6" fill="#aaa" letter-spacing="3" font-weight="bold">DIFFICULTY</text>
      <path d="M160,7 L360,7" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <polygon points="358,5 364,7 358,9" fill="#ccc"/>
      <path d="M50,45 L470,45" fill="none" stroke="#666" stroke-width="3" stroke-linecap="round"/>
      <!-- Ch1 -->
      <circle cx="50" cy="45" r="18" fill="#7a5a2a" stroke="#c4a060" stroke-width="2.5" filter="url(#jo-shadow)"/>
      <text x="50" y="49" text-anchor="middle" font-family="'Press Start 2P',monospace" font-size="8" fill="white">1</text>
      <text x="50" y="72" text-anchor="middle" font-size="7" fill="#7a5a2a" font-weight="bold">SOIL</text>
      <text x="50" y="82" text-anchor="middle" font-size="5.5" fill="#888">Lv 1-2</text>
      <!-- Ch2 -->
      <circle cx="155" cy="45" r="18" fill="#4a3a2a" stroke="#6a5a3a" stroke-width="2.5" filter="url(#jo-shadow)"/>
      <text x="155" y="49" text-anchor="middle" font-family="'Press Start 2P',monospace" font-size="8" fill="white">2</text>
      <text x="155" y="72" text-anchor="middle" font-size="7" fill="#4a3a2a" font-weight="bold">DEEP</text>
      <text x="155" y="82" text-anchor="middle" font-size="5.5" fill="#888">Lv 3-4</text>
      <!-- Ch3 -->
      <circle cx="260" cy="45" r="18" fill="#3a3040" stroke="#b040a0" stroke-width="2.5" filter="url(#jo-shadow)"/>
      <text x="260" y="49" text-anchor="middle" font-family="'Press Start 2P',monospace" font-size="8" fill="white">3</text>
      <text x="260" y="72" text-anchor="middle" font-size="7" fill="#b040a0" font-weight="bold">METHANE</text>
      <text x="260" y="82" text-anchor="middle" font-size="5.5" fill="#888">Lv 5-6</text>
      <!-- Ch4 -->
      <circle cx="365" cy="45" r="18" fill="#5a6a7a" stroke="#8a9aaa" stroke-width="2.5" filter="url(#jo-shadow)"/>
      <text x="365" y="49" text-anchor="middle" font-family="'Press Start 2P',monospace" font-size="8" fill="white">4</text>
      <text x="365" y="72" text-anchor="middle" font-size="7" fill="#5a6a7a" font-weight="bold">PERMAFROST</text>
      <text x="365" y="82" text-anchor="middle" font-size="5.5" fill="#888">Lv 7-8</text>
      <!-- Ch5 -->
      <circle cx="470" cy="45" r="18" fill="#2a2a3a" stroke="#cc3333" stroke-width="2.5" filter="url(#jo-shadow)"/>
      <text x="470" y="49" text-anchor="middle" font-family="'Press Start 2P',monospace" font-size="8" fill="#ff4f4f">5</text>
      <text x="470" y="72" text-anchor="middle" font-size="7" fill="#cc3333" font-weight="bold">HYDRO</text>
      <text x="470" y="82" text-anchor="middle" font-size="5.5" fill="#888">Lv 9-10</text>
    </svg>
  </div>

  <div class="info-box" style="margin-top:10px;">
    <div class="info-box-title">ENVIRONMENT SUMMARY</div>
    <p style="font-size:9.5pt; line-height:1.5;">
      Each world is <strong>procedurally generated</strong>, meaning no two playthroughs are identical.
      Porosity determines open space; flow speed affects substrate movement and SHIFT effectiveness.
      Toxic coverage increases from 0% in Soil to 25% in Hydrothermal.
    </p>
  </div>

  <p class="page-number right">12</p>
</div>
'''
    return html


def gen_level_map(env, seed, subs, rivals, **kw):
    """Generate a level preview tile grid."""
    return world_grid(env, gw=30, gh=10, ts=10, seed=seed,
                      subs=subs, rivals=rivals, **kw)


def gen_08_levels():
    """Generate updated 08_levels.html with tile-grid level maps."""

    lv1 = gen_level_map(0, 101, ["O2","NO3","CH4"], 0, por=0.70)
    lv2 = gen_level_map(0, 102, ["O2","NO3","CH4"], 1, por=0.65)
    lv3 = gen_level_map(1, 103, ["NO3","Fe","CH4"], 2, por=0.50, maze=True)
    lv4 = gen_level_map(1, 104, ["NO3","Mn","Fe","CH4"], 3, por=0.45, maze=True)
    lv5 = gen_level_map(2, 105, ["SO4","CH4"], 2, por=0.58, toxic=True, vents=True)
    lv6 = gen_level_map(2, 106, ["SO4","CH4","Fe"], 3, por=0.55, toxic=True, vents=True)
    lv7 = gen_level_map(3, 107, ["O2","NO3","CH4"], 3, layered=True, toxic=True)
    lv8 = gen_level_map(3, 108, ["NO3","SO4","CH4"], 4, layered=True, toxic=True)
    lv9 = gen_level_map(4, 109, ["SO4","Fe","Mn","CH4"], 4, por=0.50, toxic=True, vents=True)
    lv10 = gen_level_map(4, 110, ["SO4","Fe","Mn","CH4","NO3"], 5, por=0.45, toxic=True, vents=True)

    def lv_card(name, chapter, svg, stats, strategy, name_color="#7a5a2a", extra_style=""):
        stat_html = ""
        for s in stats:
            lbl, val = s["label"], s["value"]
            style = f' style="color:{s["color"]}"' if "color" in s else ""
            bg_style = f' style="background:{s["bg"]}"' if "bg" in s else ""
            stat_html += f'      <div class="stat"{bg_style}><span class="stat-label">{lbl}</span><span class="stat-value"{style}>{val}</span></div>\n'

        return f'''  <div class="level-card" {extra_style}>
    <div class="level-header">
      <div class="level-name" style="color:{name_color};">{name}</div>
      <div class="level-chapter">{chapter}</div>
    </div>
    <div class="level-map">
      {svg}
    </div>
    <div class="level-stats">
{stat_html}    </div>
    <div class="level-strategy">
      {strategy}
    </div>
  </div>'''

    html = f'''<!-- Section 08: Level-by-Level Guide -->
<div class="page" id="levels">
  <h1 class="section-number">SECTION 7</h1>
  <h1 class="section-title">Level Guide</h1>

{lv_card("LEVEL 1: FIRST BREATH", "Chapter 1 &mdash; The Soil Frontier", lv1,
         [{"label":"GOAL","value":"3 colonies"},{"label":"MAP","value":"30&times;20"},
          {"label":"RIVALS","value":"0","color":"#3a8a4a"},{"label":"TOXIC","value":"None","color":"#3a8a4a"}],
         '<strong>Strategy:</strong> Pure tutorial level. No enemies, no hazards. Wide open pore space with 70% porosity. O<sub>2</sub>, NO<sub>3</sub>, and CH<sub>4</sub> available. Learn the basics: WASD/Arrow movement, eating on contact, pressing SPACE to divide.')}

{lv_card("LEVEL 2: ROOTS OF LIFE", "Chapter 1 &mdash; The Soil Frontier", lv2,
         [{"label":"GOAL","value":"5 colonies"},{"label":"MAP","value":"35&times;22"},
          {"label":"RIVALS","value":"1","color":"#cc3333"},{"label":"TOXIC","value":"None","color":"#3a8a4a"}],
         '<strong>Strategy:</strong> Your first rival appears! Move quickly to eat before it does. Try using SHIFT on flow tiles to outpace the rival. <strong>Race to food clusters near the INLET.</strong>')}

  <p class="page-number left">13</p>
</div>

<!-- Levels page 2 -->
<div class="page" id="levels2">

{lv_card("LEVEL 3: INTO THE DEPTHS", "Chapter 2 &mdash; The Deep Sediment", lv3,
         [{"label":"GOAL","value":"4 colonies"},{"label":"MAP","value":"35&times;25"},
          {"label":"RIVALS","value":"2","color":"#cc3333"},{"label":"TOXIC","value":"None","color":"#3a8a4a"}],
         '<strong>Strategy:</strong> <span style="color:#cc3333;">No oxygen available!</span> Tight maze corridors with 50% porosity. NO<sub>3</sub> becomes your best friend: +15 HP and +18 GR. Navigate carefully &mdash; dead ends waste precious time.',
         name_color="#4a3a2a")}

{lv_card("LEVEL 4: THE HUNGRY DARK", "Chapter 2 &mdash; The Deep Sediment", lv4,
         [{"label":"GOAL","value":"6 colonies"},{"label":"MAP","value":"40&times;28"},
          {"label":"RIVALS","value":"3","color":"#cc3333"},{"label":"FLOW","value":"0.25&times; (crawl)"}],
         '<strong>Strategy:</strong> Hardest early-game level. Minimum food density (2). Tightest porosity (45%). Three rivals. Manganese Mn(IV) appears (purple, +12 GR). Every substrate counts.',
         name_color="#4a3a2a")}

{lv_card("LEVEL 5: THE METHANE VENTS", "Chapter 3 &mdash; The Methane Seeps", lv5,
         [{"label":"GOAL","value":"5 colonies"},{"label":"MAP","value":"35&times;22"},
          {"label":"RIVALS","value":"2","color":"#cc3333"},{"label":"TOXIC","value":"15%","color":"#c060c0"}],
         '<strong>Strategy:</strong> <span style="color:#c060c0;">TOXIC ZONES APPEAR!</span> Purple H<sub>2</sub>S tiles deal &minus;20 HP/sec. Only SO<sub>4</sub> and CH<sub>4</sub> available. CH<sub>4</sub> is your primary growth source (+25 GR).',
         name_color="#b040a0")}

  <p class="page-number right">14</p>
</div>

<!-- Levels page 3 -->
<div class="page" id="levels3">

{lv_card("LEVEL 6: VENT GUARDIANS", "Chapter 3 &mdash; The Methane Seeps", lv6,
         [{"label":"GOAL","value":"8 colonies"},{"label":"MAP","value":"40&times;25"},
          {"label":"RIVALS","value":"3","color":"#cc3333"},{"label":"TOXIC","value":"20%","color":"#c060c0"}],
         '<strong>Strategy:</strong> Double the colonies of Level 5! Fe(III) now available. Toxic zones cover 20% of tiles. Balance toxin avoidance with food access.',
         name_color="#b040a0")}

{lv_card("LEVEL 7: THAWING GROUNDS", "Chapter 4 &mdash; The Permafrost Edge", lv7,
         [{"label":"GOAL","value":"6 colonies"},{"label":"MAP","value":"40&times;25"},
          {"label":"RIVALS","value":"3","color":"#cc3333"},{"label":"FLOW","value":"0.8&times; (fast!)","color":"#4fa4ff"}],
         '<strong>Strategy:</strong> <span style="color:#4fa4ff;">OXYGEN RETURNS!</span> Fast flow (0.8&times;) makes SHIFT essential. Substrates race past at high speed. O<sub>2</sub> provides +20 HP. Abundant food (density 6)!',
         name_color="#5a6a7a")}

  <p class="page-number left">15</p>
</div>

<!-- Levels page 4 -->
<div class="page" id="levels4">

{lv_card("LEVEL 8: THE GREAT THAW", "Chapter 4 &mdash; The Permafrost Edge", lv8,
         [{"label":"GOAL","value":"8 colonies"},{"label":"MAP","value":"45&times;28"},
          {"label":"RIVALS","value":"4","color":"#cc3333"},{"label":"FLOW","value":"1.0&times; (very fast!)","color":"#cc3333"}],
         '<strong>Strategy:</strong> No oxygen again. Fastest flow yet (1.0&times;). Largest map so far (45&times;28). FOUR rivals! Must constantly ride flow with SHIFT.',
         name_color="#5a6a7a")}

{lv_card("LEVEL 9: THE ABYSS", "Chapter 5 &mdash; The Hydrothermal Realm", lv9,
         [{"label":"GOAL","value":"8 colonies"},{"label":"MAP","value":"45&times;25"},
          {"label":"RIVALS","value":"4","color":"#cc3333"},{"label":"TOXIC","value":"20%","color":"#c07030"}],
         '<strong>Strategy:</strong> Deep-sea hydrothermal vents. Full redox ladder minus O<sub>2</sub>. Extreme flow (1.2&times;). Chamber-based topology. Requires mastery of all mechanics.',
         name_color="#cc3333")}

  <p class="page-number right">16</p>
</div>

<!-- Levels page 5 -->
<div class="page" id="levels5">

{lv_card("LEVEL 10: EARTH'S LAST STAND", "FINAL LEVEL", lv10,
         [{"label":"GOAL","value":"12 colonies!","color":"#cc3333","bg":"#fff0f0"},
          {"label":"MAP","value":"50&times;30","bg":"#fff0f0"},
          {"label":"RIVALS","value":"5 (MAX)","color":"#cc3333","bg":"#fff0f0"},
          {"label":"TOXIC","value":"25% (MAX)","color":"#cc3333","bg":"#fff0f0"}],
         '<strong style="color:#cc3333;">THE ULTIMATE TEST.</strong> Everything at maximum. Largest map (50&times;30). Most colonies (12). Fastest flow (1.5&times;). Most toxic (1 in 4 tiles!). Most rivals (5). <strong>Victory triggers the end screen showing total climate impact. You saved the planet!</strong>',
         name_color="#cc3333", extra_style='style="border-color:#cc3333; border-width:3px;"')}

  <div class="info-box warning" style="margin-top: 10px;">
    <div class="info-box-title" style="color:#c05030;">GAME OVER</div>
    <p style="font-size:10pt;">
      If your Health reaches 0, you die. Press <strong>ENTER</strong> after 2 seconds
      to retry the same level. Your score resets, but you keep your global progress.
    </p>
  </div>

  <p class="page-number left">17</p>
</div>
'''
    return html


# ── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'manual_sections')

    print("Generating 03_characters.html...")
    with open(os.path.join(base, '03_characters.html'), 'w') as f:
        f.write(gen_03_characters())
    print("  Done.")

    print("Generating 07_worlds.html...")
    with open(os.path.join(base, '07_worlds.html'), 'w') as f:
        f.write(gen_07_worlds())
    print("  Done.")

    print("Generating 08_levels.html...")
    with open(os.path.join(base, '08_levels.html'), 'w') as f:
        f.write(gen_08_levels())
    print("  Done.")

    print("\nAll manual sections updated with pixel-perfect game art!")
