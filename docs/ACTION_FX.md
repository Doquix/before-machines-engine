# Action effects standard

Set by the channel owner after E015: every action gets effects, at a punchy, action cartoon strength. The engine module is `fx.py` (preset `FX_GAIN = 1.25`; 1.0 is the clean look).

## Which effect goes on which action

| Action | Effects |
|---|---|
| Fast swing or thrust (sword, club, arm, lever) | `smear` swept band from the hand to the tip over the last 0.1 to 0.15 s, plus short `speed_lines` off the tip during the fastest frames |
| Object or vehicle moving fast (charging ship, thrown spear, falling bridge, walking in) | `speed_lines` trailing behind it, anchored to it; spray or dust where it touches water or ground |
| Hit, slam, stamp, landing | `impact` frame (solid burst for two frames, then a flying outline and strokes); add `focus_lines` only on the one or two biggest hits of the video |
| Wood hit or cut | `particles('chips')` (and the older `splinters`) |
| Metal on metal, iron landing, sword clash | `particles('sparks')` plus a small `impact` |
| Feet, shields or objects hitting the ground | `particles('dust')` with `ground=` set so it settles |
| Water hit, bow wave, oars, splash | `particles('splash')` for the hit, `particles('spray')` for continuous wake |
| Stone or rubble | `particles('debris')` |
| Rope release, snap | short `speed_lines` along the rope and a small `impact` |

## Rules

1. **Effects come from the action, not decoration.** Every effect is tied to a measured event time from the beat table (`T`), the same time as its sound effect. No effect without an action, no big action without an effect.
2. **Drive smears from the real motion.** Re-evaluate the pose or the prop angle at a few earlier times (for example t minus 0.12, 0.08, 0.04, 0) and sweep between those positions. Never draw a smear shape by hand that does not match the path the object took.
3. **Order:** smears and speed lines under the moving object; impacts, sparks and chips over it; captions always drawn last so the words stay readable.
4. **Scale with importance.** The single biggest hit of the video gets the largest impact plus focus lines; ordinary hits get a small impact. At most about two focus line moments per video, so the big ones still feel big.
5. **Pure functions of time.** Every effect is computed from time since its event with a fixed seed, so frames render identically in any order and in parallel halves.
6. **Still respect the audience.** Punchy, but an effect never sits over the caption words and never hides the object the narration is naming for longer than its first two frames.
7. **Check stills at the hit frames** (the event time and two to three frames after) before every full render.
