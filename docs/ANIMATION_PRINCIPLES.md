# The 12 principles of animation, as applied in this engine

Source: the classic Disney principles (summary at idearocketanimation.com, 12 principles of animation). The house rule still holds: actions are physically real, only expressions are exaggerated. Rigid props (bronze, iron, wood) never squash; soft things do.

| Principle | How we apply it | Where |
|---|---|---|
| Squash and stretch | Only on soft or graphic things: tags and stamps pop with overshoot, dust puffs, eye blinks. Never on metal or wooden props, never on the body during real actions. | props.tag, props.stamp, fx particles, rig blink |
| Anticipation | Every thrust draws back before it drives forward, and the whole body loads with it (torso leans back, weight shifts back), not just the arms. Every big swing of a long weapon lifts slightly first. | lib.keys, render_sp.strike, render_sp.antic |
| Staging | One idea per beat; one text element at a time; cut clutter (E017 roof: 10 arrows, not 16) so the key shape reads. | scene design |
| Straight ahead and pose to pose | Key poses in POSES, in betweens by easing; particles and swings are simulated straight ahead. | rig.POSES, fx |
| Follow through and overlapping action | Successive breaking of joints: the hands lead, the body follows about 2 frames later, the head after the body, strap hung shields and long wooden shafts last; each overshoots and settles. Use `follow` springs chained on a precomputed time grid instead of hand set delays. Heavy things overshoot and settle; recoil after impacts. Metal never bends. | lib.follow, render_sp.sc_neck, sc_hook |
| Ease in, ease out | No linear moves except constant marching; falls accelerate (ei2), stops decelerate (eo3), punches overshoot. Key a move with `keys` so every segment names its easing. | lib easing, lib.keys |
| Arcs | Thrown and falling objects follow arcs; pole weapons rotate around the hands; walking figures rise and fall with each step; a strap hung shield swings around the neck. | sc_hook bob, sc_roof arrows, sc_neck |
| Secondary action | Every figure breathes (a slow torso sway, phase offset per figure); blinks; expressions change on the stressed word. | sp.phalangite, sp.hoplite |
| Weight (planted feet) | Any weight shift (lunge, thrust, brace, push) moves the pelvis and re-solves both legs by IK so the feet stay planted; never rotate the legs by hand during an action, which slides the feet. | rig.plant_legs |
| Timing | Every event is tied to a measured word onset; strikes hold at full extension briefly before recovering; sounds start with or just before the action (J cuts). | beat table T, cue sheet |
| Exaggeration | Faces only (23 expressions); actions stay physically real. | rig expressions |
| Solid drawing | Props carry two tones of light and shadow, rims, rivets and wear so they read as 3D. | docs/PROP_DETAIL.md |
| Appeal | Big round heads, clear silhouettes, one strong defining item per character (helmet, shield). | rig standard |

Checklist for every new scene: does each action have an anticipation, an overshoot or settle, an arc, a sound on its key frame, and at least one secondary motion on any figure that holds still for more than a second?

## Reference test: the sarissa thrust (E017)

`episodes/E017_sarissa/motion_test_sp.py` renders one thrust three ways, stacked: linear (arms only, even spacing), the E017 `strike` helper as shipped (wind up, accelerating drive and hold, arms only), and all principles applied. Red dots under each figure mark the rear hand once per frame, so spacing is visible. Still: `docs/reference/e017_thrust_motion_test.png`.

The thrust recipe, at 30 fps:
* `keys`: anticipation 9 frames back to -0.35 (eio), drive about 5 frames to 1.0 accelerating (ei2) on the measured hit time, hold 7 frames, recover 15 frames (eio).
* Hands travel 38 units with the arms plus the body shift; the body (`follow` 3.2 Hz, z 0.55) shifts the pelvis 12 units by `plant_legs` with a 14 unit wider stance and a 4 to 8 unit drop, and leans the torso 6 to 15 degrees.
* Head follows the torso (2.6 Hz, z 0.5); the strap hung pelta follows the shoulder (2.2 Hz, z 0.32, clamp 16 units); the sarissa tip follows the hand (5.5 Hz, z 0.22) as a slight flex of at most 9 units on top of a 6 unit sag.
* Expression changes to angry on the drive and back after the recovery.

Lessons: overlap gives the biggest gain for the least work; a real sarissa jab travels little, so sell it with a camera punch and the effects from `docs/ACTION_FX.md`, never a longer reach; a straight thrust has no arc and must not be curved. Known quirk: `render_sp.strike` recovers to 0.25, not 0, so the weapon stays slightly forward after the move; use `keys` for new thrusts.
