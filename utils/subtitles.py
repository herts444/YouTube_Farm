import re
from math import floor

def split_into_sentences(text: str):
    # грубая разбивка на предложения
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    parts = [p for p in parts if p]
    return parts if parts else [text]

def _fmt(t: float) -> str:
    ms = int(round((t - int(t)) * 1000))
    s = int(t) % 60
    m = (int(t) // 60) % 60
    h = int(t) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def build_srt_by_text_length(text: str, total_duration: float, out_path: str):
    """
    Эвристика: делим по предложениям и распределяем время пропорционально длине.
    Это не forced alignment, но даёт аккуратные сабы на MVP.
    """
    sentences = split_into_sentences(text)
    lengths = [max(len(s), 10) for s in sentences]
    total_len = sum(lengths)
    alloc = [total_duration * (l / total_len) for l in lengths]

    # минимальная длительность суба
    alloc = [max(a, 1.2) for a in alloc]

    # нормализация до total_duration
    scale = total_duration / sum(alloc)
    alloc = [a * scale for a in alloc]

    cur = 0.0
    lines = []
    for i, (s, d) in enumerate(zip(sentences, alloc), 1):
        start = cur
        end = cur + d
        cur = end
        lines.append(f"{i}\n{_fmt(start)} --> { _fmt(end)}\n{s}\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
