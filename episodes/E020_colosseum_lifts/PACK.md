# E020 Colosseum lifts: production pack

Topic: Colosseum hypogeum animal lifts (Rome, Flavian amphitheatre, late 1st c. AD onward)
Structure: B. MODERN REFRAME, with the screen overlay (Gladiator, 2000; DIRECT; stamp REAL)
Narration: DAN.mp3 (ElevenLabs, 53.1 s), matches the script
Poster card: NOT rendered. The user adds the NOW SHOWING card (now_showing_card_transparent.png) in their own edit, 0.2 to 2.8 s, top of frame. Keep the top band (y 100 to 450) free of key action in beats 1 and 2.

## PERIOD SPEC

ITEM 1: Colosseum hypogeum (Rome, Flavian amphitheatre)  [NEW BM-P022]
USED BY: beats 5 to 13 (environment)
DATE RANGE: added after the opening of AD 80, usually credited to Domitian (r. 81 to 96) (VERIFY); in use with rebuilds for nearly 400 years (Beste: four building phases)
REGION: Rome
SIZE: under the whole arena, about 83 x 48 m (VERIFY), two levels; floor about 6 to 7 m below the arena (the lift rose about 24 to 25 ft)
SHAPE: long straight central corridors with curved side corridors, masonry walls in concentric rings and chambers "like a huge thumbprint" (Smithsonian), vertical shafts along the walls, torch lit
PARTS: corridors, cells, vertical lift shafts with grooves and slots, capstan floor holes (some with bronze collars), diagonal ramp slots, wooden floor overhead
MATERIALS: tufa and brick walls (STONE, warm brick), wooden ceiling beams (WOOD), torches
HANDLING: none (environment)
REFERENCE OBJECTS: the hypogeum as excavated and opened to the public (Colosseum Archaeological Park); Beste's technical drawings (German Archaeological Institute, Rome)
DO NOT MIX: Renaissance or modern Colosseum ruins, electric lights, metal gratings
CONFIDENCE: layout SOLID (simplified); builder and date VERIFY
CODE: cl.env_hypogeum

ITEM 2: Capstan (vertical winch) of the hypogeum lifts  [NEW BM-P023]
USED BY: beats 9 to 12, workers
DATE RANGE: hypogeum period (late 1st c. AD onward)
REGION: Rome
SIZE: two stories tall (Beste); bars at chest height on each level
SHAPE: upright wooden post (drum) standing in a floor hole, cross shaped bars through it at two levels, rope winding on the drum
PARTS: post with iron collar at the foot, four bars per level (cross), rope drum, rope running up to a pulley at the shaft head
MATERIALS: oak post and bars (WOOD), iron straps and pin (IRON), hemp rope (ROPE)
HANDLING (CARRY LINE): each worker leans into one bar at chest height with BOTH hands on the bar, palms forward, body tilted into the push, legs driving behind; the bar passes in front of the chest; four men walk the circle per level. Depiction: capstan workers on the Haterii relief crane (Vatican Museums, about AD 100) walk inside a treadwheel; for the capstan push, the 2015 NOVA replica crews (eight men on two decks) are the reference
REFERENCE OBJECTS: no surviving capstan; reconstruction by Beste (Smithsonian 2011); 2015 working replica (Colosseum, Providence Pictures / NOVA)
DO NOT MIX: ship windlass (horizontal), treadwheel crane, iron gears
CONFIDENCE: SOLID (reconstruction from cuttings in the masonry)
CODE: cl.capstan

ITEM 3: Animal lift: cage in its shaft  [NEW BM-P024]
USED BY: beats 6, 7, 12, 13
DATE RANGE: hypogeum period
REGION: Rome
SIZE: cage just big enough for a lion ("nothing bigger than a lion would have fit", Beste); about 2 x 1 x 1.3 m drawn (VERIFY, reconstruction)
SHAPE: box of squared timbers with vertical bars on the front, guided in a vertical shaft by wall grooves, hung from a rope sling over a pulley
PARTS: corner posts, top and bottom frames, front bars, sliding front gate (lifts open with the trap door), rope sling, pulley, shaft guide rails
MATERIALS: WOOD frame, IRON straps and bar ends, ROPE
HANDLING: rope from the capstan drum runs up over the pulley at the shaft head and down to the cage sling
REFERENCE OBJECTS: 2015 replica lift and trap door (Colosseum, 25 ft tall); Beste's reconstruction
DO NOT MIX: iron cage, modern elevator car
CONFIDENCE: SOLID for the system, VERIFY for dimensions
CODE: cl.lift_cage, cl.lift_shaft

