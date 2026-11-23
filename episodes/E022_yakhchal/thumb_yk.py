"""E022 thumbnail in the mystery format (engine thumbs.py): the domed ice house alone, fully in frame, one phrase.
Tried with the shade wall beside it (2026-11-24): the wall reads as a plain box and shrinks the dome, so the dome
stands alone; its convex bell profile keeps it from reading as a straight sided pyramid."""
import lib
lib.BLEND = True
import props as PR, thumbs
thumbs.mystery(lambda pn: PR.yakhchal_dome(pn, 540, 1500, 40),
               'yknight', None, ("PERSIA'S DESERT", 'FREEZER?'), sizes=(112, 150), colors=(thumbs.GOLD, thumbs.GOLD), reticle=None, out='E022_thumb')
