"""複数の写真を横に並べた1枚の画像を作る。

使い方:
  python3 -I make_panels.py <出力.jpg> <画像1>[:x0,y0,x1,y1] <画像2>[:...] ...

- 各画像は「:x0,y0,x1,y1」で切り抜き範囲を指定できる（元画像のピクセル座標）。
  省略すると、縦横比 2:3 になるよう中央を切り抜く。
- 1コマは 326x500、コマの間は 10px の白。3コマで 998x500 になる。
"""
import sys
from PIL import Image

W, H, GAP = 326, 500, 10


def center_crop(im):
    w, h = im.size
    target = W / H
    if w / h > target:
        nw = int(h * target)
        x0 = (w - nw) // 2
        return im.crop((x0, 0, x0 + nw, h))
    nh = int(w / target)
    y0 = (h - nh) // 2
    return im.crop((0, y0, w, y0 + nh))


def load(spec):
    path, _, box = spec.partition(":")
    im = Image.open(path).convert("RGB")
    if box:
        return im.crop(tuple(int(v) for v in box.split(",")))
    return center_crop(im)


def main():
    out, *specs = sys.argv[1:]
    if not specs:
        sys.exit(__doc__)
    panels = [load(s) for s in specs]
    canvas = Image.new("RGB", (W * len(panels) + GAP * (len(panels) - 1), H), "white")
    for i, p in enumerate(panels):
        canvas.paste(p.resize((W, H), Image.LANCZOS), (i * (W + GAP), 0))
    canvas.save(out, "JPEG", quality=85)
    print(out, canvas.size)


if __name__ == "__main__":
    main()
