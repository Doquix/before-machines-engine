"""Shot quality gate 3: automatic checks on a rendered preview (render skill, section 6).

Input: a folder with preview frames f00000.png ... (any size, 9:16) and qc.json written by the episode's preview run:
  {"fps": 30, "W": 1080, "H": 1920,
   "shots": [{"name", "start", "end", "cue", "kind": "figure"|"graphic", "must_see", "proves"}],
   "frames": {"<n>": [{"t": "subject"|"key"|"arrow"|"text"|"token", ...}]}}
Records are in final 1080x1920 pixels: subject/key {"box": [x0, y0, x1, y1]}, arrow {"w", "len"}, text {"px"},
token {"px"}. Run: python3 qc.py <folder> [preview.mp4]. Exit code 1 when any check fails.
"""
import json, os, sys, subprocess
import numpy as np
from PIL import Image

LIM = dict(fig_h=0.25, gfx_w=0.18, arrow_w=8, arrow_len=120, text_px=40, token_px=60,
           band=(1260, 1620), cue_win=0.2, cue_diff=3.0, empty_frac=0.30)

def load(folder):
    q = json.load(open(os.path.join(folder, 'qc.json')))
    return q

def frame(folder, n, size=None):
    p = os.path.join(folder, f'f{n:05d}.png')
    if not os.path.exists(p): return None
    im = Image.open(p).convert('L')
    return np.asarray(im.resize(size) if size else im, dtype=np.float32)

def run(folder, video=None):
    q = load(folder); fps = q['fps']; W, H = q['W'], q['H']
    rep = []; fails = 0
    for s in q['shots']:
        res = dict(shot=s['name'], must_see=s['must_see'], fails=[], warns=[])
        a, b = int(s['start'] * fps), int(s['end'] * fps)
        cue_n = int(s['cue'] * fps)
        recs = q['frames'].get(str(cue_n), [])
        subj = [r['box'] for r in recs if r['t'] == 'subject']
        keys = [r['box'] for r in recs if r['t'] == 'key']
        # 1. size of the MUST SEE subject at the cue frame
        if not subj: res['fails'].append('no MUST SEE subject recorded at the cue frame')
        for bx in subj:
            if s['kind'] == 'figure' and (bx[3] - bx[1]) / H < LIM['fig_h']:
                res['fails'].append(f"subject {100 * (bx[3] - bx[1]) / H:.0f}% of frame height (min {100 * LIM['fig_h']:.0f}%)")
            if s['kind'] == 'graphic' and (bx[2] - bx[0]) / W < LIM['gfx_w']:
                res['fails'].append(f"key graphic {100 * (bx[2] - bx[0]) / W:.0f}% of frame width (min {100 * LIM['gfx_w']:.0f}%)")
        # 2. nothing important in the caption band
        for bx in keys:
            if bx[3] > LIM['band'][0] and bx[1] < LIM['band'][1]:
                res['fails'].append(f"key element enters the caption band (y {bx[1]:.0f} to {bx[3]:.0f})")
        # 3. arrows, text and tokens readable at phone size once settled: measured over the last 0.3 s of the shot
        #    (and never before 0.4 s after the cue), so pops and draw ons are not measured mid animation
        for n in range(max(a, int((s['cue'] + 0.4) * fps), b - int(0.3 * fps)), b):
            for r in q['frames'].get(str(n), []):
                if r['t'] == 'arrow' and (r['w'] < LIM['arrow_w'] or r['len'] < LIM['arrow_len']):
                    res['fails'].append(f"arrow {r['w']:.0f} px wide, {r['len']:.0f} px long"); break
                if r['t'] == 'text' and r['px'] < LIM['text_px']:
                    res['fails'].append(f"label text {r['px']:.0f} px (min {LIM['text_px']})"); break
                if r['t'] == 'token' and r['px'] < LIM['token_px']:
                    res['fails'].append(f"token {r['px']:.0f} px (min {LIM['token_px']})"); break
        res['fails'] = list(dict.fromkeys(res['fails']))
        # 4. something visibly changes around the cue word
        n0, n1 = max(a, int((s['cue'] - LIM['cue_win']) * fps)), min(b - 1, int((s['cue'] + LIM['cue_win']) * fps))
        f0, f1 = frame(folder, n0), frame(folder, n1)
        if f0 is not None and f1 is not None:
            sx = f0.shape[1] / W
            bx = (keys or subj or [[0, 0, W, LIM['band'][0]]])[0]
            x0, y0, x1, y1 = [int(max(0, v * sx)) for v in bx]
            d = float(np.abs(f0[y0:y1, x0:x1] - f1[y0:y1, x0:x1]).mean()) if (x1 > x0 and y1 > y0) else 0.0
            if d < LIM['cue_diff']: res['fails'].append(f"little visible change on the cue word (diff {d:.1f})")
        # 5. empty frame area above the captions (warning: skies and parchment can be legitimately plain)
        fc = frame(folder, cue_n)
        if fc is not None:
            sx = fc.shape[1] / W; top = fc[:int(LIM['band'][0] * sx)]
            bs = max(4, int(60 * sx)); hh, ww = top.shape[0] // bs, top.shape[1] // bs
            blocks = top[:hh * bs, :ww * bs].reshape(hh, bs, ww, bs).std(axis=(1, 3))
            frac = float((blocks < 2.5).mean())
            if frac > LIM['empty_frac']: res['warns'].append(f"{100 * frac:.0f}% of the frame above the captions is plain")
        fails += bool(res['fails'])
        rep.append(res)
    # 6. frozen frames on the whole preview
    if video:
        out = subprocess.run(['ffmpeg', '-i', video, '-vf', 'freezedetect=n=0.003:d=0.8', '-map', '0:v', '-f', 'null', '-'],
                             capture_output=True, text=True).stderr
        fz = [l.split('freeze_start: ')[1] for l in out.splitlines() if 'freeze_start' in l]
        if fz: rep.append(dict(shot='ALL', must_see='', fails=[f'frozen from {x} s' for x in fz], warns=[])); fails += 1
    return rep, fails

if __name__ == '__main__':
    rep, fails = run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    for r in rep:
        st = 'FAIL' if r['fails'] else 'pass'
        print(f"{r['shot']:5s} {st}  {'; '.join(r['fails'] + ['warn: ' + w for w in r['warns']])}")
    json.dump(rep, open(os.path.join(sys.argv[1], 'qc_report.json'), 'w'), indent=1)
    sys.exit(1 if fails else 0)
