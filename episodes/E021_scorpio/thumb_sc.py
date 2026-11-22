"""E021 thumbnail in the mystery format (engine thumbs.py): the item alone, one phrase."""
import props as PR, thumbs
ox_, oy_ = PR.scorpio_pt('frame', 4.8, -32, 20, 1.0, 110)
thumbs.mystery(lambda pn: PR.scorpio(pn, 700 - ox_, 1120 - oy_, 4.8, draw=1.0, bolt=True, yaw=-32, pitch=20, H0=110),
               'rcamp', None, ("ROME'S SNIPER", 'RIFLE?'), qmark=(560, 1060), sizes=(130, 150),
               colors=(thumbs.GOLD, thumbs.GOLD), out='E021_thumb')
