#!/usr/bin/env python3
"""v2.7: 击退/开局乱射/回血被动/走路/站姿/HUD/经验曲线/移动端/性能/无尽模式/新角色/新武器"""
import re, sys

P = '/home/hatch/workspace/bug-survivor/index.html'
html = open(P, encoding='utf-8').read()
parts = re.split(r'(<script>[\s\S]*?</script>)', html)
assert len(parts) == 3, f'script blocks: {len(parts)}'
head, script_tag, tail = parts
js = re.findall(r'<script>([\s\S]*?)</script>', script_tag)[0]
orig_len = len(js)
n_edit = 0

def rep(old, new, cnt=1):
    global js, n_edit
    assert js.count(old) >= 1, 'JS MISSING: ' + old[:80]
    js = js.replace(old, new, cnt)
    n_edit += 1

def rep_html(old, new, cnt=1):
    global html, n_edit
    assert html.count(old) >= 1, 'HTML MISSING: ' + old[:80]
    html = html.replace(old, new, cnt)
    n_edit += 1

# ---------- 1. 移动端检测 ----------
rep("const TAU = Math.PI * 2;",
    "const TAU = Math.PI * 2;\n"
    "const IS_MOBILE = (typeof matchMedia !== 'undefined' && matchMedia('(pointer:coarse)').matches) ||\n"
    "  /Mobi|Android|iPhone|iPad|HarmonyOS/i.test(navigator.userAgent || '');")

# ---------- 2. 击退：Boss/精英抗性 ----------
rep("if (knock) { e.kbx += kx * knock; e.kby += ky * knock; }",
    "if (knock) { const kr = e.boss ? 0.15 : (e.elite ? 0.4 : 1); e.kbx += kx * knock * kr; e.kby += ky * knock * kr; }")

# ---------- 3. 子弹击退 1.6->0.7，轨道球 1.2->0.6，评审波 2.6->1.6 ----------
rep("hurtEnemy(e, b.dmg, b.vx * 0.012, b.vy * 0.012, 1.6, b.wid);",
    "hurtEnemy(e, b.dmg, b.vx * 0.012, b.vy * 0.012, 0.7, b.wid);")
rep("hurtEnemy(e, s.dmg * dm, (e.x - ox) * 0.05, (e.y - oy) * 0.05, 1.2, ow.id);",
    "hurtEnemy(e, s.dmg * dm, (e.x - ox) * 0.05, (e.y - oy) * 0.05, 0.6, ow.id);")
rep("hurtEnemy(e, w.dmg, (e.x - w.x) * 0.01, (e.y - w.y) * 0.01, 2.6, w.wid);",
    "hurtEnemy(e, w.dmg, (e.x - w.x) * 0.01, (e.y - w.y) * 0.01, 1.6, w.wid);")

# ---------- 4. 开局无怪乱射：索敌判空 ----------
rep("case 'regex': {",
    "case 'regex': {\n        if (!nearestEnemy(p.x, p.y, 650)) { w.t = 0.15; break; }")
rep("case 'undo': {",
    "case 'undo': {\n        if (!nearestEnemy(p.x, p.y, 550)) { w.t = 0.15; break; }")
rep("case 'overflow': {",
    "case 'overflow': {\n        if (!nearestEnemy(p.x, p.y, 450)) { w.t = 0.15; break; }")
rep("case 'review': {",
    "case 'review': {\n        if (!nearestEnemy(p.x, p.y, s.r + 120)) { w.t = 0.15; break; }")
rep("case 'docker': {",
    "case 'docker': {\n        if (!nearestEnemy(p.x, p.y, 750)) { w.t = 0.15; break; }")
rep("case 'mine': {",
    "case 'mine': {\n        if (!nearestEnemy(p.x, p.y, 550)) { w.t = 0.15; break; }")

# ---------- 5. 回血被动改为实时计算 ----------
rep("if (p.regen > 0 && p.hp < p.maxHp) p.hp = Math.min(p.maxHp, p.hp + p.regen * dt);",
    "const rgRate = Game.stat('regen') * 0.7;\n  if (rgRate > 0 && p.hp < p.maxHp) p.hp = Math.min(p.maxHp, p.hp + rgRate * dt);")
rep("      if (o.id === 'regen') p.regen = Game.stat('regen') * 0.7;\n", "")
rep("        if (id === 'regen') p.regen = Game.stat('regen') * 0.7;\n", "")

# ---------- 6. 走路：减小弹跳 + 朝向翻转迟滞 ----------
rep("const bob = moving ? Math.sin(p.walkT * 9) * 2.2 : Math.sin(Game.t * 2.2) * 0.8;",
    "const bob = moving ? Math.sin(p.walkT * 9) * 1.3 : Math.sin(Game.t * 2.2) * 0.8;")
