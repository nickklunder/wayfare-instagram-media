#!/usr/bin/env bash
# WayFare Film: vaste filmlook voor alle beelden (stock, eigen, AI).
#
# Gebruik:
#   ./filmlook.sh <in.mp4> <uit.mp4> [opties]
#
# Opties:
#   --ai          AI-beeld: iets zachter en extra korrel (oogt minder "plastic")
#   --ss <sec>    begin bij deze seconde
#   --t <sec>     duur van het stuk
#   --x <0-1>     bij liggend beeld: waar de 9:16-uitsnede staat (0 = links, 0.5 = midden, 1 = rechts)
#   --zoom <f>    extra inzoomen (bijv. 1.1), handig om randen of UI weg te snijden
#   --y <0-1>     verticale positie bij --zoom (standaard 0.5)
#   --exp <f>     belichting bijstellen, bijv. 0.04 (lichter) of -0.04 (donkerder)
#   --landscape   uitvoer 1920x1080 in plaats van 1080x1920
#
# Wat het doet, in deze volgorde:
#   1. HDR (HLG/PQ van iPhone) netjes omzetten naar normaal beeld
#   2. naar 30 fps (24 fps wordt vloeiend omgerekend, geen schokken)
#   3. uitsnede naar 9:16 op bronresolutie, dan schalen naar 1080x1920
#   4. de kleur-LUT wayfare-film.cube (diep groen in de schaduw, warm crème/goud in het licht,
#      zachte zwarten, rustiger groen en blauw)
#   5. halation (warme gloed rond felle lichten), zachte vignet, filmkorrel
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
LUT="$HERE/wayfare-film.cube"
IN="$1"; OUT="$2"; shift 2
AI=0; SS=""; T=""; XPOS=0.5; ZOOM=1; YPOS=0.5; EXP=0; W=1080; H=1920
while [ $# -gt 0 ]; do
  case "$1" in
    --ai) AI=1;;
    --ss) SS="$2"; shift;;
    --t) T="$2"; shift;;
    --x) XPOS="$2"; shift;;
    --zoom) ZOOM="$2"; shift;;
    --y) YPOS="$2"; shift;;
    --exp) EXP="$2"; shift;;
    --landscape) W=1920; H=1080;;
  esac; shift
done

read SW SH TRC FPS <<<"$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,color_transfer,r_frame_rate -of csv=p=0 "$IN" | tr ',' ' ')"
FPSN=$(python3 -c "print(round(eval('$FPS'),3))")

F=""
# 1. HDR -> SDR
if [ "$TRC" = "arib-std-b67" ] || [ "$TRC" = "smpte2084" ]; then
  F+="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:param=0.35:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
fi
# 2. fps
F+="setpts=PTS-STARTPTS,"
if python3 -c "import sys; sys.exit(0 if abs($FPSN-30)<0.2 or abs($FPSN-29.97)<0.2 else 1)"; then
  F+="fps=30,"
elif python3 -c "import sys; sys.exit(0 if $FPSN>=50 else 1)"; then
  F+="fps=30,"
else
  F+="minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
fi
# 3. uitsnede (op bronresolutie) + schalen
read CW CH CX CY <<<"$(python3 - <<PY
sw,sh,W,H=$SW,$SH,$W,$H
z=$ZOOM; xp=$XPOS; yp=$YPOS
ar=W/H
if sw/sh>ar: ch=sh; cw=round(sh*ar)
else: cw=sw; ch=round(sw/ar)
cw=int(cw/z)//2*2; ch=int(ch/z)//2*2
cx=int((sw-cw)*xp)//2*2; cy=int((sh-ch)*yp)//2*2
print(cw,ch,cx,cy)
PY
)"
F+="crop=$CW:$CH:$CX:$CY,scale=$W:$H:flags=lanczos,setsar=1,"
# AI: iets zachter
if [ $AI = 1 ]; then F+="gblur=sigma=0.6,"; fi
# belichting
if [ "$EXP" != "0" ]; then F+="eq=brightness=$EXP,"; fi
# 4. LUT
F+="format=gbrp,lut3d=file='$LUT':interp=tetrahedral,"
# 5. halation + vignet + korrel
GR=6; [ $AI = 1 ] && GR=9
F+="split[a][b];[b]curves=all='0/0 0.72/0 1/1',gblur=sigma=22,colorchannelmixer=rr=1:gg=0.45:bb=0.2[h];[a][h]blend=all_mode=screen:all_opacity=0.22,"
F+="vignette=angle=PI/6.5:mode=forward,format=yuv420p,noise=c0s=$GR:c0f=t+u:c1s=2:c1f=t:c2s=2:c2f=t"

ARGS=()
[ -n "$SS" ] && ARGS+=(-ss "$SS")
ARGS+=(-i "$IN")
[ -n "$T" ] && ARGS+=(-t "$T")
ffmpeg -v error -y "${ARGS[@]}" -filter_complex "[0:v]$F[v]" -map "[v]" -an -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "$OUT"
echo "klaar: $OUT"
