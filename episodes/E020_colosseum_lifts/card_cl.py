"""E020 NOW SHOWING cards (portrait and landscape), poster slot left blank for the user's edit."""
from props import now_showing_card
for orient in ('portrait', 'landscape'):
    for name, bg in (('white', (255, 255, 255)), ('transparent', None)):
        im, slot, card = now_showing_card('Gladiator', 2000, 'The arena trap doors. Real or not?', orient == 'portrait', 3, bg)
        (im.convert('RGB') if bg else im).save(f'now_showing_{orient}_{name}.png')
        print(orient, name, im.size, 'slot', slot, 'card', card)