rep("""  let key = 'p_down', flip = false;
  if (p.heroSpr && SPR[p.heroSpr]) {
    key = p.heroSpr; flip = ax < 0;
  } else if (Math.abs(ay) > Math.abs(ax) * 0.68) {
    key = ay > 0 ? 'p_down' : 'p_up';
  } else { key = 'p_side'; flip = ax < 0; }""",
"""  let key = 'p_down', flip = p._flip || false;
  if (p.heroSpr && SPR[p.heroSpr]) {
    key = p.heroSpr;
  } else if (Math.abs(ay) > Math.abs(ax) * 0.68) {
    key = ay > 0 ? 'p_down' : 'p_up';
  } else { key = 'p_side'; }
  if (ax > 0.25) flip = false; else if (ax < -0.25) flip = true;
  p._flip = flip;""")

# ---------- 7. 经验曲线：前快后难 ----------
rep("function expNeed(lv){ return Math.floor(6 + lv * 5.6 + Math.pow(lv, 1.85)); }",
    "function expNeed(lv){ return Math.floor(5 + lv * 4.8 + Math.pow(lv, 2.0)); }")

# ---------- 8. 性能：DPR 上限 / 渐晕缓存 / 粒子减半 / 阴影 ----------
rep("DPR = Math.min(2, window.devicePixelRatio || 1);",
    "DPR = Math.min(IS_MOBILE ? 1.5 : 2, window.devicePixelRatio || 1);")
rep("let bgPat = null;",
    "let bgPat = null, bgVig = null;")
rep("""    const g = ctx.createRadialGradient(LW / 2, LH / 2, LH * 0.18, LW / 2, LH / 2, LH * 0.78);
    g.addColorStop(0, 'rgba(4,7,14,0)'); g.addColorStop(1, 'rgba(4,7,14,.38)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, LW, LH);""",
"""    if (!bgVig) {
      bgVig = ctx.createRadialGradient(LW / 2, LH / 2, LH * 0.18, LW / 2, LH / 2, LH * 0.78);
      bgVig.addColorStop(0, 'rgba(4,7,14,0)'); bgVig.addColorStop(1, 'rgba(4,7,14,.38)');
    }
    ctx.fillStyle = bgVig; ctx.fillRect(0, 0, LW, LH);""")
rep("""function particle(x, y, color, n, spd, size){
  for (let i = 0; i < n; i++) {""",
"""function particle(x, y, color, n, spd, size){
  n = IS_MOBILE ? Math.max(1, Math.ceil(n / 2)) : n;
  for (let i = 0; i < n; i++) {""")
rep("ctx.shadowColor = b.color; ctx.shadowBlur = 14;",
    "ctx.shadowColor = b.color; ctx.shadowBlur = IS_MOBILE ? 0 : 14;")
rep("ctx.shadowColor = WMAP.orb.color; ctx.shadowBlur = 16;",
    "ctx.shadowColor = WMAP.orb.color; ctx.shadowBlur = IS_MOBILE ? 0 : 16;")
rep("ctx.shadowColor = '#22d3ee'; ctx.shadowBlur = 12;",
    "ctx.shadowColor = '#22d3ee'; ctx.shadowBlur = IS_MOBILE ? 0 : 12;")
rep("ctx.shadowColor = w.color; ctx.shadowBlur = 18;",
    "ctx.shadowColor = w.color; ctx.shadowBlur = IS_MOBILE ? 0 : 18;")

# ---------- 9. 移动端隐藏 1/2/3 ----------
rep("'<div class=\"keyhint\">' + (i + 1) + '</div>' +",
    "(IS_MOBILE ? '' : '<div class=\"keyhint\">' + (i + 1) + '</div>') +")

# ---------- 10. 无尽模式 ----------
rep("if (Game.t >= RUN_TIME) { endGame(true); return; }",
    "if (!Game.endless && Game.t >= RUN_TIME) { endGame(true); return; }")
rep("  // BOSS\n  const nb = BOSS_DEFS[Game.bossSpawned];\n  if (nb && t >= nb.at) spawnBoss();",
    "  // BOSS\n  const nb = BOSS_DEFS[Game.bossSpawned];\n  if (nb && t >= nb.at) spawnBoss();\n"
    "  // 无尽模式：固定 Boss 打完后，每 150 秒循环刷一只（血量随次数成长）\n"
    "  if (Game.endless && Game.bossSpawned >= BOSS_DEFS.length) {\n"
    "    Game.endlessBossAcc = (Game.endlessBossAcc || 0) + dt;\n"
    "    if (Game.endlessBossAcc >= 150) { Game.endlessBossAcc = 0; spawnBoss(); }\n"
    "  }")
