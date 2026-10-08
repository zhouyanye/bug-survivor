#!/usr/bin/env python3
"""补上 v2.7 + v2.8 丢失的 HTML/CSS 改动（纯 HTML 操作）"""
import re

P = '/home/hatch/workspace/bug-survivor/index.html'
html = open(P, encoding='utf-8').read()
orig = len(html)
n = 0

def rep(old, new, cnt=1):
    global html, n
    assert html.count(old) >= 1, 'HTML MISSING: ' + old[:80]
    html = html.replace(old, new, cnt); n += 1

# ===== v2.7 =====
# 1. 帮助 1/2/3 加 id
rep('<b data-page-node-id="BXGWexWWaScFV62VjyWqwY">1 / 2 / 3</b>',
    '<b id="kbHint" data-page-node-id="BXGWexWWaScFV62VjyWqwY">1 / 2 / 3</b>')
# 2. 模式选择 HTML
rep('<div class="diff" id="diffBox" data-page-node-id="W3OEMIHREDuihFjWI4yuq1"></div>',
    '<div class="diff" id="diffBox" data-page-node-id="W3OEMIHREDuihFjWI4yuq1"></div>\n'
    '          <h3 style="margin-top:12px">模 式 选 择</h3>\n'
    '          <div class="diff" id="modeBox"></div>')
# 3-6. HUD CSS
rep(".barbox{position:relative;height:19px;border-radius:6px;overflow:hidden;\n  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.13)}",
    ".barbox{position:relative;height:22px;border-radius:11px;overflow:hidden;\n  background:rgba(2,6,16,.72);border:1px solid rgba(94,234,212,.25);\n  box-shadow:inset 0 2px 6px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.4)}")
rep(".barbox .fill{position:absolute;left:0;top:0;bottom:0;border-radius:5px;transition:width .16s ease}",
    ".barbox .fill{position:absolute;left:0;top:0;bottom:0;border-radius:10px;transition:width .16s ease;\n  box-shadow:inset 0 2px 0 rgba(255,255,255,.35),inset 0 -2px 4px rgba(0,0,0,.25)}")
rep(".mini{position:relative;height:13px;border-radius:5px;overflow:hidden;\n  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.11)}",
    ".mini{position:relative;height:16px;border-radius:8px;overflow:hidden;\n  background:rgba(2,6,16,.72);border:1px solid rgba(167,139,250,.30);\n  box-shadow:inset 0 2px 5px rgba(0,0,0,.6)}")
rep("background:linear-gradient(90deg,#a78bfa,#22d3ee);box-shadow:0 0 10px rgba(167,139,250,.55);",
    "background:linear-gradient(90deg,#a78bfa,#22d3ee);box-shadow:0 0 10px rgba(167,139,250,.55),inset 0 2px 0 rgba(255,255,255,.30);")
# 7. 冲刺条去内联样式
rep('class="mini" style="height:5px;border-radius:3px"', 'class="mini dash"')
# 8. body 渐变
rep('body{width:100%;height:100%;overflow:hidden;background:#04060c;',
    'body{width:100%;height:100%;overflow:hidden;background:radial-gradient(120% 90% at 50% 10%, #0d1528 0%, #070b16 55%, #04060c 100%);')

# ===== v2.8 =====
# 10. 主菜单去掉 heroBox
rep('<div class="herobar" id="heroBox"></div>\n', '')
# 11. 加设置按钮
rep('<div class="btn" id="btnStart" data-page-node-id="vYl5rPCE7yEUCbyUH3a4oT">开 始 上 班</div>',
    '<div class="btn" id="btnStart" data-page-node-id="vYl5rPCE7yEUCbyUH3a4oT">开 始 上 班</div>\n'
    '        <div class="btn ghost" id="btnSettings">设 置</div>')
