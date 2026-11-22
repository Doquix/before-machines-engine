"""E021 thumbnail in the mystery format (engine thumbs.py)."""
import props as PR, thumbs
ox_, oy_ = PR.scorpio_pt('frame', 4.4, -32, 20, 1.0, 110)
thumbs.mystery(lambda pn: PR.scorpio(pn, 560 - ox_, 1100 - oy_, 4.4, draw=1.0, bolt=True, yaw=-32, pitch=20, H0=110),
               'rcamp', 'rkeep21', ('NO BOW.', 'NO GUNPOWDER.', 'SO WHAT FIRED IT?'), out='E021_thumb')
