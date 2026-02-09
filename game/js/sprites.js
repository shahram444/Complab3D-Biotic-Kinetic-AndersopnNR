/**
 * PORELIFE: Microbe Survivor
 * Pixel Art Sprite Definitions
 * All sprites defined as 2D arrays with palette character codes
 */

(function() {
    // Sprite palette - single char to hex color
    const SP = {
        '.': null,              // transparent
        'k': '#000000',         // black (outline)
        'w': '#ffffff',         // white
        'W': '#cccccc',         // light gray
        'a': '#888888',         // gray
        'A': '#444444',         // dark gray

        // Paler (microbe) colors
        'g': '#5fcf5f',         // body green
        'G': '#8bef6b',         // highlight green
        'D': '#2f8f2f',         // dark green
        'd': '#1a6f1a',         // darker green
        'L': '#afffaf',         // glow green

        // Brown (grains)
        'b': '#8b6914',         // brown
        'B': '#c4a35a',         // light brown
        'n': '#5a3921',         // dark brown
        'N': '#dcc07a',         // tan

        // Blue (water/pore)
        'u': '#1a3c6e',         // blue
        'U': '#3c6eaa',         // light blue
        'c': '#5ab5c4',         // cyan
        'C': '#8ad0e0',         // light cyan

        // Yellow/Gold (substrate)
        'y': '#ffd700',         // gold
        'Y': '#ffec80',         // light gold
        'o': '#cc9900',         // dark gold

        // Red (danger)
        'r': '#ef4444',         // red
        'R': '#ff8888',         // light red

        // Purple (toxic)
        'p': '#8b3a8b',         // purple
        'P': '#cf5fcf',         // light purple
        'q': '#5a1a5a',         // dark purple

        // Special
        'e': '#1a1a2e',         // eye pupil
        'i': '#5f9fef',         // info blue
        't': '#2a5a2a',         // biofilm green
        'T': '#3a7a3a',         // biofilm light
        'h': '#ff6644',         // hurt orange
        's': '#ffff5f',         // ready glow
    };

    function parseSprite(lines) {
        return lines.map(row => row.split('').map(ch => SP[ch] || null));
    }

    // ─── PALER SPRITES (16x16) ──────────────────────────────

    const PALER_DOWN = parseSprite([
        '......kkkk......',
        '.....kGGGGk.....',
        '....kGGggGGk....',
        '...kGgggggGGk...',
        '...kGgwkgwkGk...',
        '...kGggggggGk...',
        '..kGGgggggGGGk..',
        '..kGGGggggGGGk..',
        '..kDGGggGGGGDk..',
        '...kDGGGGGGDk...',
        '...kDdGGGGdDk...',
        '....kdDGGDdk....',
        '.....kddddk.....',
        '......kkkk......',
        '................',
        '................'
    ]);

    const PALER_UP = parseSprite([
        '......kkkk......',
        '.....kDDDDk.....',
        '....kDDggDDk....',
        '...kDgggggDDk...',
        '...kDggggggDk...',
        '...kGggggggGk...',
        '..kGGgggggGGGk..',
        '..kGGGggggGGGk..',
        '..kGGGggGGGGGk..',
        '...kGGGGGGGGk...',
        '...kGgGGGGgGk...',
        '....kgGGGGgk....',
        '.....kggggk.....',
        '......kkkk......',
        '................',
        '................'
    ]);

    const PALER_LEFT = parseSprite([
        '................',
        '.....kkkk.......',
        '....kDDDGk......',
        '...kDgggGGk.....',
        '..kkgwkggGGk....',
        '..kDggggGGGk....',
        '.kDDgggggGGGk...',
        '.kDGGggggGGGk...',
        '.kDGGGgggGGk....',
        '..kDGGGGGGGk....',
        '..kDdGGGGGk.....',
        '...kdDGGDk......',
        '....kdddk.......',
        '.....kkk........',
        '................',
        '................'
    ]);

    const PALER_RIGHT = parseSprite([
        '................',
        '.......kkkk.....',
        '......kGDDDk....',
        '.....kGGgggDk...',
        '....kGGggkwgkk..',
        '....kGGGggggDk..',
        '...kGGGgggggDDk.',
        '...kGGGggggGDk..',
        '....kGGgggGGDk..',
        '....kGGGGGGDk...',
        '.....kGGGGGdDk..',
        '......kDGGDdk...',
        '.......kdddk....',
        '........kkk.....',
        '................',
        '................'
    ]);

    // Paler eating animation (mouth open)
    const PALER_EAT = parseSprite([
        '......kkkk......',
        '.....kGGGGk.....',
        '....kGGggGGk....',
        '...kGgggggGGk...',
        '...kGgwkgwkGk...',
        '...kGggkkkgGk...',
        '..kGGgkyykkGGk..',
        '..kGGGkkkgGGGk..',
        '..kDGGggGGGGDk..',
        '...kDGGGGGGDk...',
        '...kDdGGGGdDk...',
        '....kdDGGDdk....',
        '.....kddddk.....',
        '......kkkk......',
        '................',
        '................'
    ]);

    // Paler ready to divide (glowing)
    const PALER_GLOW = parseSprite([
        '....sskkkkss....',
        '...skGGGGGGks...',
        '..skGGLLLGGGks..',
        '..kGLggggLGGk...',
        '..kGLwkgwkLGk...',
        '..kGLgggggLGk...',
        '.kGGLgggggLGGk..',
        '.kGGGLgggLGGGk..',
        '.kDGGLggLGGGDk..',
        '..kDGGLLGGGDk...',
        '..kDdGGGGGdDk...',
        '...kdDGGGDdk....',
        '...skkddddkks...',
        '....sskkkkkss...',
        '................',
        '................'
    ]);

    // Paler hurt
    const PALER_HURT = parseSprite([
        '......kkkk......',
        '.....khhhhhk....',
        '....khhrrhhhk...',
        '...khrrrrrhhk...',
        '...khrkkrkkhk...',
        '...khrrrrrrhk...',
        '..khhrrrrrhhk...',
        '..khhhrrrrhhk...',
        '..khhhrrhhhhhk..',
        '...khhhhhhhhk...',
        '...khhhhhhhhk...',
        '....khhhhhk.....',
        '.....khhhk......',
        '......kkkk......',
        '................',
        '................'
    ]);

    // Paler death frames
    const PALER_DIE1 = parseSprite([
        '................',
        '......kkkk......',
        '.....kaaagk.....',
        '....kaagggak....',
        '...kakkkkkak....',
        '...kaggggggak...',
        '..kaagggggaak...',
        '..kaaagggaaak...',
        '...kaaaaaaaak...',
        '....kaaaaaak....',
        '.....kaaaak.....',
        '......kkkk......',
        '................',
        '................',
        '................',
        '................'
    ]);

    const PALER_DIE2 = parseSprite([
        '................',
        '................',
        '.......kkk......',
        '......kaaak.....',
        '.....kaAAAak....',
        '.....kAAAAAk....',
        '.....kaAAAak....',
        '......kaaak.....',
        '.......kkk......',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................'
    ]);

    // ─── SUBSTRATE SPRITES (8x8) ────────────────────────────

    const DOC_PARTICLE = [
        parseSprite(['.kkkk...','.kyyok..','kyyYYyok','kyYYYyok','koyyYyok','koyyyyok','.koooyk.','.kkkkk..']),
        parseSprite(['.kkkk...','.koyyok.','koyyYyok','kyYYYYok','kyYYyyok','koyyyyok','.koooyk.','.kkkkk..'])
    ];

    const NUTRIENT_PARTICLE = [
        parseSprite(['.kkkkk..','.kccUck.','kcCCCck.','kCCCCck.','kcCCCck.','.kccuck.','..kuuck.','...kkk..']),
        parseSprite(['..kkkk..','.kccUck.','kcCCCck.','kCCCCCk.','kcCCCck.','.kcccuk.','.kuuuk..','..kkkk..'])
    ];

    // ─── COLONY CELL (16x16) ────────────────────────────────

    const COLONY_CELL = parseSprite([
        '................',
        '.....kkkkk......',
        '....kTTTTTk.....',
        '...kTTtttTTk....',
        '..kTTttttTTk....',
        '..kTtttttTTk....',
        '..kTtttttTTk....',
        '..kTTttttTTk....',
        '..kTTtttTTk.....',
        '...kTTTTTk......',
        '....kkkkk.......',
        '................',
        '................',
        '................',
        '................',
        '................'
    ]);

    const COLONY_GLOW = parseSprite([
        '....sssssss.....',
        '...skTTTTTks....',
        '..skTTtttTTks...',
        '.skTTtLLtTTks...',
        '.kTTtLLLtTTk....',
        '.kTtLLLLtTTk....',
        '.kTtLLLtTTk.....',
        '.kTTtLLtTTk.....',
        '..kTTtttTTk.....',
        '...kTTTTTk......',
        '....kkkkk.......',
        '................',
        '................',
        '................',
        '................',
        '................'
    ]);

    // ─── FLOW ARROW (8x8) ───────────────────────────────────

    const FLOW_RIGHT = parseSprite([
        '........','...k....','...kU...','..kUUU..','..kUUU..','...kU...','...k....','........'
    ]);
    const FLOW_LEFT = parseSprite([
        '........','....k...','...Uk...','..UUUk..','..UUUk..','...Uk...','....k...','........'
    ]);
    const FLOW_DOWN = parseSprite([
        '........','..kkkk..','...UU...','..UUUU..','...UU...','...kk...','........','........'
    ]);

    // ─── TOXIC BUBBLE (8x8) ─────────────────────────────────

    const TOXIC_BUBBLE = [
        parseSprite(['.kkkk...','.kPPpk..','.kPppk..','.kpppk..','..kkkk..','........','........','........']),
        parseSprite(['........','.kkkk...','.kPPpk..','.kppqk..','..kkkk..','........','........','........'])
    ];

    // ─── PARTICLE EFFECTS ───────────────────────────────────

    const SPARKLE = [
        parseSprite(['....','..y.','....','....']),
        parseSprite(['..y.','.yYy','..y.','....']),
        parseSprite(['.y.y','y.Y.','..Y.','.y.y']),
        parseSprite(['..y.','.yYy','..y.','....'])
    ];

    const DEATH_PARTICLE = [
        parseSprite(['..a.','....','....','....']),
        parseSprite(['.a..','...a','....','a...']),
        parseSprite(['a...','....','...a','..a.'])
    ];

    // ─── EXPORT ─────────────────────────────────────────────

    PL.Sprites = {
        SP,
        parseSprite,
        paler: {
            down: [PALER_DOWN],
            up: [PALER_UP],
            left: [PALER_LEFT],
            right: [PALER_RIGHT],
            eat: PALER_EAT,
            glow: PALER_GLOW,
            hurt: PALER_HURT,
            die: [PALER_DIE1, PALER_DIE2]
        },
        doc: DOC_PARTICLE,
        nutrient: NUTRIENT_PARTICLE,
        colony: COLONY_CELL,
        colonyGlow: COLONY_GLOW,
        flowRight: FLOW_RIGHT,
        flowLeft: FLOW_LEFT,
        flowDown: FLOW_DOWN,
        toxicBubble: TOXIC_BUBBLE,
        sparkle: SPARKLE,
        deathParticle: DEATH_PARTICLE
    };
})();
