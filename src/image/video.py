# -*- coding: utf-8 -*-
"""
Gera um Reel (MP4 9:16) a partir de um frame estatico do story.
Movimento: push-in suave (Ken Burns) + fade-in. Audio silencioso.
Saida compativel com Instagram Reels: H.264, yuv420p, +faststart.
"""
import subprocess
import numpy as np

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

W, H = 1080, 1920


def gerar_reel(frame, saida="reel.mp4", dur=7.0, fps=30, zoom=0.07, musica=None):
    """frame: PIL 1080x1920. Gera MP4 com push-in suave + fade-in.
    musica: caminho de um arquivo de audio pra trilha (loop + fade-out). None = silencio."""
    frame = frame.convert("RGB").resize((W, H))
    base = np.asarray(frame)
    n = int(dur * fps)
    if musica:
        audio_in = ["-stream_loop", "-1", "-i", musica]
        audio_tail = ["-map", "0:v:0", "-map", "1:a:0",
                      "-af", f"afade=t=out:st={max(0.0, dur-1.2):.2f}:d=1.2,volume=0.85",
                      "-c:a", "aac", "-b:a", "128k"]
    else:
        audio_in = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        audio_tail = ["-c:a", "aac", "-b:a", "96k"]
    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           *audio_in, "-t", str(dur), "-c:v", "libx264", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           *audio_tail, "-shortest", saida]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    from PIL import Image
    fimg = Image.fromarray(base)
    for i in range(n):
        t = i / max(1, n - 1)
        s = 1.0 + zoom * t                       # push-in
        nw, nh = int(W * s), int(H * s)
        big = fimg.resize((nw, nh), Image.LANCZOS)
        x = (nw - W) // 2; y = (nh - H) // 2
        crop = big.crop((x, y, x + W, y + H))
        proc.stdin.write(np.asarray(crop).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()
    return saida