ITEM 4: Trap door that drops into a ramp  [NEW BM-P025]
USED BY: beats 1, 14, 15, 19
SHAPE: hinged wooden panel set in the arena floor; released, it swings down to form a ramp from the cage up to the arena; a diagonal slot in the shaft wall guides the ramp
PARTS: plank panel, hinge edge, battens underneath, rope release
MATERIALS: WOOD, IRON hinges
REFERENCE OBJECTS: Beste's diagonal ramp slots; NOVA 2015 replica ("a trap door that could lower to become a ramp")
CONFIDENCE: SOLID
CODE: cl.trapdoor (open 0 to 1)

ITEM 5: Arena floor: timber boards under sand  [NEW BM-P026]
USED BY: beats 1, 2, 14 to 19
SHAPE: board floor over the hypogeum, covered with a layer of sand (harena)
MATERIALS: WOOD boards, sand (pale ochre)
CONFIDENCE: SOLID
CODE: cl.arena_floor

ITEM 6: Lion (Barbary type)  [NEW BM-P027]
USED BY: beats 6, 7, 13, 15, 18
SHAPE: big cat silhouette, heavy mane in dark brown for the male (Barbary lions are shown with dark manes in Roman art), tufted tail
REFERENCE OBJECTS: late 1st c. AD fresco of a venator with a black maned Barbary lioness (Encyclopaedia Romana); Villa Borghese hunt mosaic, 3rd c. (lion at the right)
CONFIDENCE: SOLID
CODE: cl.lion (pose: crouch, run, sit; expr eyes)

ITEM 7: Tiger  [NEW BM-P028]
USED BY: beat 1 only (the screen moment)
SHAPE: big cat, orange with black stripes
CONFIDENCE: SOLID (tigers were shown in Roman spectacles; first under Augustus, Pliny: VERIFY)
CODE: cl.lion(striped=True)

ITEM 8: Roman worker clothing, late 1st to 2nd c. AD  [NEW BM-P029]
USED BY: the Keeper (outfit rkeeper, round glasses kept), capstan crew (operae, operae2)
SHAPE: short sleeved tunic to the knee, belted at the waist with the cloth bloused over the belt; closed leather shoes or sandals; short hair, clean shaven or short beard (both seen in the period)
MATERIALS: wool tunic in plain earth colours (off white, brown, faded red)
REFERENCE OBJECTS: Roman worker in a tunic on Trajan's Column (relief); funerary relief of a marble workshop, Ostia (Museo Ostiense, 1st c. AD)
DO NOT MIX: toga, legionary armour, Greek chiton
CONFIDENCE: SOLID
CODE: rig OUT 'rkeeper', 'operae', 'operae2'

ITEM 9: Venator (arena beast hunter)  [NEW BM-P030]
USED BY: beat 1 (generic arena fighter facing the tigers; never Maximus or any film costume), beat 18 (hunter watching the floor)
SHAPE: belted tunic above the knee, legs bound below the knee with wrappings (fasciae), bare head or no helmet
REFERENCE OBJECTS: Thelepte mosaic, venator in a belted tunic above the knee with boot like footwear; Velleia cippus (Hadrian): short tunic with legs bound by thongs below the knee
DO NOT MIX: murmillo helmet, Gladiator film armour, fur cloaks
CONFIDENCE: SOLID ("venatores had no special attire", Schreiber)
CODE: rig OUT 'venator'

