#!/usr/bin/env python3
"""v2.8: 主菜单三屏流程(选角/选武器)/解锁系统/设置/被动核查(ai重名)"""
import re

P = '/home/hatch/workspace/bug-survivor/index.html'
html = open(P, encoding='utf-8').read()
parts = re.split(r'(<script>[\s\S]*?</script>)', html)
assert len(parts) == 3
head, script_tag, tail = parts
js = re.findall(r'<script>([\s\S]*?)</script>', script_tag)[0]
orig_len = len(js)
n = 0

def rep(old, new, cnt=1):
    global js, n
    assert js.count(old) >= 1, 'JS MISSING: ' + old[:80]
    js = js.replace(old, new, cnt); n += 1

def rep_html(old, new, cnt=1):
    global html, n
    assert html.count(old) >= 1, 'HTML MISSING: ' + old[:80]
    html = html.replace(old, new, cnt); n += 1

# ---------- 1. 存档扩展 ----------
rep("data:{ tp:0, best:null, unlocks:{}, diff:'normal', plays:0, hero:'dev' },",
    "data:{ tp:0, best:null, unlocks:{}, diff:'normal', plays:0, hero:'dev', mode:'std',\n"
    "    wins:0, totalKills:0, endlessBest:0,\n"
    "    settings:{ sfx:true, shake:true, dmgnum:true } },")

# ---------- 2. 英雄 ai -> trainer（与被动 Copilot 重名，改掉） ----------
rep("{ id:'ai',  name:'AI 训 练 师', spr:'h_ai',  color:'#f0abfc', weapon:'log',",
    "{ id:'trainer', name:'AI 训 练 师', spr:'h_ai',  color:'#f0abfc', weapon:'log',")

# ---------- 3. 解锁表 ----------
rep("const HMAP = {}; HEROES.forEach(h => HMAP[h.id] = h);",
"""const HMAP = {}; HEROES.forEach(h => HMAP[h.id] = h);
/* ---------------- 解锁条件 ---------------- */
const HERO_UNLOCKS = {
  trainer: { tip:'标准模式通关 1 次', ok:() => (Save.data.wins | 0) >= 1 },
  mf:      { tip:'累计击杀 3000',     ok:() => (Save.data.totalKills | 0) >= 3000 },
};
const WEAPON_UNLOCKS = {
  overflow: { tip:'累计击杀 1500',     ok:() => (Save.data.totalKills | 0) >= 1500 },
  review:   { tip:'标准模式通关 1 次', ok:() => (Save.data.wins | 0) >= 1 },
  docker:   { tip:'累计击杀 4000',     ok:() => (Save.data.totalKills | 0) >= 4000 },
  nullptr:  { tip:'无尽模式存活 8 分钟', ok:() => (Save.data.endlessBest | 0) >= 480 },
  loop:     { tip:'累计击杀 8000',     ok:() => (Save.data.totalKills | 0) >= 8000 },
};
function isHeroUnlocked(id){ const u = HERO_UNLOCKS[id]; return !u || u.ok(); }
function isWUnlocked(id){ const u = WEAPON_UNLOCKS[id]; return !u || u.ok(); }
function heroLockTip(id){ const u = HERO_UNLOCKS[id]; return u ? u.tip : ''; }
function weaponLockTip(id){ const u = WEAPON_UNLOCKS[id]; return u ? u.tip : ''; }""")

# ---------- 4. 开局武器用所选 ----------
rep("const startWeapons = [{ id:H.weapon, lv:1, t:0 }];",
    "const swId = (this.starterWeapon && isWUnlocked(this.starterWeapon)) ? this.starterWeapon : H.weapon;\n"
    "    const startWeapons = [{ id:swId, lv:1, t:0 }];")

# ---------- 5. 结算统计 ----------
rep("    Save.data.plays++;\n",
    "    Save.data.plays++;\n"
    "    Save.data.totalKills = (Save.data.totalKills | 0) + G.kills;\n"
    "    if (win && !G.endless) Save.data.wins = (Save.data.wins | 0) + 1;\n"
    "    if (G.endless) Save.data.endlessBest = Math.max(Save.data.endlessBest | 0, Math.floor(G.t));\n"
    "    Save.flush();\n")

# ---------- 6. 局内武器池过滤未解锁 ----------
rep("if (p.weapons.length < 6) for (const d of WEAPONS) if (!Game.weapon(d.id)) opts.push({ type:'w', id:d.id, isNew:true });",
    "if (p.weapons.length < 6) for (const d of WEAPONS) if (!Game.weapon(d.id) && isWUnlocked(d.id)) opts.push({ type:'w', id:d.id, isNew:true });")
rep("for (const d of WEAPONS) if (p.weapons.length < 6 && !Game.weapon(d.id)) opts.push(['w', d.id]);",
    "for (const d of WEAPONS) if (p.weapons.length < 6 && !Game.weapon(d.id) && isWUnlocked(d.id)) opts.push(['w', d.id]);")

