"""Generate PWA PNG and favicon.ico from brand colors."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "app" / "static" / "icons"
IMG_DIR = ROOT / "app" / "static" / "img"


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (6, 6, 11, 255))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = int(size * 0.375)
    pad = int(size * 0.06)

    for i in range(3):
        gr = r + pad + i * 2
        alpha = 30 - i * 8
        d.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=(99, 102, 241, alpha))

    lw = max(1, size // 96)
    d.ellipse([cx - r - pad, cy - r - pad, cx + r + pad, cy + r + pad], outline=(99, 102, 241, 140), width=lw)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(129, 140, 248, 100), width=max(1, size // 128))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(129, 140, 248, 90), width=max(1, size // 106))
    d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=(99, 102, 241, 70), width=max(1, size // 137))
    d.line([cx - r, cy, cx + r, cy], fill=(99, 102, 241, 50), width=max(1, size // 160))
    d.line([cx, cy - r, cx, cy + r], fill=(99, 102, 241, 50), width=max(1, size // 160))

    node_r = max(2, size // 48)
    rays = [
        (cx, cy - r - pad * 2),
        (cx + r + pad, cy - r // 2),
        (cx + r + pad * 2, cy),
        (cx - r - pad * 2, cy),
        (cx - r - pad, cy - r // 2),
    ]
    colors = [
        (6, 182, 212, 230),
        (129, 140, 248, 180),
        (99, 102, 241, 180),
        (99, 102, 241, 180),
        (129, 140, 248, 180),
    ]
    for (x, y), col in zip(rays, colors):
        d.ellipse([x - node_r, y - node_r, x + node_r, y + node_r], fill=col)

    s = size / 120
    bolt = [(64 * s, 44 * s), (52 * s, 62 * s), (58 * s, 62 * s), (56 * s, 76 * s), (72 * s, 54 * s), (66 * s, 54 * s)]
    bx, by = cx - 60 * s, cy - 60 * s
    bolt = [(x + bx, y + by) for x, y in bolt]
    d.polygon(bolt, fill=(99, 102, 241, 255))
    d.polygon(bolt, outline=(6, 182, 212, 120))
    return img


def main() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    for sz in (192, 512):
        img = draw_icon(sz)
        name = f"icon-{sz}.png"
        img.save(ICON_DIR / name, "PNG")
        img.save(IMG_DIR / name, "PNG")
        print(f"Wrote {name}")

    ico = draw_icon(32)
    ico.save(IMG_DIR / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32)])
    print("Wrote favicon.ico")


if __name__ == "__main__":
    main()
