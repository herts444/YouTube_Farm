import asyncio
import json
import os
from typing import Dict, Optional, Tuple

from utils.config import FFMPEG_BIN, FFPROBE_BIN

class FFmpegError(RuntimeError):
    def __init__(self, cmd: str, log: str):
        super().__init__(f"FFmpeg/FFprobe failed. CMD: {' '.join(cmd)}\nLOG:\n{log[:6000]}")
        self.cmd = cmd
        self.log = log

async def _run(*cmd: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    out_b, _ = await proc.communicate()
    out = (out_b or b"").decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise FFmpegError(cmd=" ".join(cmd), log=out)
    return out

# ---------- ПРОБЫ/ИНФО ----------
async def probe_duration(path: str) -> float:
    out = await _run(
        FFPROBE_BIN, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", path
    )
    data = json.loads(out)
    try:
        return float(data["format"]["duration"])
    except Exception:
        return 0.0

# ---------- АУДИО ----------
async def loudness_normalize(in_audio: str, out_audio: str, target_i: float = -14.0):
    await _run(
        FFMPEG_BIN, "-y",
        "-i", in_audio,
        "-af", f"loudnorm=I={target_i}:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "2",
        out_audio
    )

# ---------- СУБТИТРЫ/МУКС ----------
async def mux_av_with_optional_subs(
    video_path: str,
    audio_path: str,
    srt_path: Optional[str],
    out_path: str,
    metadata: Optional[Dict[str, str]] = None
) -> Tuple[bool, str]:
    # Оптимизация: используем stream copy для видео (без повторного кодирования)
    # Это в 10-20 раз быстрее чем перекодирование
    cmd = [FFMPEG_BIN, "-y", "-threads", "0", "-i", video_path, "-i", audio_path]

    map_args = ["-map", "0:v:0", "-map", "1:a:0"]
    meta_args = []
    if metadata:
        for k, v in metadata.items():
            meta_args += ["-metadata", f"{k}={v}"]

    subs_included = False
    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        cmd += ["-i", srt_path]
        map_args += ["-map", "2:s:0"]
        subs_included = True

    cmd += map_args
    cmd += [
        "-c:v", "copy",  # Stream copy - НЕ перекодируем видео (огромная экономия времени)
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-movflags", "+faststart",
    ]
    if subs_included:
        cmd += ["-c:s", "mov_text"]

    if meta_args:
        cmd += meta_args

    cmd += [out_path]
    await _run(*cmd)
    return subs_included, out_path

# ---------- ОВЕРЛЕЙ ----------
async def overlay_alpha(bg_video: str, fg_alpha_video: str, out_path: str):
    await _run(
        FFMPEG_BIN, "-y",
        "-i", bg_video, "-i", fg_alpha_video,
        "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_path
    )

# ---------- ТГ ЛИМИТ ----------
async def ensure_telegram_size(input_path: str, output_path: str, target_mb: int = 48) -> str:
    size_mb = os.path.getsize(input_path) / (1024 * 1024)
    if size_mb <= target_mb:
        return input_path

    # Оптимизация: ultrafast preset + threads для максимальной скорости
    await _run(
        FFMPEG_BIN, "-y",
        "-threads", "0",
        "-i", input_path,
        "-vf", "scale=1080:1920:flags=fast_bilinear:force_original_aspect_ratio=decrease,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "33",
        "-maxrate", "1.2M", "-bufsize", "2.4M",
        "-c:a", "aac", "-b:a", "96k", "-ar", "48000",
        "-movflags", "+faststart",
        output_path
    )
    return output_path