rep("""    const left = Math.max(0, RUN_TIME - G.t);
    $('timeText').textContent = fmtTime(left);
    $('timeText').style.color = left < 60 ? '#ff6b8b' : '#e8f1ff';""",
"""    if (G.endless) {
      $('timeText').textContent = fmtTime(G.t);
      $('timeText').style.color = '#e8f1ff';
      $('timeSub').textContent = '已 加 班';
    } else {
      const left = Math.max(0, RUN_TIME - G.t);
      $('timeText').textContent = fmtTime(left);
      $('timeText').style.color = left < 60 ? '#ff6b8b' : '#e8f1ff';
      $('timeSub').textContent = '距 下 班';
    }""")
rep("""    $('overTitle').textContent = win ? '下 班 成 功' : '你 被 优 化 了';
    $('overSub').textContent = win
      ? '10 分钟零重大故障，你是这个项目的定海神针'
      : 'Bug 洪流冲垮了最后一道防线';""",
"""    $('overTitle').textContent = win ? '下 班 成 功' : (G.endless ? '精 疲 力 尽' : '你 被 优 化 了');
    $('overSub').textContent = win
      ? '10 分钟零重大故障，你是这个项目的定海神针'
      : (G.endless ? '在无尽的 Bug 洪流中坚持了 ' + fmtTime(G.t) : 'Bug 洪流冲垮了最后一道防线');""")
rep("""    Game.diff = DIFFS.find(x => x.id === Game.diffId) || DIFFS[1];
    Game.reset();""",
"""    Game.diff = DIFFS.find(x => x.id === Game.diffId) || DIFFS[1];
    Game.endless = (Save.data.mode === 'endless');
    Game.reset();""")
rep("this.toast('开工！' + Game.diff.name.replace(/\\s/g, '') + ' · 活满 10 分钟就能下班');",
    "this.toast('开工！' + Game.diff.name.replace(/\\s/g, '') + (Game.endless ? ' · 无尽模式，活下去' : ' · 活满 10 分钟就能下班'));")

# 模式选择 UI
rep("""  },

  /* ---- 菜单：角色选择 ---- */""",
"""  },

  /* ---- 菜单：模式选择 ---- */
  renderMode(){
    const modes = [
      { id:'std', name:'标准模式', tip:'活满 10 分钟下班' },
      { id:'endless', name:'无尽模式', tip:'活到死为止' },
    ];
    const cur = Save.data.mode || 'std';
    $('modeBox').innerHTML = modes.map(m =>
      '<div class="dbtn' + (cur === m.id ? ' on' : '') + '" data-m="' + m.id + '">' +
      '<span>' + m.name + '</span><span class="d2">' + m.tip + '</span></div>').join('');
    for (const el of $('modeBox').querySelectorAll('.dbtn'))
      el.addEventListener('click', () => {
        Save.data.mode = el.dataset.m; Save.flush();
        this.renderMode(); SFX.pick();
      });
  },

  /* ---- 菜单：角色选择 ---- */""")
rep("UI.renderDiff();", "UI.renderDiff(); UI.renderMode();")

