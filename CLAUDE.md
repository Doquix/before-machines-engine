# Before Machines engine: instructions for Claude

Read `README.md` for the engine layout and standards before working on an episode.

**Held objects are a hard rule.** Every object a figure holds, carries, wields, pulls, throws or wears must be drawn the way a professional animator would: hand on the real grip point by IK, the object driven by the hand, layered the way it is really held, clear of the body, with weight shown in the pose, and checked on a pose sheet before use. Full rules: `docs/HELD_OBJECTS.md`. This applies to all future props, not just shields.

**Props are drawn as detailed as possible.** Figures stay simple; every object carries real construction (seams, rivets, lashings, joints), material treatment (wood grain, metal highlights, rope twist), at least two tones of light and shadow, true curvature, light wear, and strict period accuracy. Detail scales with on screen size so it still reads on a phone, and every new prop is checked at small, medium and full screen sizes before use. Full rules: `docs/PROP_DETAIL.md`.

**Every action gets effects, punchy strength.** Swings and thrusts get motion smears and speed lines, fast moving objects get speed lines plus spray or dust, every hit gets an impact frame (focus lines only on the one or two biggest), and particles match the material: chips for wood, sparks for metal, dust for ground, splash and spray for water. Effects are tied to measured event times, smears follow the real motion path, captions stay on top. Module: `fx.py`. Full rules: `docs/ACTION_FX.md`.