ITEM 10: Venabulum (hunting spear)  [NEW BM-P031]
USED BY: venator
SIZE: about 2 m (VERIFY)
SHAPE: wooden shaft, broad leaf shaped iron head
HANDLING (CARRY LINE): held in BOTH hands, low and forward, left hand forward on the shaft, right hand back near the butt, point toward the animal (Nennig mosaic: "holds a hunting spear in both hands")
REFERENCE OBJECTS: Nennig mosaic (AD 234); Villa Borghese mosaic, 3rd c.
CONFIDENCE: SOLID for the grip; head shape VERIFY
CODE: cl.venabulum

ITEM 11: Colosseum seating with spectators  [NEW BM-P032]
USED BY: beat 16, 17
SHAPE: tiers of seating in an ellipse, arched outer wall in the distance; spectators as a grid of identical small figures (formation rule)
CONFIDENCE: SOLID; capacity about 50,000 (VERIFY range)
CODE: cl.env_cavea, cl.crowd

ITEM 12: Torch  [NEW BM-P033]
USED BY: hypogeum walls (environment light)
SHAPE: wall mounted wooden torch with flame
CONFIDENCE: SOLID ("torch lit labyrinth", History.com)
CODE: cl.torch

## BEAT SHEET

Times are from the original narration (pocketsphinx), before pause tightening.

