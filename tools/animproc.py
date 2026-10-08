#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 GIF 动画 / 横向精灵表切成序列帧，供 Canvas 逐帧播放。

用法：
  # GIF（自动抽帧，可选隔帧抽取）
  python tools/animproc.py _art/photo/爆炸.gif _art/out/boom anim_boom --size 72
  # 精灵表（必须给行列）
  python tools/animproc.py photo/spritesheets/flameball-32x32.png out/flame anim_flame \
      --cols 4 --rows 1 --size 32

产物：
  <out>/<name>_00.png ... <name>_NN.png   逐帧精灵（已抠背景/硬 alpha/量化/索引色）
  <out>/<name>.json                       帧数、单帧尺寸、抽帧信息
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageSequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spriteproc import (strip_background, drop_specks, trim_to_content,
                        hard_alpha, save_indexed, quantize)


def frames_from_gif(im, step):
    out = []
    for i, fr in enumerate(ImageSequence.Iterator(im)):
        if i % step:
            continue
        out.append(fr.convert('RGBA'))
    return out


def frames_from_sheet(im, cols, rows, step):
    """按等分网格切帧。GIF 靠 greatness"""
    w, h = im.size
    cw, ch = w // cols, h // rows
    out = []
    n = 0
    for r in range(rows):
        for c in range(cols):
            if n % step:
                n += 1
                continue
            out.append(im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)).convert('RGBA'))
            n += 1
    return out


def union_bbox(frames):
    """整个序列共用的内容窗口。

    关键：绝不能逐帧独立 trim 再拉伸 —— 各帧内容大小不同时，
    独立的归一化会让图案在画布里来回缩放跳 ("breathing")，动画直接废掉。
    统一窗口才能保证帧间位置关系稳定。
    """
    x0 = y0 = 1 << 30
    x1 = y1 = -1
    for f in frames:
        b = f.split()[-1].getbbox()
        if not b:
            continue
        x0 = min(x0, b[0]); y0 = min(y0, b[1])
        x1 = max(x1, b[2]); y1 = max(y1, b[3])
    if x1 < 0:
        return None
    return (x0, y0, x1, y1)


def process_frames(frames, dst_dir, name, size, colors, tol):
    """统一窗口裁剪 -> 等比缩放 -> 硬 alpha -> 量化 -> 索引色。"""
    os.makedirs(dst_dir, exist_ok=True)
    clean = [drop_specks(f) for f in frames]
    box = union_bbox(clean)
    if box is None:
        raise SystemExit('所有帧都是空的，检查一下源文件或背景阈值')

    bw, bh = box[2] - box[0], box[3] - box[1]
    # 保持内容宽高比，只限制长边 —— 方形化会在两侧留大片空白
    ow = size if bw >= bh else max(1, round(size * bw / bh))
    oh = size if bh >= bw else max(1, round(size * bh / bw))

    sizes = []
    for i, fr in enumerate(clean):
        img = fr.crop(box)
        img = img.resize((ow, oh), Image.BOX)
        img = hard_alpha(img)
        img = quantize(img, colors)
        p = os.path.join(dst_dir, '%s_%02d.png' % (name, i))
        save_indexed(img, p, colors)
        sizes.append(os.path.getsize(p))
    return sizes, (ow, oh), box


def fit_to_box(img, size):
    """等比缩放塞进 size×size。内容 box 在调用方统一处理时用得上。"""
    w, h = img.size
    if w == 0 or h == 0:
        return Image.new('RGBA', (size, size), (0, 0, 0, 0))
    s = max(w, h)
    canvas = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    canvas.paste(img, ((s - w) // 2, (s - h) // 2))
    return canvas.resize((size, size), Image.BOX)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('name')
    ap.add_argument('--size', type=int, default=72)
    ap.add_argument('--colors', type=int, default=20)
    ap.add_argument('--cols', type=int, default=0, help='精灵表列数（>0 时按网格切帧）')
    ap.add_argument('--rows', type=int, default=1)
    ap.add_argument('--step', type=int, default=1, help='隔 N 帧取一帧，用来降帧率/省体积')
    ap.add_argument('--tol', type=int, default=42)
    ap.add_argument('--order', default='',
                    help='重排帧序，逗号分隔。循环动画拆成一次性特效时用，'
                         '例：--order 8,9,10,11,12,13,14,15,16,0,1,2,3,4,5,6')
    ap.add_argument('--from-frame', type=int, default=0)
    ap.add_argument('--to-frame', type=int, default=-1)
    a = ap.parse_args()

    im = Image.open(a.src)
    if a.cols > 0:
        frames = frames_from_sheet(im.convert('RGBA'), a.cols, a.rows, a.step)
    else:
        frames = frames_from_gif(im, a.step)
    n = getattr(im, 'n_frames', 1)
    print('源: %s %s  共 %d 帧 -> 取 %d 帧' % (
        os.path.basename(a.src), im.size, n, len(frames)))

    if a.order:
        idx = [int(x) for x in a.order.split(',') if x.strip() != '']
        frames = [frames[i] for i in idx]
        print('重排帧序 -> %d 帧' % len(frames))
    elif a.to_frame >= 0:
        frames = frames[a.from_frame:a.to_frame + 1]
    elif a.from_frame:
        frames = frames[a.from_frame:]
    print('最终 %d 帧' % len(frames))

    sizes, (ow, oh), box = process_frames(frames, a.dst, a.name, a.size, a.colors, a.tol)

    man = {
        'name': a.name, 'w': ow, 'h': oh, 'frames': len(frames),
        'src': os.path.basename(a.src),
    }
    with open(os.path.join(a.dst, a.name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    total = sum(sizes)
    print('输出 %s_00..%02d.png  画布 %dx%d  %d 帧  %s KB' % (
        a.name, len(frames) - 1, ow, oh, len(frames), round(total / 1024, 1)))


if __name__ == '__main__':
    main()
