# The 12 principles of animation, as applied in this engine

Source: the classic Disney principles (summary at idearocketanimation.com, 12 principles of animation). The house rule still holds: actions are physically real, only expressions are exaggerated. Rigid props (bronze, iron, wood) never squash; soft things do.

| Principle | How we apply it | Where |
|---|---|---|
| Squash and stretch | Only on soft or graphic things: tags and stamps pop with overshoot, dust puffs, eye blinks. Never on metal or wooden props, never on the body during real actions. | props.tag, props.stamp, fx particles, rig blink |
| Anticipation | Every thrust draws back before it drives forward (`strike`). Every big swing of a long weapon lifts slightly first (`antic`). | render_sp.strike, render_sp.antic |
| Staging | One idea per beat; one text element at a time; cut clutter (E017 roof: 10 arrows, not 16) so the key shape reads. | scene design |
| Straight ahead and pose to pose | Key poses in POSES, in betweens by easing; particles and swings are simulated straight ahead. | rig.POSES, fx |
| Follow through and overlapping action | Heavy things overshoot and settle (`antic` uses eoback); a shield on a strap catches and swings on its strap before resting; recoil after impacts. | render_sp.sc_neck, sc_hook |
| Ease in, ease out | No linear moves except constant marching; falls accelerate (ei2), stops decelerate (eo3), punches overshoot. | lib easing |
| Arcs | Thrown and falling objects follow arcs; pole weapons rotate around the hands; walking figures rise and fall with each step; a strap hung shield swings around the neck. | sc_hook bob, sc_roof arrows, sc_neck |
| Secondary action | Every figure breathes (a slow torso sway, phase offset per figure); blinks; expressions change on the stressed word. | sp.phalangite, sp.hoplite |
| Timing | Every event is tied to a measured word onset; strikes hold at full extension briefly before recovering; sounds start with or just before the action (J cuts). | beat table T, cue sheet |
| Exaggeration | Faces only (23 expressions); actions stay physically real. | rig expressions |
| Solid drawing | Props carry two tones of light and shadow, rims, rivets and wear so they read as 3D. | docs/PROP_DETAIL.md |
| Appeal | Big round heads, clear silhouettes, one strong defining item per character (helmet, shield). | rig standard |

Checklist for every new scene: does each action have an anticipation, an overshoot or settle, an arc, a sound on its key frame, and at least one secondary motion on any figure that holds still for more than a second?
