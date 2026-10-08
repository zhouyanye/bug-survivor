#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 AI 生成的大图裁成"真正的像素精灵"。

流程：
  读图 → 去背景（若 alpha 未生效则用边缘连通域抠图）
       → 按 alpha 裁剪到内容边界
       → BOX 降采样到目标尺寸（得到干净的像素块）
       → 色板量化到固定色数（保证整套精灵"有限色板"观感一致）
       → 输出 PNG

用法：
  python spriteproc.py <输入目录> <输出目录> [--size 48] [--colors 24] [--all]
不带 --all 时，只处理 spec 里显式列出的文件映射。
"""
import argparse
import os
import sys
from collections import deque

from PIL import Image


# ---------------------------------------------------------------- 去背景
def strip_background(img, tol=42):
    """如果图片没有透明通道（或四角不透明），用边缘连通域把背景抠掉。"""
    img = img.convert('RGBA')
    w, h = img.size
    px = img.load()

    # 已经透明就直接用
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    if all(c[3] < 16 for c in corners):
        return img

    # 背景色 = 出现频率最高的颜色（比四角平均鲁棒：主体居中时四角一定为背景，
    # 但出现渐变/边框时四角会骗人；众数色才是真正的底色）
    small0 = img.resize((64, 64), Image.BOX).convert('RGB')
    counts = {}
    for c in small0.get_flattened_data():
        key = (c[0] >> 3, c[1] >> 3, c[2] >> 3)
        counts[key] = counts.get(key, 0) + 1
    top = max(counts.items(), key=lambda kv: kv[1])[0]
    bg = tuple(v * 8 + 4 for v in top)

    # 从四条边出发 BFS，只吞掉与背景色接近的连通区域
    # 先缩小到 256 工作分辨率，避免 1024x1024 的 BFS 太慢
    work = 256
    if max(w, h) > work:
        small = img.resize((work, work), Image.BOX).convert('RGBA')
    else:
        small = img.convert('RGBA')
    sw, sh = small.size
    sp = small.load()
    mask = [[False] * sh for _ in range(sw)]
    q = deque()
    for x in range(sw):
        for y in (0, sh - 1):
            if not mask[x][y]:
                mask[x][y] = True
                q.append((x, y))
    for y in range(sh):
        for x in (0, sw - 1):
            if not mask[x][y]:
                mask[x][y] = True
                q.append((x, y))

    def near(c):
        return (abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2])) < tol * 3

    while q:
        x, y = q.popleft()
        if not near(sp[x, y]):
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < sw and 0 <= ny < sh and not mask[nx][ny]:
                mask[nx][ny] = True
                q.append((nx, ny))

    out = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    op = out.load()
    for x in range(sw):
        for y in range(sh):
            c = sp[x, y]
            op[x, y] = c if not (mask[x][y] and near(c)) else (0, 0, 0, 0)
    return out.resize((w, h), Image.NEAREST)


def drop_specks(img, min_ratio=0.004):
    """删掉小连通域 —— AI 抠图后角落常留几粒噪点，会把 bbox 撑满整张图。"""
    w, h = img.size
    a = img.split()[-1].load()
    seen = [[False] * h for _ in range(w)]
    keep = [[False] * h for _ in range(w)]
    min_area = max(4, int(w * h * min_ratio))
    for x in range(w):
        for y in range(h):
            if a[x, y] < 16 or seen[x][y]:
                continue
            comp = []
            q = deque([(x, y)])
            seen[x][y] = True
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny] and a[nx, ny] >= 16:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            if len(comp) >= min_area:
                for cx, cy in comp:
                    keep[cx][cy] = True
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    op = out.load()
    src = img.load()
    for x in range(w):
        for y in range(h):
            if keep[x][y]:
                op[x, y] = src[x, y]
    return out


def trim_to_content(img, pad=2):
    """按 alpha 裁剪到内容边界，并留一点边距。"""
    bbox = img.split()[-1].getbbox()
    if not bbox:
        return img
    w, h = img.size
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(w, x1 + pad); y1 = min(h, y1 + pad)
    return img.crop((x0, y0, x1, y1))


def fit_square(img, size):
    """等比缩放并居中放进 size×size 的方形画布。"""
    w, h = img.size
    s = max(w, h)
    canvas = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    canvas.paste(img, ((s - w) // 2, (s - h) // 2))
    return canvas.resize((size, size), Image.BOX)


def hard_alpha(img, thresh=110):
    """把半透明边缘二值化 —— 抗锯齿的半透明像素是"假像素"的元凶。"""
    rgba = img.convert('RGBA')
    a = rgba.split()[-1].point(lambda v: 255 if v >= thresh else 0)
    rgba.putalpha(a)
    return rgba


def add_outline(img, color=(16, 16, 24, 255)):
    """给不透明区域外缘补一圈 1px 深色描边，让精灵在任何背景上都立得住。"""
    w, h = img.size
    a = img.split()[-1].load()
    out = img.copy()
    op = out.load()
    solid = [[a[x, y] > 128 for y in range(h)] for x in range(w)]
    for x in range(w):
        for y in range(h):
            if solid[x][y]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and solid[nx][ny]:
                    op[x, y] = color
                    break
    return out


def quantize(img, colors):
    """量化到固定色数，同时保住 alpha。"""
    rgba = img.convert('RGBA')
    alpha = rgba.split()[-1]
    rgb = rgba.convert('RGB')
    q = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
    q = q.convert('RGB')
    q.putalpha(alpha)
    return q


def save_indexed(img, path, colors):
    """存成索引色 PNG（索引 0 = 透明）。

    同样内容比 RGBA PNG 小 3~5 倍 —— 单文件游戏里这些图要 base64 内嵌，
    体积直接等于 HTML 体积，值得抠。
    """
    rgba = img.convert('RGBA')
    w, h = rgba.size
    a = rgba.split()[-1].load()

    # 透明区域压成黑色，避免它们的杂色抢占调色板色位
    flat = Image.new('RGB', (w, h), (0, 0, 0))
    fp = flat.load()
    rp = rgba.load()
    for y in range(h):
        for x in range(w):
            if a[x, y] >= 128:
                fp[x, y] = (rp[x, y][0], rp[x, y][1], rp[x, y][2])

    q = flat.quantize(colors=max(2, colors - 1), method=Image.MEDIANCUT,
                      dither=Image.NONE)
    pal = q.getpalette()
    qd = list(q.get_flattened_data())

    newpal = [0, 0, 0]          # 索引 0 = 透明
    for i in range(max(2, colors - 1)):
        newpal += pal[i * 3:i * 3 + 3]
    newpal += [0, 0, 0] * (256 - colors)

    out = Image.new('P', (w, h))
    out.putpalette(newpal)
    out.putdata([0 if a[x, y] < 128 else v + 1
                 for y in range(h) for x in range(w) for v in [qd[y * w + x]]])
    out.save(path, optimize=True, transparency=0)


def seam_diff(img):
    """无缝性检查：比较左右边缘、上下边缘的像素差。

    返回平均通道差（0~255）。< 25 基本看不出缝，> 45 平铺会有明显格子印。
    """
    rgb = img.convert('RGB')
    w, h = rgb.size
    p = rgb.load()
    def avg(i0, i1):
        s = n = 0
        for i in i0:
            for j in i1:
                pass
        return s, n
    # 左右边缘
    dl = sum(abs(p[0, y][c] - p[w - 1, y][c]) for y in range(h) for c in range(3)) / (h * 3)
    # 上下边缘
    dt = sum(abs(p[x, 0][c] - p[x, h - 1][c]) for x in range(w) for c in range(3)) / (w * 3)
    return dl, dt


def make_tileable(img, blend=0.12):
    """把非无缝的图改成无缝：四边各切掉一点，用镜像过渡带把接缝藏进图案里。

    做法是把边缘 blend 比例的区域与对边做交叉淡化。背景纹理上这点过渡肉眼无感，
    但比平铺出一道十字缝强得多。
    """
    img = img.convert('RGB')
    w, h = img.size
    bw = max(2, int(min(w, h) * blend))
    p = img.load()
    for y in range(h):
        for i in range(bw):
            t = (i + 1) / (bw + 1)                      # 0→1 从左接缝向右
            a = p[i, y]; b = p[w - bw + i, y]           # 左 band 与右 band 混合
            # 用右边的颜色去补左边的缝，权重随距离衰减
            img.putpixel((i, y), tuple(
                int(a[c] * (1 - t) + b[c] * t) for c in range(3)))
    for x in range(w):
        for i in range(bw):
            t = (i + 1) / (bw + 1)
            a = p[x, i]; b = p[x, h - bw + i]
            img.putpixel((x, i), tuple(
                int(a[c] * (1 - t) + b[c] * t) for c in range(3)))
    return img


def to_gray_tintable(img, gamma=0.55):
    """转成灰度图，供运行时用 multiply 给任意武器上色。

    一张灰图适配所有颜色，比给每把武器单独生成一张划算得多。
    要求：外轮廓够暗（multiply 后是武器的暗部）、核心够亮（multiply 后接近纯武器色）。
    """
    alpha = img.split()[-1]
    g = img.convert('RGB').convert('L')
    # 只按不透明区域统计，否则大片透明会把直方图拉偏
    vals = [g.getpixel((x, y)) for y in range(0, g.size[1], 2)
            for x in range(0, g.size[0], 2) if alpha.getpixel((x, y)) >= 128]
    if vals:
        lo, hi = min(vals), max(vals)
        if hi - lo > 8:
            g = g.point(lambda v: max(0, min(255, int((v - lo) * 255 / (hi - lo)))))
    # gamma < 1 提亮中间调：multiply 上色后才不会整体发暗
    g = g.point(lambda v: min(255, int(255 * ((v / 255.0) ** gamma))))
    out = Image.merge('RGB', (g, g, g))
    out.putalpha(hard_alpha(img).split()[-1])
    return out


def process(src, dst, size, colors, tol=42, outline=True, tile=False,
            fix_seam=False, seam_max=30, gray=False, gamma=0.55):
    if tile:
        # 背景砖：不抠图、不描边，只做降采样 + 量化 +  Possibly 无缝修复
        img = Image.open(src).convert('RGB')
        img = img.resize((size, size), Image.BOX)
        if fix_seam:
            dl, dt = seam_diff(img)
            if max(dl, dt) > seam_max:
                img = make_tileable(img)
                dl, dt = seam_diff(img)
                print('    已做无缝修复 -> 左右差 %.1f 上下差 %.1f' % (dl, dt))
            else:
                print('    本身够无缝（左右差 %.1f 上下差 %.1f），未处理' % (dl, dt))
        else:
            dl, dt = seam_diff(img)
            print('    接缝检查：左右差 %.1f 上下差 %.1f' % (dl, dt))
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        # 存索引色（无透明），比 RGBA 小 2/3
        img.convert('RGB').quantize(colors=colors, method=Image.MEDIANCUT,
                                    dither=Image.NONE).save(dst, optimize=True)
        return dst

    img = Image.open(src)
    img = strip_background(img, tol)
    img = drop_specks(img)
    img = trim_to_content(img)
    img = fit_square(img, size)
    img = hard_alpha(img)
    if gray:
        img = to_gray_tintable(img, gamma)
    if outline:
        img = add_outline(img)
    img = quantize(img, colors)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    save_indexed(img, dst, colors)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--size', type=int, default=48)
    ap.add_argument('--colors', type=int, default=24)
    ap.add_argument('--tol', type=int, default=42)
    ap.add_argument('--map', default='', help='形如 原名=新名,原名=新名')
    ap.add_argument('--tile', action='store_true', help='背景砖模式：不抠图不描边')
    ap.add_argument('--fix-seam', action='store_true', help='接缝超阈值时自动修复')
    ap.add_argument('--gray', action='store_true', help='转灰度，供运行时 multiply 上色')
    ap.add_argument('--gamma', type=float, default=0.55,
                    help='灰度提亮曲线，越小越亮（默认 0.55）')
    a = ap.parse_args()

    pairs = []
    if a.map:
        for item in a.map.split(','):
            old, new = item.split('=')
            old = old.strip()
            if not os.path.splitext(old)[1]:
                old += '.png'
            pairs.append((old, new.strip()))
    else:
        for f in sorted(os.listdir(a.src)):
            if f.lower().endswith('.png'):
                pairs.append((f, os.path.splitext(f)[0] + '.png'))

    for old, new in pairs:
        s = os.path.join(a.src, old)
        if not os.path.exists(s):
            print('跳过（不存在）:', old)
            continue
        if a.tile:
            size = a.size
        else:
            # BOSS 用 2 倍；道具/图标比角色小一号
            base = os.path.splitext(new)[0]
            if base.startswith('boss'):
                size = int(a.size * 2)
            elif base.startswith(('enemy_', 'hero', 'shot_', 'boom')):
                size = a.size
            else:
                size = max(24, int(a.size * 2 // 3))
        d = os.path.join(a.dst, new)
        process(s, d, size, a.colors, a.tol, tile=a.tile, fix_seam=a.fix_seam,
                gray=a.gray, gamma=a.gamma)
        print('%-46s -> %s (%dpx, %d色%s)' % (
            old[:46], new, size, a.colors, ', 灰度' if a.gray else ''))


if __name__ == '__main__':
    main()