# 12. 战绩行
rep('<div id="bestText" style="margin-top:7px;font-size:12px;color:#6f83a3;letter-spacing:.5px"',
    '<div id="statsLine" style="margin-top:7px;font-size:12px;color:#6f83a3;letter-spacing:.5px"></div>\n'
    '      <div id="bestText" style="margin-top:7px;font-size:12px;color:#6f83a3;letter-spacing:.5px"')
# 13. 新界面
anchor = '<!-- ================= HUD ================= -->'
assert anchor in html
new_screens = '''<!-- ================= 选角 ================= -->
    <div id="heroSel" class="screen hidden">
      <div class="title" style="font-size:30px">选 择 角 色</div>
      <div class="sub">每 个 角 色 都 是 不 同 的 玩 法</div>
      <div class="herobar" id="heroBox" style="justify-content:center;flex-wrap:wrap;max-width:900px"></div>
      <div class="rowbtns" style="margin-top:14px"><div class="btn ghost" id="btnHeroBack">返 回</div></div>
    </div>
    <!-- ================= 选初始武器 ================= -->
    <div id="weaponSel" class="screen hidden">
      <div class="title" style="font-size:30px">选 择 初 始 武 器</div>
      <div class="sub" id="wsHero"></div>
      <div class="herobar" id="weaponBox" style="justify-content:center;flex-wrap:wrap;max-width:980px"></div>
      <div class="rowbtns" style="margin-top:14px">
        <div class="btn ghost" id="btnWeaponBack">返 回</div>
        <div class="btn" id="btnGo">出 战！</div>
      </div>
    </div>
    <!-- ================= 设置 ================= -->
    <div id="settings" class="screen hidden">
      <div class="title" style="font-size:30px">设 置</div>
      <div class="sub">调 整 你 的 战 斗 体 验</div>
      <div class="pnl" style="width:420px;margin:18px auto" id="settingsBox"></div>
      <div class="rowbtns"><div class="btn ghost" id="btnSettingsBack">返 回</div></div>
    </div>
    ''' + anchor
html = html.replace(anchor, new_screens, 1); n += 1

# ===== CSS 追加 =====
assert html.count('</style>') == 1
rep('</style>',
'''.mini.dash{height:9px;border-radius:5px}
.mini.dash .fill{background:linear-gradient(90deg,#22d3ee,#67e8f9);box-shadow:0 0 8px rgba(34,211,238,.6)}
.mini.dash::after{content:"冲刺";position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:9px;color:#a5f3fc;font-weight:800;letter-spacing:2px;text-shadow:0 1px 2px #000}
#lvText{background:rgba(167,139,250,.28);border:1px solid rgba(167,139,250,.55);border-radius:9px;padding:1px 8px;margin-right:6px;font-size:11px}
.wcard{width:150px;padding:8px 8px 9px;border-radius:12px;cursor:pointer;text-align:center;
  background:linear-gradient(170deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.12)}
.wcard.on{border-color:#fbbf24;box-shadow:0 0 14px rgba(251,191,36,.35)}
.wcard .wic{width:40px;height:40px;margin:0 auto 5px;border-radius:10px;display:flex;align-items:center;justify-content:center;
  background:rgba(255,255,255,.05);position:relative}
.wcard .wn{font-size:13px;font-weight:800;color:#e8f1ff;margin-bottom:3px}
.wcard .wd{font-size:11px;color:#8fa3c4;line-height:1.5;min-height:33px}
.hcard.locked,.wcard.locked{filter:grayscale(.65);opacity:.8;cursor:not-allowed}
.hic{position:relative}
.lockov{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-size:22px;background:rgba(2,6,16,.5);border-radius:10px}
.srow{display:flex;align-items:center;justify-content:space-between;padding:11px 4px;
  border-bottom:1px solid rgba(255,255,255,.07);font-size:14px;color:#c9d6ec}
.srow .dbtn{min-width:70px;text-align:center;cursor:pointer}
.srow b{color:#e8f1ff}
</style>''')

open(P, 'w', encoding='utf-8').write(html)
print(f'HTML OK: {n} edits, {orig} -> {len(html)}')