BEAT 1 (0.04)
LINE: In Gladiator, tigers burst up through trap doors in the arena floor.
BACKGROUND: arena, sand floor, cavea blurred behind
FIGURES: 1 venator, low stance, DETERMINED, venabulum held in both hands
PROP OR DIAGRAM: trap door at frame centre, tiger bursting up out of it
MOTION: trap door already swinging at frame 0, tiger leaps up on "burst" (anticipation crouch inside the shaft, then rise), sand spray, camera punch on "burst"
TEXT: (none: the user's NOW SHOWING card sits at the top 0.2 to 2.8 s)
SFX: wood bang, tiger roar, sand hiss

BEAT 2 (4.61)
LINE: That part was real.
BACKGROUND: same arena, push in on the open trap door
FIGURES: none (tiger out of frame)
PROP OR DIAGRAM: trap door, open shaft below
MOTION: STAMP REAL lands on "real" with a camera punch
TEXT: STAMP: REAL
SFX: stamp thud

BEAT 3 (6.24) SLIDE
LINE: Under the Colosseum sat a machine you ride every day:
BACKGROUND: cutaway: arena floor at top, dark hypogeum below
FIGURES: none
PROP OR DIAGRAM: camera tilts down through the open trap door into a section view
MOTION: slide in, then the camera sinks down the shaft
TEXT: none
SFX: whoosh

BEAT 4 (9.85)
LINE: an elevator.
BACKGROUND: blank parchment diagram
FIGURES: none
PROP OR DIAGRAM: modern elevator car outline morphs into the wooden lift cage at the same size and position
MOTION: hold 0.5 s, then morph
TEXT: TAG: ABOUT AD 80 ONWARD (hedge, VERIFY wording)
SFX: elevator ding, wood creak

BEAT 5 (11.01)
LINE: Below the sand was the hypogeum,
BACKGROUND: hypogeum corridor, torch lit
FIGURES: none
PROP OR DIAGRAM: label HYPOGEUM on a sticker tag with the pronunciation hint
MOTION: camera tracks along the corridor, torches flicker
TEXT: TAG: HYPOGEUM ("UNDERGROUND")
SFX: torch crackle, drip

BEAT 6 (12.82)
LINE: a maze of tunnels and cells.
BACKGROUND: top down simplified plan of the hypogeum (parchment), labelled SIMPLIFIED
FIGURES: none
PROP OR DIAGRAM: corridors draw on, cells fill
MOTION: lines draw along the corridors, hold 0.5 s
TEXT: TAG: SIMPLIFIED
SFX: pen scratch

BEAT 7 (15.6)
LINE: A lion waited in a wooden cage.
BACKGROUND: hypogeum cell
FIGURES: lion inside the cage, close up, eyes moving
PROP OR DIAGRAM: lift cage
MOTION: lion paces one step, tail flick, breath
TEXT: none
SFX: low growl

BEAT 8 (18.16)
LINE: Nothing bigger would fit.
BACKGROUND: parchment diagram
FIGURES: lion
PROP OR DIAGRAM: cage with a dimension arrow; an elephant silhouette slides in and does not fit (red X)
MOTION: elephant pushes in, bounces off, X pops
TEXT: none (caption carries it)
SFX: thud, buzzer

BEAT 9 (19.74) SLIDE
LINE: Beside it stood a capstan,
BACKGROUND: hypogeum, capstan beside the shaft
FIGURES: none yet
PROP OR DIAGRAM: capstan assembles part by part on the narration (post, bars, rope)
MOTION: staged pops
TEXT: TAG: CAPSTAN
SFX: wood knocks

BEAT 10 (21.50)
LINE: an upright winch two stories tall.
BACKGROUND: section view, two levels
FIGURES: Keeper on the lower level for scale, POINT, THINKING
PROP OR DIAGRAM: dimension arrow up the post, two floor levels
MOTION: camera tilts up the post
TEXT: TAG: 2 STORIES
SFX: creak

BEAT 11 (24.15)
LINE: Eight men pushed its bars in a circle,
BACKGROUND: section view
FIGURES: crew of workers (max 3 individuals in front, the rest as a matched formation on the level above), DETERMINED
PROP OR DIAGRAM: capstan turning, rope winding on the drum
MOTION: push walk cycle, bars rotate, camera punch on "Eight"
TEXT: none
SFX: rhythmic grunt, wood creak loop

BEAT 12 (26.46)
LINE: four on each level.
BACKGROUND: same
FIGURES: count markers 1 to 4 pop over each level
PROP OR DIAGRAM: numbers 4 + 4
MOTION: pops on each word
TEXT: none
SFX: ticks

BEAT 13 (28.01)
LINE: Ropes wound around the shaft, and the cage climbed about twenty five feet.
BACKGROUND: section view with shaft
FIGURES: lion in the cage
PROP OR DIAGRAM: rope from drum over pulley to cage; cage rises; dimension arrow 25 FT
MOTION: rope winds, cage rises with ease in out, camera follows up
TEXT: TAG: ABOUT 25 FT (7.6 m)
SFX: rope stretch, ratchet

BEAT 14 (32.52) SLIDE
LINE: At the top, a trap door swung down into a ramp.
BACKGROUND: section at arena level
FIGURES: lion in the cage, crouched
PROP OR DIAGRAM: trap door swings down into a ramp; daylight pours in
MOTION: door swing with overshoot settle, light beam fades up
TEXT: none
SFX: bang, wood rattle

BEAT 15 (35.98)
LINE: The lion ran up it, straight into the light,
BACKGROUND: arena from floor level, bright
FIGURES: lion running up the ramp and out
MOTION: tracking run, sand dust, camera punch on "light", the one flash at half strength
TEXT: none
SFX: paws, roar, crowd swell

BEAT 16 (38.74)
LINE: and fifty thousand people watched it appear from nowhere.
BACKGROUND: cavea with crowd formation
FIGURES: crowd grid rises and cheers in a wave
PROP OR DIAGRAM: counter rolls to about 50,000
MOTION: crowd wave left to right
TEXT: TAG: ABOUT 50,000
SFX: crowd roar

BEAT 17 (42.61) SLIDE
LINE: Dozens of these lifts were hidden under one floor,
BACKGROUND: arena seen from above as an ellipse (parchment diagram)
FIGURES: none
PROP OR DIAGRAM: trap door dots pop around the arena (dozens), hidden by a sand overlay that fades
MOTION: staged pops, hold 0.5 s
TEXT: TAG: ESTIMATES: 24 TO 40+ (hedge)
SFX: pops

BEAT 18 (45.40)
LINE: so a hunter never knew where the next lion would rise.
BACKGROUND: arena
FIGURES: venator in close up (about 3x), WORRIED, eyes darting left and right
PROP OR DIAGRAM: trap doors around him, one starts to lift
MOTION: expression change on "never", eyes dart on "where"
TEXT: none
SFX: heartbeat, creak

BEAT 19 (48.66)
LINE: When that floor opens in Gladiator, you are watching a Roman elevator.
BACKGROUND: arena, the same framing as beat 1
FIGURES: none, then trap door opening exactly as beat 1
PROP OR DIAGRAM: trap door; ghosted cutaway of the cage below
MOTION: camera punch on "Roman elevator", fades into frame 1 for the loop
TEXT: none
SFX: bang (matches beat 1)

## CAPTIONS

[{"t": "In Gladiator, tigers burst", "k": "tigers"},
 {"t": "up through trap doors", "k": "trap"},
 {"t": "in the arena floor.", "k": "floor"},
 {"t": "That part was real.", "k": "real"},
 {"t": "Under the Colosseum sat", "k": "Colosseum"},
 {"t": "a machine you ride every day:", "k": "machine"},
 {"t": "an elevator.", "k": "elevator"},
 {"t": "Below the sand was the hypogeum,", "k": "hypogeum"},
 {"t": "a maze of tunnels and cells.", "k": "maze"},
 {"t": "A lion waited in a wooden cage.", "k": "lion"},
 {"t": "Nothing bigger would fit.", "k": "bigger"},
 {"t": "Beside it stood a capstan,", "k": "capstan"},
 {"t": "an upright winch", "k": "winch"},
 {"t": "two stories tall.", "k": "two"},
 {"t": "Eight men pushed its bars", "k": "Eight"},
 {"t": "in a circle,", "k": "circle"},
 {"t": "four on each level.", "k": "four"},
 {"t": "Ropes wound around the shaft,", "k": "Ropes"},
 {"t": "and the cage climbed", "k": "climbed"},
 {"t": "about twenty five feet.", "k": "twenty"},
 {"t": "At the top, a trap door", "k": "top"},
 {"t": "swung down into a ramp.", "k": "ramp"},
 {"t": "The lion ran up it,", "k": "ran"},
 {"t": "straight into the light,", "k": "light"},
 {"t": "and fifty thousand people", "k": "fifty"},
 {"t": "watched it appear from nowhere.", "k": "nowhere"},
 {"t": "Dozens of these lifts", "k": "Dozens"},
 {"t": "were hidden under one floor,", "k": "hidden"},
 {"t": "so a hunter never knew", "k": "never"},
 {"t": "where the next lion would rise.", "k": "rise"},
 {"t": "When that floor opens in Gladiator,", "k": "Gladiator"},
 {"t": "you are watching a Roman elevator.", "k": "elevator"}]

## POSTING PACK

TITLE options:
1. The Colosseum Had Elevators (Gladiator Got It Right)  (recommended)
2. Gladiator's Trap Doors Were Real
3. How Lions Rose Into the Colosseum

DESCRIPTION: The trap doors in Gladiator were real. Under the Colosseum floor, crews turned two story capstans to lift caged animals into the arena, and archaeologist Heinz Jürgen Beste spent years reading their cuttings in the stone. A working replica lift was installed in the hypogeum in 2015.
Sources: Smithsonian Magazine, "Secrets of the Colosseum" (Beste); PBS NOVA, "Colosseum: Roman Death Trap"

HASHTAGS: #Shorts #History #AncientRome #Colosseum #Gladiator

PINNED COMMENT: Which movie scene should we fact check next against the real history?

ALTERED CONTENT SETTING: No (stylized animation). If the ElevenLabs voice imitates a real person, Yes.

## TOPIC LOG UPDATE

2026-11-20 | Colosseum hypogeum animal lifts (E020) | Rome, Flavian amphitheatre, late 1st c. AD onward | B. MODERN REFRAME | stick figure | scripted | | screen: Gladiator (2000)

## LIBRARY UPDATE

NEW: BM-P022 to BM-P033 (hypogeum, capstan, lift cage, trap door ramp, arena floor, lion, tiger, Roman worker clothing, venator, venabulum, cavea with crowd, torch)
REUSED: none (no Roman entry in the library covers the late 1st c. AD)
