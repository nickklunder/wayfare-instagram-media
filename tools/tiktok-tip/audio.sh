#!/usr/bin/env bash
# Gebruik: ./audio.sh <stem-opname> <muziek> <totale-duur-sec> <uit.wav>
# "Podcast-klank" (akkoord Nick, 26-11-2026): warm, niet scherp, rustige stiltes.
# 1) stem opschonen, 2) vaste volumeaanpassing (geen dynamische loudnorm: die trekt ruis omhoog),
# 3) muziek op -30 LUFS met ducking, 4) eindmix op -14 LUFS.
set -e
VO="$1"; MUS="$2"; DUR="$3"; OUT="$4"; TMP=$(mktemp -d)
CH="pan=mono|c0=0.5*c0+0.5*c1,highpass=f=75:p=2,afftdn=nr=10:nf=-42,agate=threshold=0.03:ratio=3:range=0.2:attack=4:release=200:knee=4,lowshelf=f=140:g=2.5,equalizer=f=350:t=q:w=1:g=-2.5,equalizer=f=3200:t=q:w=1.2:g=-3,equalizer=f=6500:t=q:w=1.5:g=-2.5,highshelf=f=9000:g=-3,deesser=i=0.6:m=0.6:f=0.45,acompressor=threshold=-26dB:ratio=3:attack=15:release=220:knee=4:makeup=2,acompressor=threshold=-16dB:ratio=2:attack=5:release=80,lowpass=f=14000"
lufs(){ ffmpeg -hide_banner -i "$1" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}'; }
ffmpeg -v error -y -i "$VO" -af "$CH" -ar 48000 "$TMP/pre.wav"
G=$(python3 -c "print(round(-14-($(lufs "$TMP/pre.wav")),2))")
ffmpeg -v error -y -i "$TMP/pre.wav" -af "volume=${G}dB,alimiter=limit=0.89:level=false" "$TMP/vo.wav"
ffmpeg -v error -y -i "$MUS" -t $(echo "$DUR+1" | bc) -af "loudnorm=I=-30:TP=-6,lowpass=f=12000" -ar 48000 "$TMP/m.wav"
FO=$(echo "$DUR-1.5" | bc)
ffmpeg -v error -y -i "$TMP/m.wav" -af "atrim=0:$DUR,afade=t=in:st=0:d=0.8,afade=t=out:st=$FO:d=1.5" "$TMP/bed.wav"
ffmpeg -v error -y -i "$TMP/vo.wav" -i "$TMP/bed.wav" -filter_complex "[0:a]aformat=channel_layouts=mono,apad=pad_dur=5,atrim=0:$DUR,asplit=2[vo][sc];[1:a][sc]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=400[md];[vo]pan=stereo|c0=c0|c1=c0[vs];[vs][md]amix=inputs=2:duration=first:normalize=0[a]" -map "[a]" "$TMP/mix.wav"
G2=$(python3 -c "print(round(-14-($(lufs "$TMP/mix.wav")),2))")
ffmpeg -v error -y -i "$TMP/mix.wav" -af "volume=${G2}dB,alimiter=limit=0.89:level=false" "$OUT"
rm -rf "$TMP"
