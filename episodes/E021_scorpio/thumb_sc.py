"""E021 thumbnail in the mystery format (engine thumbs.py): the item alone, fully in frame, one phrase."""
import props as PR, thumbs
thumbs.mystery(lambda pn: PR.scorpio(pn, 640, 1500, 3.0, draw=1.0, bolt=True, yaw=-32, pitch=20, H0=110),
               'rcamp', None, ("ROME'S SNIPER", 'RIFLE?'), sizes=(130, 150), colors=(thumbs.GOLD, thumbs.GOLD), out='E021_thumb')
