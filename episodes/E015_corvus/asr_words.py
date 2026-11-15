"""Offline word timestamps with pocketsphinx (bundled en-US model, no download): writes "time word" lines to asr.txt.
Usage: ffmpeg -i vo_orig.wav -ar 16000 -ac 1 -f s16le vo16.raw && python3 asr_words.py > asr.txt"""
from pocketsphinx import Decoder
import sys
d = Decoder(samprate=16000)
raw = open('vo16.raw','rb').read()
d.start_utt(); d.process_raw(raw, full_utt=True); d.end_utt()
for s in d.seg():
    if s.word.startswith('<') or s.word.startswith('['): continue
    print(f"{s.start_frame/100:6.2f} {s.word}")
