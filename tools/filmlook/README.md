# WayFare Film (vaste filmlook)

Eén look voor alle beelden: stock, eigen beelden en AI. Zo lijkt alles van dezelfde camera te komen.

**De look:** zachte zwarten, diep WayFare-groen in de schaduwen, warm crème en goud in het licht, rustiger groen en blauw, een warme gloed rond felle lichten (halation), een zachte vignet en filmkorrel.

## Bestanden
- `wayfare-film.cube`: de kleur-LUT. Werkt ook in CapCut, Premiere, DaVinci Resolve en Final Cut (alleen de kleur, zonder korrel en gloed).
- `filmlook.sh`: de complete look met ffmpeg (HDR omzetten, 30 fps, 9:16-uitsnede, LUT, gloed, vignet, korrel).
- `make_lut.py`: maakt de `.cube` opnieuw aan als we de look willen bijstellen.
- `voor-na.png`: voorbeeld.

## Gebruik
```
./filmlook.sh clip.mp4 uit.mp4                       # staand 1080x1920
./filmlook.sh liggend.mp4 uit.mp4 --x 0.35           # liggend: kies waar de uitsnede staat
./filmlook.sh ai.mp4 uit.mp4 --ai --zoom 1.1         # AI-beeld: zachter, extra korrel, randen weg
./filmlook.sh clip.mp4 uit.mp4 --ss 3 --t 4 --exp 0.03
```
iPhone-HDR (HLG) wordt automatisch omgezet. 24 fps wordt vloeiend naar 30 fps gezet.
Vervangt `tools/tiktok-tip/grade.txt`.
