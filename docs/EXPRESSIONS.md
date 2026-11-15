# Expressions and facial hair

The face is drawn in code by `rig.face`, inside the locked E012 figure: round head, big white eyes with black pupils, straight brows, a simple mouth. Expressions and facial hair add range without changing that design.

## Expressions (23)

Original: neutral, happy, surprised, confused, worried, fear, determined, smug, thinking, angry.
Added in E015: seasick, pain, terrified, awe, proud, sly, exhausted, skeptical, disgusted, laughing, embarrassed, crying, bored.

Built from:
* **Eyes:** open, sparkle (awe), arc (closed happy), squeeze (shut tight, > <), squint, plus lids from 0 to 1 and pupil size (tiny pupils for terror).
* **Brows:** a tilt where positive lifts the inner end (worried, sad) and negative drops it (angry, determined), plus named pairs (mix, smug, skeptic). Note: before E015 the tilt was inverted in code, so older episodes rendered worried as angry and the reverse; it is fixed now.
* **Mouths:** flat, smile, frown, O, grim, smirk, wavy, side, puff, grit, scream, ooh, grin, sly, pant, curl, laugh, wobble, cry.
* **Extras:** green tint, sweat drops, tears, laughing tears, blush, stress marks, shock lines.

Reference sheet: `docs/reference/e015_expression_sheet.png`.

## Rules

1. **Match the narration.** Pick the expression the line actually names or implies, and change it on the stressed word with a blink just before, as before. When the narration names a feeling, show it in a close up (figure about 3x) so the face is big enough to read.
2. **Readable at size.** Below about 58 px head diameter on screen, subtle expressions automatically fall back to a bold one (skeptical and sly become smug, seasick becomes worried, and so on), and extras only appear above about 80 px. Use subtle expressions only in close ups; give small figures and formations bold ones.
3. **Check on the expression sheet** (large and small) before adding a new expression, and add it to the sheet script `episodes/E015_corvus/exprsheet.py`.

## Facial hair (11 styles)

`stubble, short, full, long, goatee, vandyke, chinstrap, mustache, handlebar, walrus, mutton`, set per outfit with `beard=<colour>, beard_style='<style>'` in `rig.OUT`. Drawn in the channel's own shapes (a user supplied stock reference was used for style only, not copied). Reference sheet: `docs/reference/e015_facial_hair_sheet.png`.

Rules:
1. **The mouth always sits on bare skin.** Styles that cover the mouth area cut a skin patch around it (bigger when the mouth is open), so every expression reads through any beard. Moustaches sit above the mouth, never over it.
2. **Period and culture first.** Choose styles from the evidence for the culture and date. E015 example: Pliny says barbers reached Rome around 300 BC and daily shaving came later, so mid Republic Romans get a mix of clean shaven and stubble; Punic men get full and long beards as on Punic stelae.
3. **Variety in groups.** Give named figures distinct hair and beard combinations so viewers can tell them apart at a glance.
