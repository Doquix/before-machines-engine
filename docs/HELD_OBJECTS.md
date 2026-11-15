# Held and carried objects: the animator standard

This applies to every object a figure holds, carries, wields, pulls, throws or wears in a Before Machines Short: weapons, shields, tools, ropes, levers, jars, sacks, scrolls, oars, reins, anything. It was set by the channel owner after E015, where a scutum looked pasted beside the body. Treat it as a hard rule, not a suggestion.

## The rules

1. **Every object has a real grip point.** Before drawing, decide where a real hand holds it: a sword's hilt, a hammer's handle end, a spear's shaft at two points, a shield's grip behind the boss, a jar's handles or its base, a rope's line, a lever's bar. The hand goes exactly there.

2. **The hand drives the object, never the other way round.** Place the hand on the grip with IK (`hands={'F': ..., 'B': ...}` in `rig.figure`), then draw the object from the hand's position and the forearm's direction. When the arm moves, the object moves with it. An object placed at a fixed screen position near a figure is wrong.

3. **Layer it the way it is really held.** Ask what is in front from the camera:
   * Gripped from the front (sword, hammer, torch, rope, lever, tube): object under the fingers, hand drawn on top so the grip shows. `held` and `grip` callbacks do this.
   * Gripped from behind (shield on its grip or straps, a board, a basket carried against the body): the board in front, hand and forearm hidden behind it, only the upper arm or shoulder showing at the edge.
   * Worn (helmet, belt, scabbard, quiver, cloak): attached to its body joint and drawn in that joint's layer.
   Never let a limb cross over the front of an object it is supposed to be holding from behind, and never let an object cover the hand that is supposed to be gripping it from the front.

4. **Two handed objects use both hands on the object.** Spears, oars, poles, carried tubes, heavy jars, sacks: both hands on the grip points along the object, the shaft passing through both fists in a straight line.

5. **Size and place objects so they clear the body.** No object sits over a joint it would block in real life. Shields stop below the shoulder and above the knees; carried loads sit at the waist or chest, never at face height where the big head hides the hands; nothing covers the feet. Keep real proportions relative to the figure unless the scene is a diagram.

6. **Weight changes the pose.** Heavy things bend the knees, lean the torso back or forward to balance, and pull the arms straight. Light things are held loosely. A figure carrying a jar should not stand in the plain idle pose.

7. **Thrown and released objects follow the hand until the release frame.** The object stays locked to the hand through the wind up, separates on the release word, then follows its own arc. Ropes go slack after release.

8. **Check on a pose sheet before use.** Render any new held object on the figure in at least four poses (idle, walk, a braced or loaded pose, the action the scene needs) and look at it before it goes into an episode. Save the sheet in `docs/reference/`. The reference example is `docs/reference/e015_shield_grip_sheet.png`.

## How the engine supports it

* `rig.figure(..., hands=..., held=fn, grip=fn)`: `hands` sets IK hand targets in figure local units; `held` and `grip` draw the object after the clothing and before the arms, so the hands land on top.
* Outfits with `scutum` are handled automatically: the back hand goes to the grip by IK, the shield is drawn over the forearm, and it follows the pose.
* `render_cv.sword_held(pn, J)` is the pattern for a one handed weapon: blade from the hand along the forearm direction, guard across the fist.
* New objects should get the same treatment: a function that takes the joint dict `J` and draws from `J['haF']` / `J['haB']` and the elbow to hand direction, never from fixed coordinates.