# ---------- 11. 新武器：空指针 / 死循环 ----------
rep("""      {dmg:48, n:3, life:10, cd:0.40}] },
];""",
"""      {dmg:48, n:3, life:10, cd:0.40}] },

  { id:'nullptr', name:'空指针解引用', abbr:'空', color:'#f472b6', max:8,
    desc:'向最近的 Bug 发射高伤害狙击针，超长穿透，一击脱离。',
    cd:1.50, stats:[
      {dmg:34, n:1, pierce:3}, {dmg:42, n:1, pierce:3}, {dmg:50, n:1, pierce:4},
      {dmg:58, n:2, pierce:4}, {dmg:68, n:2, pierce:5}, {dmg:78, n:2, pierce:5},
      {dmg:90, n:3, pierce:6}, {dmg:105, n:3, pierce:8}] },

  { id:'loop', name:'死循环 while', abbr:'循', color:'#facc15', max:8,
    desc:'while(true) 螺旋弹幕，越转越快，停不下来。',
    cd:1.10, stats:[
      {dmg:7, n:3}, {dmg:8, n:3}, {dmg:9, n:4}, {dmg:11, n:4},
      {dmg:12, n:5}, {dmg:14, n:5}, {dmg:16, n:6}, {dmg:19, n:8}] },
];""")
rep("""  // 断点光环
  const aw = Game.weapon('aura');""",
"""      case 'nullptr': {
        if (!nearestEnemy(p.x, p.y, 900)) { w.t = 0.15; break; }
        const tgt = nearestEnemy(p.x, p.y, 900);
        const a = Math.atan2(tgt.y - p.y, tgt.x - p.x);
        for (let i = 0; i < s.n; i++) {
          const aa = a + (i - (s.n - 1) / 2) * 0.09;
          bullet({ x:p.x, y:p.y, vx:Math.cos(aa) * 780, vy:Math.sin(aa) * 780, r:7,
            dmg:s.dmg * dm, pierce:s.pierce, life:1.2, color:def.color, wid:w.id });
        }
        SFX.shoot(); break;
      }
      case 'loop': {
        if (!nearestEnemy(p.x, p.y, 450)) { w.t = 0.15; break; }
        for (let i = 0; i < s.n; i++) {
          const a = p.spiral + (i / s.n) * TAU;
          bullet({ x:p.x, y:p.y, vx:Math.cos(a) * 300, vy:Math.sin(a) * 300, r:6,
            dmg:s.dmg * dm, pierce:1, life:1.1, color:def.color, wid:w.id });
        }
        SFX.shoot(); break;
      }
    }
  }

  // 断点光环
  const aw = Game.weapon('aura');""")

# ---------- 12. 新角色 + 默认程序员站姿 ----------
rep("{ id:'dev', name:'全 栈 工 程 师', spr:null,    color:'#38bdf8', weapon:'log',",
    "{ id:'dev', name:'全 栈 工 程 师', spr:'h_dev', color:'#38bdf8', weapon:'log',")
rep("""  { id:'qa',  name:'测 试 找 茬 王', spr:'h_qa',  color:'#c084fc', weapon:'regex',
    desc:'复现一次学一次，升级飞快，就是打不疼。',
    pros:['经验+25%','拾取+15%'], cons:['伤害−12%'],
    mods:{ exp:1.25, pick:1.15, dmg:0.88 } },
];""",
"""  { id:'qa',  name:'测 试 找 茬 王', spr:'h_qa',  color:'#c084fc', weapon:'regex',
    desc:'复现一次学一次，升级飞快，就是打不疼。',
    pros:['经验+25%','拾取+15%'], cons:['伤害−12%'],
    mods:{ exp:1.25, pick:1.15, dmg:0.88 } },
  { id:'ai',  name:'AI 训 练 师', spr:'h_ai',  color:'#f0abfc', weapon:'orb',
    desc:'调参炼丹，越训越强，升级如喝水。',
    pros:['经验+15%','攻速+8%'], cons:['生命−10'],
    mods:{ exp:1.15, rate:1.08, hp:-10 } },
  { id:'mf',  name:'摸 鱼 大 师', spr:'h_mf',  color:'#fde68a', weapon:'undo',
    desc:'带薪摸鱼，跑得快、捡得快，就是不太想打。',
    pros:['移速+12%','拾取+30%'], cons:['伤害−8%'],
    mods:{ spd:1.12, pick:1.30, dmg:0.92 } },
];""")

# ---------- 13. 锤子挥舞贴锤子图 / 评审波带图标 ----------
rep("Game.hazards.push({ x:p.x, y:p.y, r:s.r, a0:p.face, a:s.a, life:0.22, max:0.22,\n          color:def.color });",
    "Game.hazards.push({ x:p.x, y:p.y, r:s.r, a0:p.face, a:s.a, life:0.22, max:0.22,\n          color:def.color, wid:w.id });")
rep("""    ctx.beginPath(); ctx.moveTo(0, 0);
    ctx.arc(0, 0, h.r, h.a0 - h.a / 2, h.a0 + h.a / 2); ctx.closePath(); ctx.fill();
    ctx.restore(); ctx.globalAlpha = 1;""",
"""    ctx.beginPath(); ctx.moveTo(0, 0);
    ctx.arc(0, 0, h.r, h.a0 - h.a / 2, h.a0 + h.a / 2); ctx.closePath(); ctx.fill();
    if (h.wid === 'hammer' && SPR.shot_hammer) {
      const k = 1 - h.life / h.max, ma = h.a0 - h.a / 2 + h.a * k;
      ctx.save(); ctx.translate(Math.cos(ma) * h.r * 0.72, Math.sin(ma) * h.r * 0.72);
      ctx.rotate(ma + Math.PI / 2);
      blit(SPR.shot_hammer, 0, 0, 46, 46, false);
      ctx.restore();
    }
    ctx.restore(); ctx.globalAlpha = 1;""")
