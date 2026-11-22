set -e
H=818
( python3 render_sc.py seg 0 $H | ffmpeg -loglevel error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p p1.mp4 ) &
( python3 render_sc.py seg $H 1636 | ffmpeg -loglevel error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p p2.mp4 ) &
wait
printf "file p1.mp4\nfile p2.mp4\n" > parts.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i parts.txt -c copy video.mp4
ffmpeg -loglevel error -y -i video.mp4 -i mix_raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000 -c:v copy -c:a aac -b:a 192k -shortest E021_scorpio.mp4
echo done
