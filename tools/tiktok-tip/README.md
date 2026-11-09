# TikTok-tipvideo (WayFare Reizen)

Korte TikTok (30-35 sec) met één nuttige reistip, een sterke hook, de stem van Nick (of Thomas in ElevenLabs), bewegend beeld met filmlook, ondertitels, een geanimeerde uitleg-graphic, logo, zachte muziek en een eindkaart naar de gratis reisgids.

Volledige werkwijze: zie de skill `wayfare-tiktok-tip`.

## Bestanden
- `grade.txt`: ffmpeg-filter voor de subtiele filmlook (alle clips).
- `audio.sh`: stem opschonen + muziek op -30 LUFS + ducking. `./audio.sh stem.m4a music/zephiramusic-travel-lofi.mp3 32.4 mix.wav`
- `examples/vietnam-tet-overlay.py`: overlay met hook, datumkaart, kalenderstrook, badge, eindkaart, logo, ondertitels. Beste startpunt.
- `examples/srilanka-trein-overlay.py`: overlay met routekaartje (spoor, afzetting, tuktuk, trein).
- `symbols/<land>/`: transparante symbolen van Nick.
- `music/`: vaste muziek.
- Logo: `2026/brand/logo-creme-tiktok.png` (crème, transparant).

## Overlay renderen
Werkmap met `overlay.py`, `sym/` (symbolen) en `logo.png`. Render in 8 delen tegelijk:
`for p in 0 1 2 3 4 5 6 7; do python3 overlay.py $p 8 & done; wait`
Frames komen in `ov/00000.png ...` (30 fps, 1080x1920, transparant).

## Monteren
Per clip: `setpts=PTS-STARTPTS`, dan
- 30/60 fps: `fps=30`
- 24 fps: na schalen `minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1` (anders schokt het)
- liggend naar staand: `crop` op bronresolutie (9:16), dan `scale=1080:1920:flags=lanczos`
- daarna `setsar=1,<grade.txt>`
Geen eigen pans op integer-crops (schokt). Alle clips `concat`, `overlay` met `ov/%05d.png`, audio `mix.wav`, `libx264 -crf 20 -maxrate 9M`.
