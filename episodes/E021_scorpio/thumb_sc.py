"""E021 thumbnail in the mystery format (engine thumbs.py): one phrase."""
import props as PR, thumbs
ox_, oy_ = PR.scorpio_pt('frame', 4.4, -32, 20, 1.0, 110)
thumbs.mystery(lambda pn: PR.scorpio(pn, 560 - ox_, 1100 - oy_, 4.4, draw=1.0, bolt=True, yaw=-32, pitch=20, H0=110),
               'rcamp', 'rkeep21', ("ROME'S SNIPER", 'RIFLE?'), sizes=(130, 150), colors=(thumbs.GOLD, thumbs.GOLD), out='E021_thumb')