# ---------- 7. renderHeroes 重写（含锁） ----------
i0 = js.find('renderHeroes(){')
i1 = js.find('renderUnlocks(){')
assert i0 > 0 and i1 > i0
new_heroes = '''renderHeroes(){
    const box = $('heroBox'); if (!box) return;
    box.innerHTML = HEROES.map(h => {
      const unlocked = isHeroUnlocked(h.id);
      const on = Game.heroId === h.id;
      const sprKey = (h.spr && SPR[h.spr]) ? h.spr : 'p_down';
      const bg = 'background:linear-gradient(155deg,' + mix(h.color, '#0b1220', .45) +
                 ',' + mix(h.color, '#0b1220', .8) + ')';
      return '<div class="hcard' + (on ? ' on' : '') + (unlocked ? '' : ' locked') + '" data-h="' + h.id + '">' +
        '<div class="hic" style="' + bg + '"><canvas data-spr="' + sprKey + '"></canvas>' +
        (unlocked ? '' : '<div class="lockov">\\uD83D\\uDD12</div>') + '</div>' +
        '<div class="hn">' + h.name + '</div>' +
        '<div class="hw">起手：' + (WMAP[h.weapon] ? WMAP[h.weapon].name : '—') + '</div>' +
        '<div class="hb">' +
          (unlocked
            ? (h.pros.length ? '<i>' + h.pros.join(' ') + '</i>' : '<i>均衡 · 无副作用</i>') +
              (h.cons.length ? '<u>' + h.cons.join(' ') + '</u>' : '')
            : '<u>\\uD83D\\uDD12 ' + heroLockTip(h.id) + '解锁</u>') +
        '</div></div>';
    }).join('');
    this.paintIcons(box);
    for (const el of box.querySelectorAll('.hcard'))
      el.addEventListener('click', () => {
        const id = el.dataset.h;
        if (!isHeroUnlocked(id)) { this.toast('\\uD83D\\uDD12 ' + heroLockTip(id) + '后解锁'); return; }
        Game.heroId = id;
        Save.data.hero = id; Save.flush();
        this.renderHeroes();
        this.openWeaponSel();
        SFX.pick();
      });
  },

  /* ---- 选初始武器 ---- */
  openWeaponSel(){
    const h = HMAP[Game.heroId] || HEROES[0];
    if (!Game.starterWeapon || !isWUnlocked(Game.starterWeapon)) Game.starterWeapon = h.weapon;
    this.renderWeaponSel();
    this.showOnly('weaponSel');
  },
  renderWeaponSel(){
    const box = $('weaponBox'); if (!box) return;
    const h = HMAP[Game.heroId] || HEROES[0];
    $('wsHero').textContent = '—— ' + h.name.replace(/\\s/g, '') + ' ——';
    box.innerHTML = WEAPONS.map(w => {
      const unlocked = isWUnlocked(w.id);
      const on = Game.starterWeapon === w.id;
      return '<div class="wcard' + (on ? ' on' : '') + (unlocked ? '' : ' locked') + '" data-w="' + w.id + '">' +
        '<div class="wic"><canvas data-spr="i_' + w.id + '"></canvas>' +
        (unlocked ? '' : '<div class="lockov">\\uD83D\\uDD12</div>') + '</div>' +
        '<div class="wn">' + w.name + '</div>' +
        '<div class="wd">' + (unlocked ? w.desc : '\\uD83D\\uDD12 ' + weaponLockTip(w.id) + '解锁') + '</div></div>';
    }).join('');
    this.paintIcons(box);
    for (const el of box.querySelectorAll('.wcard'))
      el.addEventListener('click', () => {
        const id = el.dataset.w;
        if (!isWUnlocked(id)) { this.toast('\\uD83D\\uDD12 ' + weaponLockTip(id) + '后解锁'); return; }
        Game.starterWeapon = id;
        this.renderWeaponSel(); SFX.pick();
      });
  },

  /* ---- 界面切换 ---- */
  showOnly(id){
    for (const s of ['start','heroSel','weaponSel','help','tech','settings']) $(s).classList.add('hidden');
    $(id).classList.remove('hidden');
    Game.state = 'start';
  },
  openHeroSel(){ this.renderHeroes(); this.renderStatsLine(); this.showOnly('heroSel'); },

  /* ---- 设置 ---- */
  renderSettings(){
    const s = Save.data.settings || (Save.data.settings = { sfx:true, shake:true, dmgnum:true });
    const rows = [
      ['sfx', '音效', SFX.on !== false],
      ['shake', '屏幕震动', s.shake !== false],
      ['dmgnum', '伤害数字', s.dmgnum !== false],
    ];
    $('settingsBox').innerHTML = rows.map(r =>
      '<div class="srow"><span>' + r[1] + '</span><div class="dbtn' + (r[2] ? ' on' : '') + '" data-k="' + r[0] + '">' +
      '<span>' + (r[2] ? '开' : '关') + '</span></div></div>').join('') +
      '<div class="srow"><span>累计击杀</span><b>' + (Save.data.totalKills | 0) + '</b></div>' +
      '<div class="srow"><span>标准通关</span><b>' + (Save.data.wins | 0) + ' 次</b></div>' +
      '<div class="srow" style="border:none"><span>无尽最久</span><b>' + fmtTime(Save.data.endlessBest | 0) + '</b></div>';
    for (const el of $('settingsBox').querySelectorAll('.dbtn'))
      el.addEventListener('click', () => {
        const k = el.dataset.k;
        if (k === 'sfx') SFX.on = !SFX.on; else s[k] = !s[k];
        Save.flush(); this.renderSettings(); SFX.pick();
      });
  },
  renderStatsLine(){
    const el = $('statsLine');
    if (el) el.textContent = '累计击杀 ' + (Save.data.totalKills | 0) + ' · 标准通关 ' + (Save.data.wins | 0) + ' 次';
  },

'''
js = js[:i0] + new_heroes + js[i1:]
n += 1

