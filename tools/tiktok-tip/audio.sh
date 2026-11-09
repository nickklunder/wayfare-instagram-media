#!/usr/bin/env bash
# Gebruik: ./audio.sh <stem-opname> <muziek> <totale-duur-sec> <uit.wav>
# 1) stem opschonen (studio-klank), 2) muziek op -30 LUFS, 3) ducking onder de stem.
set -e
VO="$1"; MUS="$2"; DUR="$3"; OUT="$4"; TMP=$(mktemp -d)
ffmpeg -v error -y -i "$VO" -af "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=12:nf=-46:tn=1,equalizer=f=250:t=q:w=1.2:g=-3,equalizer=f=4000:t=q:w=1.5:g=2.5,equalizer=f=11000:t=h:w=0.7:g=2,deesser=i=0.4,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=3,alimiter=limit=0.89,loudnorm=I=-14:TP=-1.5:LRA=9" -ar 48000 "$TMP/vo.wav"
ffmpeg -v error -y -i "$MUS" -t $(echo "$DUR+1" | bc) -af "loudnorm=I=-30:TP=-6" -ar 48000 "$TMP/m.wav"
FO=$(echo "$DUR-1.5" | bc)
ffmpeg -v error -y -i "$TMP/m.wav" -af "atrim=0:$DUR,afade=t=in:st=0:d=0.8,afade=t=out:st=$FO:d=1.5" "$TMP/bed.wav"
ffmpeg -v error -y -i "$TMP/vo.wav" -i "$TMP/bed.wav" -filter_complex "[0:a]apad=pad_dur=5,atrim=0:$DUR,asplit=2[vo][sc];[1:a][sc]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=400[md];[vo][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]" -map "[a]" "$OUT"
rm -rf "$TMP"
