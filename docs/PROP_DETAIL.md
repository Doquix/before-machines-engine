# Prop detail standard

Set by the channel owner after E015: objects must be as detailed as possible. Figures stay simple (the locked E012 rig); the props carry the detail and the historical accuracy. This applies to every object: weapons, armour, shields, tools, ships, machines, buildings, containers, furniture.

## What every prop must have

1. **Real construction, drawn.** Show how the object was actually made and assembled: planks and their seams, nails and rivets, lashings and bindings, pegs and joints, rims and edging, hinges, straps and buckles, handles and how they attach. A shield shows its edging and boss rivets; a ship shows strakes, oar ports and the ram's fins; a spear shows the socket and its rivet.

2. **Materials that read as materials.** Each material gets its own treatment:
   * Wood: grain lines following the shape, darker end grain, a lighter edge bevel.
   * Iron and steel: cool grey with a hard highlight stripe and a darker underside.
   * Bronze and brass: warm gold with a bright highlight and a brown shadow edge.
   * Leather: warm brown, stitching dashes along edges.
   * Rope and cord: twisted strand marks, not a flat line.
   * Cloth: fold lines where it bends, hem lines.
   * Stone and clay: chips, a rim highlight, slightly irregular outline.

3. **Light and shadow.** At least two tones per surface (a lit side and a shade side, light from the upper left) plus one highlight on metal or glaze. A soft contact shadow where the object meets the ground or the body.

4. **Shape that is curved where the real thing is curved.** A scutum bows around the body, a helmet is a dome, a jar swells. Use a highlight band and an inner rim line to show the curve instead of drawing a flat outline.

5. **Use and wear.** Edges slightly worn, a scratch or dent on weapons and armour, soot on fire tools, water staining on hulls. Light touches only, enough to say "used".

6. **Period accuracy first.** Detail never invents features: every rivet, decoration and fitting must match the culture and date of the episode. When a detail is uncertain, leave it plain rather than guess, and hedge on screen if it matters.

## Detail that survives on a phone

The audience watches on phones and many are 55 and over, so detail must read at 1080 px wide:

* **Scale detail with screen size (level of detail).** Each prop function takes its drawn size into account: below about 120 px on screen draw the silhouette, main colours and one or two key features; from 120 to 400 px add construction and material marks; above 400 px (close ups, diagrams) draw everything. Lines thinner than about 2 px at final size, or features smaller than about 6 px, are noise: skip them at that size.
* **Detail never competes with the silhouette.** Keep the outline bold (the INK outline) and put detail inside it in lower contrast tones.
* **Close ups are where detail pays off.** When the narration names an object or a part, give it a full screen or diagram beat so the detail is actually seen.

## Process

* Build each new prop as a reusable function with a `detail` level (or derive it from its scale), so it can be drawn as a small map token and as a full screen close up.
* Before using a new or upgraded prop, render it at three sizes (small, medium, full screen) on parchment and look at it, alongside the held object pose sheet from `docs/HELD_OBJECTS.md`. Save the sheet in `docs/reference/`.

## Reference

`detail.py` holds the shared material helpers. E015 is the first episode built to this standard: see `docs/reference/e015_detail_*.png` for the three size sheets (galley, figure kit with scutum, helmet and sword, corvus with spike and pestle) and `episodes/E015_corvus/propsheet_cv.py` for the sheet script.
