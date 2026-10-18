"""Generates a multi-resolution assets/icon.ico.

Source selection:
  1. If assets/icon.ico is an image that is NOT a real ICO (a dropped-in
     PNG/JPEG), that image is used and saved to assets/icon_source.png.
  2. Otherwise assets/icon_source.png is used if present.
  3. Otherwise a default white square with a black "C" is drawn.
"""

import os
import struct
import sys
import tempfile

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication

SIZES = (16, 24, 32, 48, 64, 128, 256)


def root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_valid_ico(path):
    try:
        with open(path, "rb") as handle:
            head = handle.read(6)
    except OSError:
        return False
    if len(head) < 6 or head[:4] != b"\x00\x00\x01\x00":
        return False
    return struct.unpack("<H", head[4:6])[0] > 0


def load_source(assets):
    ico = os.path.join(assets, "icon.ico")
    src_png = os.path.join(assets, "icon_source.png")

    if os.path.isfile(ico) and not is_valid_ico(ico):
        image = QImage(ico)
        if not image.isNull():
            image.save(src_png, "PNG")
            print("captured dropped-in artwork ->", src_png)
            return image

    if os.path.isfile(src_png):
        image = QImage(src_png)
        if not image.isNull():
            return image

    return None


def render_from_source(src, size):
    scaled = src.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    canvas = QImage(size, size, QImage.Format_ARGB32)
    canvas.fill(QColor(0, 0, 0, 0))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.drawImage((size - scaled.width()) // 2, (size - scaled.height()) // 2, scaled)
    painter.end()
    return canvas


def render_default(size):
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(QColor("transparent"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)

    inset = max(1, round(size * 18 / 256))
    radius = round(size * 36 / 256)
    stroke = max(1, round(size * 18 / 256))

    painter.setBrush(QColor("#FFFFFF"))
    border = QPen(QColor("#000000"))
    border.setWidth(stroke)
    border.setJoinStyle(Qt.RoundJoin)
    painter.setPen(border)
    painter.drawRoundedRect(
        QRectF(inset, inset, size - 2 * inset, size - 2 * inset), radius, radius
    )

    painter.setPen(QColor("#000000"))
    font = QFont("Arial")
    font.setBold(True)
    font.setPixelSize(max(6, int(size * 0.56)))
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignCenter, "C")

    painter.end()
    return image


def image_to_png(image):
    # QImage.save() into a QBuffer crashes on Windows, so use a temp file.
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        image.save(tmp_path, "PNG")
        with open(tmp_path, "rb") as handle:
            return handle.read()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def image_to_dib(image):
    """Encode a QImage as a 32bpp BMP (DIB) frame for an ICO.

    Windows Explorer is unreliable with PNG-compressed frames smaller than
    256px, so small frames are stored as uncompressed DIBs instead.
    """
    img = image.convertToFormat(QImage.Format_ARGB32)
    width, height = img.width(), img.height()
    bytes_per_line = img.bytesPerLine()
    raw = img.constBits().tobytes()

    header = struct.pack(
        "<IiiHHIIiiII", 40, width, height * 2, 1, 32, 0, 0, 0, 0, 0, 0
    )

    pixels = bytearray()
    for y in range(height - 1, -1, -1):
        start = y * bytes_per_line
        pixels += raw[start:start + width * 4]

    # 1bpp AND mask, one row per scanline, padded to 4-byte boundaries.
    mask_row = ((width + 31) // 32) * 4
    mask = b"\x00" * (mask_row * height)

    return header + bytes(pixels) + mask


def write_ico(path, images):
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    entries = b""
    data = b""
    for size, png in images:
        dim = 0 if size >= 256 else size
        entries += struct.pack(
            "<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset + len(data)
        )
        data += png
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(entries)
        handle.write(data)


def main():
    app = QApplication(sys.argv)  # noqa: F841 - required for QImage/QPainter
    assets = os.path.join(root_dir(), "assets")
    os.makedirs(assets, exist_ok=True)
    out = os.path.join(assets, "icon.ico")

    source = load_source(assets)
    if source is not None:
        print("source image:", source.width(), "x", source.height())
        frames = [(size, render_from_source(source, size)) for size in SIZES]
    else:
        print("no source image found; drawing default 'C' icon")
        frames = [(size, render_default(size)) for size in SIZES]

    # DIB frames for small sizes (Explorer-safe), PNG for the 256 frame.
    images = [
        (size, image_to_png(frame) if size >= 256 else image_to_dib(frame))
        for size, frame in frames
    ]

    write_ico(out, images)
    print("wrote", out, "sizes:", [size for size, _ in images])


if __name__ == "__main__":
    main()