# ---------- 8. startGame：隐藏新界面 + 默认起手 ----------
rep("for (const id of ['start','over','pause','levelup','help','tech']) $(id).classList.add('hidden');",
    "for (const id of ['start','over','pause','levelup','help','tech','heroSel','weaponSel','settings']) $(id).classList.add('hidden');\n"
    "    if (!Game.starterWeapon) Game.starterWeapon = (HMAP[Game.heroId] || HEROES[0]).weapon;")

# ---------- 9. init 接线 ----------
rep("UI.renderDiff(); UI.renderMode();",
    "UI.renderDiff(); UI.renderMode();\n"
    "  SFX.on = Save.data.settings.sfx !== false;")
rep("$('btnStart').addEventListener('click', () => UI.startGame());",
    "$('btnStart').addEventListener('click', () => UI.openHeroSel());\n"
    "  $('btnSettings').addEventListener('click', () => { UI.renderSettings(); UI.showOnly('settings'); });\n"
    "  $('btnHeroBack').addEventListener('click', () => UI.showOnly('start'));\n"
    "  $('btnWeaponBack').addEventListener('click', () => UI.openHeroSel());\n"
    "  $('btnGo').addEventListener('click', () => UI.startGame());\n"
    "  $('btnSettingsBack').addEventListener('click', () => UI.showOnly('start'));")

# ---------- 10. 震屏/伤害数字开关 ----------
rep("if (Game.shake > 0) ctx.translate(rnd(-Game.shake, Game.shake) * 0.5, rnd(-Game.shake, Game.shake) * 0.5);",
    "if (Game.shake > 0 && (Save.data.settings || {}).shake !== false) ctx.translate(rnd(-Game.shake, Game.shake) * 0.5, rnd(-Game.shake, Game.shake) * 0.5);")
rep("function dmgText(x, y, v, color, crit){\n  if (Game.texts.length > 46) Game.texts.shift();",
    "function dmgText(x, y, v, color, crit){\n  if ((Save.data.settings || {}).dmgnum === false) return;\n  if (Game.texts.length > 46) Game.texts.shift();")

# ---------- HTML: 主菜单改造 ----------
rep_html('<div class="herobar" id="heroBox"></div>\n', '')
rep_html('<div class="btn" id="btnStart" data-page-node-id="vYl5rPCE7yEUCbyUH3a4oT">开 始 上 班</div>',
         '<div class="btn" id="btnStart" data-page-node-id="vYl5rPCE7yEUCbyUH3a4oT">开 始 上 班</div>\n'
         '        <div class="btn ghost" id="btnSettings">设 置</div>')
# 主菜单加战绩行（bestText 后）
rep_html('<div id="bestText" style="margin-top:7px;font-size:12px;color:#6f83a3;letter-spacing:.5px"',
         '<div id="statsLine" style="margin-top:7px;font-size:12px;color:#6f83a3;letter-spacing:.5px"></div>\n'
         '      <div id="bestText" style="margin-top:7px;font-size:12px;color:#6f83a3;letter-spacing:.5px"')

# ---------- HTML: 新界面 ----------
rep_html('      <div id="bestText"',
         '''      <div id="bestText"''')  # no-op, anchor check below
# 在 start 界面结束后插入新界面：找 hud 注释
anchor = '<!-- ================= HUD ================= -->'
assert anchor in html, 'HUD anchor missing'
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

# ---------- CSS ----------
assert html.count('</style>') == 1
rep_html('</style>',
'''.wcard{width:150px;padding:8px 8px 9px;border-radius:12px;cursor:pointer;text-align:center;
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

script_tag_new = '<script>' + js + '</script>'
html = head + script_tag_new + tail
open(P, 'w', encoding='utf-8').write(html)
print(f'OK: {n} edits, js {orig_len} -> {len(js)}')
