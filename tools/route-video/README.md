# Route-video (WayFare Reizen)

Bewegende routekaart voor de bestemming van de week: Instagram-story, Instagram-reel (met muziek) en TikTok (met voice-over en ondertiteling).

- `template.html`: canvas-animatie (1080x1920). Modus via URL: geen parameter = story, `?reel=1` = reel, `?tiktok=1` = TikTok.
- `render.js`: rendert frames met headless Chrome. `PAGE=bestand.html node render.js stills 1,5,10` of `... video`. Zet `REEL=1` of `TT=1` voor de andere modi.
- `examples/`: Vietnam en Japan als voorbeeld.
- `music/`: achtergrondmuziek voor reel en TikTok.
