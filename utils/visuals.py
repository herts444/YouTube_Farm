import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
from utils.config import FONT_PATH
from utils.ffmpeg import _run  # строгий раннер

def make_background_image(seed_text: str, out_path: str, size=(1080, 1920)):
    """Генерит простой абстрактный фон: градиент + шум. Без водяного знака-текста."""
    w, h = size
    img = Image.new("RGB", (w, h), color=(10, 10, 18))
    draw = ImageDraw.Draw(img)

    # градиент
    for y in range(h):
        r = int(10 + (y / h) * 30)
        g = int(10 + (y / h) * 10)
        b = int(18 + (y / h) * 40)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # шумовые пятна
    for _ in range(80):
        x0 = random.randint(0, w)
        y0 = random.randint(0, h)
        rad = random.randint(30, 200)
        color = (random.randint(40, 80), random.randint(40, 80), random.randint(90, 140))
        draw.ellipse((x0 - rad, y0 - rad, x0 + rad, y0 + rad), fill=color)

    img = img.filter(ImageFilter.GaussianBlur(4))

    # РАНЬШЕ: здесь рисовали полупрозрачный текст (водяной знак) по seed_text.
    # УДАЛЕНО, чтобы не дублировать субтитры по нижнему краю.

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")

async def make_animated_video(img_path: str, out_path: str, duration: float):
    """
    Делает 1080x1920 30fps видео из картинки с лёгким Ken-Burns.
    Используем общий раннер _run() — при ошибке ffmpeg упадёт с понятным логом.
    """
    vf = (
        "scale=1080:1920,"
        "zoompan="
        "z='min(zoom+0.0006,1.08)':"
        "s=1080x1920:"
        "d=1:"
        "fps=30,"
        "format=yuv420p"
    )

    # локальный импорт, чтобы избежать циклических зависимостей
    from utils.config import FFMPEG_BIN

    await _run(
        FFMPEG_BIN, "-y",
        "-loop", "1", "-i", img_path,
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_path
    )
