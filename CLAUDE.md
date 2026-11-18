# Before Machines engine: instructions for Claude

Read `README.md` for the engine layout and standards before working on an episode.

**Held objects are a hard rule.** Every object a figure holds, carries, wields, pulls, throws or wears must be drawn the way a professional animator would: hand on the real grip point by IK, the object driven by the hand, layered the way it is really held, clear of the body, with weight shown in the pose, and checked on a pose sheet before use. Full rules: `docs/HELD_OBJECTS.md`. This applies to all future props, not just shields.

**Actions are physically real; only expressions are exaggerated.** Every action uses the real technique and body mechanics (a bow is drawn with a straight bow arm, a level arrow and the draw elbow in line behind it), checked against a reference of a real person before use. Details: `docs/HELD_OBJECTS.md`.

**Props are drawn as detailed as possible.** Figures stay simple; every object carries real construction (seams, rivets, lashings, joints), material treatment (wood grain, metal highlights, rope twist), at least two tones of light and shadow, true curvature, light wear, and strict period accuracy. Detail scales with on screen size so it still reads on a phone, and every new prop is checked at small, medium and full screen sizes before use. Full rules: `docs/PROP_DETAIL.md`.

**Every action gets effects, punchy strength.** Swings and thrusts get motion smears and speed lines, fast moving objects get speed lines plus spray or dust, every hit gets an impact frame (focus lines only on the one or two biggest), and particles match the material: chips for wood, sparks for metal, dust for ground, splash and spray for water. Effects are tied to measured event times, smears follow the real motion path, captions stay on top. Module: `fx.py`. Full rules: `docs/ACTION_FX.md`.

**Expressions and facial hair.** 23 expressions and 11 facial hair styles live in `rig.py`. Match the expression to the narration and change it on the stressed word; subtle expressions only in close ups (they fall back to bold ones automatically on small figures). Beards never cover the mouth, which always sits on bare skin, and styles follow the culture and period. Full rules: `docs/EXPRESSIONS.md`.

**The 12 principles of animation.** Every action gets anticipation, easing, arcs, follow through and settle, and held figures get secondary motion (breathing, blinks), within the realism rule above: rigid props never squash. Helpers `antic` and `strike` in the E017 render script. Full mapping and checklist: `docs/ANIMATION_PRINCIPLES.md`.
