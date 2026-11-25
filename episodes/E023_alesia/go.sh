set -e
H=814
( python3 render_al.py seg 0 $H | ffmpeg -loglevel error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p p1.mp4 ) &
( python3 render_al.py seg $H 1628 | ffmpeg -loglevel error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p p2.mp4 ) &
wait
printf "file p1.mp4\nfile p2.mp4\n" > parts.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i parts.txt -c copy video.mp4
ffmpeg -loglevel error -y -i mix_raw.wav -af "volume=+5.8dB,alimiter=limit=0.70:level=false" -ar 48000 pre.wav
ffmpeg -loglevel error -y -i video.mp4 -i pre.wav -af "volume=0.9dB,alimiter=limit=0.70:level=false" -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest E023_alesia.mp4
