# Before Machines engine

Code rendered motion graphics for the Before Machines YouTube Shorts channel (ancient weapons, crafts and lost techniques). Every frame is drawn with Python and Pillow at 2x, then encoded with FFmpeg to a 1080x1920, 30 fps H.264 MP4 with AAC audio mastered to about -14 LUFS.

![Rig standard](docs/rig_standard.png)

## Layout

| File | What it does |
|---|---|
| `lib.py` | Easing, camera (punch, shake, drift factor), the camera aware 2x vector `Pen`, radial mask |
| `rig.py` | Skeleton rig (forward kinematics plus two bone IK hands), poses, expressions, wardrobe, contact shadow |
| `props.py` | Sticker tags, stamp, callouts, arrows, trebuchet, castle, wall blocks |
| `env.py` | Painted environments, cached, blurred and graded so figures read clearly |
| `make_map.py` | Real coastline maps from `global-land-mask` (set `LEVELS` per episode) |
| `timeline.py` | Pause tightening, chapter pauses (padded with silence), word onsets to `timing.json` |
| `episodes/E014_greek_fire/` | Latest episode: `gf.py` (props and environments), `render_gf.py` (beat table, scenes, captions, cue sheet), `audio_gf.py` (SFX, modal music bed, ducking, mix) |

Only the beat table `T`, `SCENES`, the `sc_*` scene functions, `EPISODE_OUTFIT` and map settings are episode specific. Everything else is the engine.

## Running an episode

The scripts import the engine modules from the same folder, so work in a scratch build folder:

```bash
pip install --break-system-packages pillow numpy scipy soundfile global-land-mask
mkdir build && cp *.py episodes/E014_greek_fire/*.py build/ && cd build
ffmpeg -i narration.mp3 -ar 48000 -ac 1 vo_orig.wav
python3 timeline.py              # edit PHR, SIL and DRAMA first
python3 make_map.py
python3 render_gf.py cues && python3 audio_gf.py
python3 render_gf.py still 0.5 3.0 7.0   # always look at stills first
python3 render_gf.py seg 0 771 | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p a.mp4
```

Render in two parallel halves, check each frame count, join, then master: pre limit the mix (`volume=+5.8dB,alimiter=limit=0.70:level=false`), measure with `ebur128`, apply the remaining gain and limit again before AAC.

## Standards

**Audience.** Mostly US men aged 55 and over. One text element at a time, room to read, fewer but meaningful moves.

**Rig.** Bone limbs (cream fill, dark outline), big head (about a third of body height) with round expressive eyes, shoulders at the torso edges so arms hang visibly at the sides, short sleeve caps, small hands and shoes. Garments stop at the knee so thighs and knees always show. Every figure casts a contact shadow and stands on solid ground.

**Edit.**
* Hard cuts by default, a slide push (about 0.35 s, always from the right) at 3 or 4 chapter turns, a 0.3 s dissolve on big brightness jumps, and match dissolves when the same object appears on both sides of a change. No radial wipes.
* About 6 camera punches per video, shakes only on impacts, at most one flash at half strength, camera drift at half strength.
* Captions word by word, 76 px, at most 4 words per chunk, keyword in amber, centered at y 1440.
* Tags only when they add something the caption does not: a date, a name's spelling, a hedge such as LIKELY.
* J cuts: the next shot's sounds start 0.12 s before the change.
* Never leave a frame empty after a change, and nothing floats.

**History.** Only well documented facts. Hedge reconstructions and disputed points on screen (LIKELY, LATER ACCOUNTS, ROUTE SIMPLIFIED). Every costume and prop must match the period.