rep("""    ctx.beginPath(); ctx.arc(x, y, w.r, 0, TAU); ctx.stroke();
    ctx.restore(); ctx.globalAlpha = 1; ctx.shadowBlur = 0;""",
"""    ctx.beginPath(); ctx.arc(x, y, w.r, 0, TAU); ctx.stroke();
    if (w.wid === 'review' && SPR.shot_review) {
      const pr = 26 + Math.sin(Game.t * 10) * 4;
      blit(SPR.shot_review, x, y - w.r, pr, pr, false);
    }
    ctx.restore(); ctx.globalAlpha = 1; ctx.shadowBlur = 0;""")

# ---------- 14. 帮助里 1/2/3 移动端改字 ----------
rep_html('<b data-page-node-id="BXGWexWWaScFV62VjyWqwY">1 / 2 / 3</b>',
         '<b id="kbHint" data-page-node-id="BXGWexWWaScFV62VjyWqwY">1 / 2 / 3</b>')
rep("UI.renderDiff(); UI.renderMode();",
    "UI.renderDiff(); UI.renderMode();\n  if (IS_MOBILE && $('kbHint')) $('kbHint').textContent = '点选';")

# ---------- 15. 模式选择 HTML ----------
rep_html('<div class="diff" id="diffBox" data-page-node-id="W3OEMIHREDuihFjWI4yuq1"></div>',
         '<div class="diff" id="diffBox" data-page-node-id="W3OEMIHREDuihFjWI4yuq1"></div>\n'
         '          <h3 style="margin-top:12px">模 式 选 择</h3>\n'
         '          <div class="diff" id="modeBox"></div>')

# ---------- 16. HUD 样式重做 ----------
rep_html(".barbox{position:relative;height:19px;border-radius:6px;overflow:hidden;\n  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.13)}",
".barbox{position:relative;height:22px;border-radius:11px;overflow:hidden;\n  background:rgba(2,6,16,.72);border:1px solid rgba(94,234,212,.25);\n  box-shadow:inset 0 2px 6px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.4)}")
rep_html(".barbox .fill{position:absolute;left:0;top:0;bottom:0;border-radius:5px;transition:width .16s ease}",
".barbox .fill{position:absolute;left:0;top:0;bottom:0;border-radius:10px;transition:width .16s ease;\n  box-shadow:inset 0 2px 0 rgba(255,255,255,.35),inset 0 -2px 4px rgba(0,0,0,.25)}")
rep_html(".mini{position:relative;height:13px;border-radius:5px;overflow:hidden;\n  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.11)}",
".mini{position:relative;height:16px;border-radius:8px;overflow:hidden;\n  background:rgba(2,6,16,.72);border:1px solid rgba(167,139,250,.30);\n  box-shadow:inset 0 2px 5px rgba(0,0,0,.6)}")
rep_html("background:linear-gradient(90deg,#a78bfa,#22d3ee);box-shadow:0 0 10px rgba(167,139,250,.55);",
"background:linear-gradient(90deg,#a78bfa,#22d3ee);box-shadow:0 0 10px rgba(167,139,250,.55),inset 0 2px 0 rgba(255,255,255,.30);")
# 冲刺条去内联样式 + 等级徽章 + 冲刺标签
rep_html('class="mini" style="height:5px;border-radius:3px"', 'class="mini dash"')
rep_html('body{width:100%;height:100%;overflow:hidden;background:#04060c;',
         'body{width:100%;height:100%;overflow:hidden;background:radial-gradient(120% 90% at 50% 10%, #0d1528 0%, #070b16 55%, #04060c 100%);')
assert html.count('</style>') == 1
rep_html('</style>',
         '.mini.dash{height:9px;border-radius:5px}\n'
         '.mini.dash .fill{background:linear-gradient(90deg,#22d3ee,#67e8f9);box-shadow:0 0 8px rgba(34,211,238,.6)}\n'
         '.mini.dash::after{content:"冲刺";position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:9px;color:#a5f3fc;font-weight:800;letter-spacing:2px;text-shadow:0 1px 2px #000}\n'
         '#lvText{background:rgba(167,139,250,.28);border:1px solid rgba(167,139,250,.55);border-radius:9px;padding:1px 8px;margin-right:6px;font-size:11px}\n'
         '</style>')

script_tag_new = '<script>' + js + '</script>'
html = head + script_tag_new + tail
open(P, 'w', encoding='utf-8').write(html)
print(f'OK: {n_edit} edits, js {orig_len} -> {len(js)}')
