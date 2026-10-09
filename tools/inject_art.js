/**
 * 把 AI 生成的像素精灵以 base64 内嵌进 index.html。
 *
 * 设计原则：内嵌图是"覆盖层"，不是"替换层"——
 * 程序化精灵照常生成（保证任何一张图挂了/没生成都不会开天窗），
 * 图片加载完成后再覆盖对应 key。这样单文件、零依赖的约束不会被破坏。
 *
 * 用法：
 *   node tools/inject_art.js            # 注入（幂等，重复执行会替换旧块）
 *   node tools/inject_art.js --remove   # 移除，回退到纯程序化精灵
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const HTML = path.join(ROOT, 'index.html');
const SRC = path.join(ROOT, '_art', 'out');

// 文件名（去扩展名） -> 要覆盖的 SPR key 列表
const MAP = {
  bg_tile:         ['bgTile'],        // 背景砖：单独在 drawBackground 里用
  shot_energy:     ['shotEnergy'],    // 灰度贴图：运行时按武器色染色
  shot_orb:        ['shotOrb'],
  mine:            ['mine', 'd_mineitem'],  // 覆盖程序化版本；拾取道具图标复用
  turret:          ['turret'],
  boom:            ['boom'],          // 爆炸特效贴图
  hero:            ['p_down', 'p_up', 'p_side'],
  // v2.4：可选角色（各自一张正面图，运行时按朝向翻转）
  hero_fe:         ['h_fe'],
  hero_be:         ['h_be'],
  hero_ops:        ['h_ops'],
  hero_qa:         ['h_qa'],
  enemy_npe:       ['e_null'],
  enemy_leak:      ['e_mem'],
  enemy_loop:      ['e_loop'],
  enemy_race:      ['e_race'],
  enemy_deadlock:  ['e_block'],
  enemy_segfault:  ['e_seg'],
  enemy_conflict:  ['e_dep'],
  // v2.4：新增敌人
  enemy_worm:      ['e_worm'],
  enemy_inject:    ['e_inject'],
  enemy_zombie:    ['e_zombie'],
  enemy_cache:     ['e_cache'],
  // v2.5：新增敌人
  enemy_frag:      ['e_frag'],
  enemy_stack:     ['e_stack'],
  enemy_cors:      ['e_cors'],
  boss_debt:       ['e_techdebt'],
  boss_require:    ['e_require'],
  // v2.4：第三只 BOSS
  boss_prod:       ['e_prod'],
  // v2.5：第四只 BOSS
  boss_rmrf:       ['e_rmrf'],
  // v2.4：新增被动图标
  item_ai:         ['i_ai'],
  item_shield:     ['i_shield', 'd_shield'],  // WAF 护盾限时道具拾取图标复用
  item_backup:     ['i_backup'],
  // 宝箱三态
  chest_closed:    ['chest'],
  chest_lidopen:   ['chestLid'],
  chest_opened:    ['chestOpen'],
  gem:             ['gem', 'gemBig'],
  chest:           ['chest'],
  coffee:          ['d_heal'],
  magnet:          ['d_magnet'],
  bomb:            ['d_bomb'],
  clock:           ['d_clock'],
  // v2.6：武器专属贴图（弹道 + 图标共用一张，覆盖程序化 ICONS）
  shot_log:      ['shot_log', 'i_log'],
  shot_aura:     ['shot_aura', 'i_aura'],
  shot_orb:      ['shot_orb', 'i_orb'],
  shot_regex:    ['shot_regex', 'i_regex'],
  shot_undo:     ['shot_undo', 'i_undo'],
  shot_hammer:   ['shot_hammer', 'i_hammer'],
  shot_push:     ['shot_push', 'i_push'],
  shot_overflow: ['shot_overflow', 'i_overflow'],
  shot_review:   ['shot_review', 'i_review'],
  shot_docker:   ['shot_docker', 'i_docker'],
  shot_nullptr:  ['shot_nullptr', 'i_nullptr'],
  shot_loop:     ['shot_loop', 'i_loop'],
  hero_dev:      ['h_dev'],
  hero_ai:       ['h_ai'],
  hero_mf:       ['h_mf'],
};

const BEG = '/*__ART_BEG__*/';
const END = '/*__ART_END__*/';

// 序列帧：_art/out/anim 下按 <name>_NN.png 组织的帧序列，配 <name>.json 描述元信息
function animEntries() {
  const dir = path.join(SRC, 'anim');
  const lines = [], defs = {};
  if (!fs.existsSync(dir)) return { lines, defs, count: 0, bytes: 0 };
  const groups = {};
  for (const f of fs.readdirSync(dir)) {
    const m = f.match(/^(.+)_(\d{2})\.png$/);
    if (!m) continue;
    (groups[m[1]] = groups[m[1]] || []).push(f);
  }
  let count = 0, bytes = 0;
  for (const [name, files] of Object.entries(groups)) {
    files.sort();
    for (const f of files) {
      const b64 = fs.readFileSync(path.join(dir, f)).toString('base64');
      lines.push(`  '${f.replace('.png', '')}': 'data:image/png;base64,${b64}',`);
      count++; bytes += b64.length;
    }
    const mp = path.join(dir, name + '.json');
    if (fs.existsSync(mp)) {
      const man = JSON.parse(fs.readFileSync(mp, 'utf8'));
      defs[name] = { n: man.frames, w: man.w, h: man.h };
    }
  }
  return { lines, defs, count, bytes };
}

function buildBlock() {
  const lines = [];
  let total = 0;
  for (const [file, keys] of Object.entries(MAP)) {
    const p = path.join(SRC, file + '.png');
    if (!fs.existsSync(p)) { console.log('  缺图，跳过:', file); continue; }
    const b64 = fs.readFileSync(p).toString('base64');
    total += b64.length;
    const uri = 'data:image/png;base64,' + b64;
    for (const k of keys) lines.push(`  '${k}': '${uri}',`);
  }
  const anim = animEntries();
  const body = [
    BEG,
    '/* ---- 像素素材：base64 内嵌，加载后覆盖同名程序化精灵 ---- */',
    'const ART_RAW = {',
    ...lines,
    ...anim.lines,
    '};',
    '/* 序列帧元信息：帧数 + 单帧画布尺寸（非正方形，绘制时按比例还原） */',
    'const ANIM = ' + JSON.stringify(anim.defs) + ';',
    'const ART = {};',
    'function loadArt(done){',
    '  const keys = Object.keys(ART_RAW);',
    '  let left = keys.length;',
    '  if (!left) { if (done) done(); return; }',
    '  const one = () => { if (--left <= 0 && done) done(); };',
    '  for (const k of keys) {',
    '    const im = new Image();',
    '    im.onload = () => { ART[k] = im; one(); };',
    '    im.onerror = () => one();          // 单张失败静默回退到程序化精灵',
    '    im.src = ART_RAW[k];',
    '  }',
    '}',
    'function animFrame(name, i){',
    '  return ART[name + "_" + (i < 10 ? "0" : "") + i];',
    '}',
    'function applyArt(){',
    '  for (const k in ART) {',
    '    const im = ART[k];',
    '    if (!im || !im.naturalWidth) continue;',
    '    SPR[k] = im;',
    '    if (k.indexOf("bg") !== 0) SPR["w_" + k] = whiteSprite(im);  // 背景砖不需要闪白帧',
    '  }',
    '}',
    END,
  ].join('\n');
  return { body, total: total + anim.bytes, animCount: anim.count };
}

// 用字符串切片而不是正则：标记里的 * / 是正则元字符，
// 手写转义很容易漏，一旦漏了 remove 就会静默失效、然后重复插入。
function stripBlock(html) {
  for (;;) {
    const i = html.indexOf(BEG);
    if (i < 0) return html;
    const j = html.indexOf(END, i);
    if (j < 0) return html;
    html = html.slice(0, i) + html.slice(j + END.length).replace(/^\r?\n/, '');
  }
}

function main() {
  let html = fs.readFileSync(HTML, 'utf8');
  const remove = process.argv.includes('--remove');

  html = stripBlock(html);

  if (remove) {
    fs.writeFileSync(HTML, html);
    console.log('已移除内嵌素材，回退到纯程序化精灵。');
    return;
  }

  const { body, total, animCount } = buildBlock();
  const anchor = 'function buildSprites(){';
  if (!html.includes(anchor)) throw new Error('找不到 buildSprites 锚点');
  html = html.replace(anchor, body + '\n' + anchor);

  // 让白闪帧兼容 HTMLImageElement（没有 width 属性时用 naturalWidth）
  html = html.replace(
    'function whiteSprite(canvas){\n  const c = document.createElement(\'canvas\');\n  c.width = canvas.width; c.height = canvas.height;',
    'function whiteSprite(canvas){\n  const c = document.createElement(\'canvas\');\n  c.width = canvas.naturalWidth || canvas.width;\n  c.height = canvas.naturalHeight || canvas.height;'
  );

  // init 里加载完素材后覆盖并重绘图标。
  // 必须放在 Game.reset() 之后：回调里要读 Game.player，
  // 不能依赖"图片解码一定比 init 慢"这种假设。
  html = html.replace(/\n[ \t]*loadArt\(\(\) => \{[^\n]*\n?/g, '\n');
  const anchor2 = '  Game.reset();\n  updateCamera();\n  render();\n';
  if (!html.includes(anchor2)) throw new Error('找不到 init 里的 Game.reset 锚点');
  html = html.replace(
    anchor2,
    '  Game.reset();\n  updateCamera();\n  render();\n' +
    '  loadArt(() => { applyArt(); if (Game.player) { UI.renderSlots(); render(); } });\n'
  );

  fs.writeFileSync(HTML, html);
  console.log('内嵌素材 %d 张 + %d 序列帧，占 %s KB（base64）',
              Object.keys(MAP).length, animCount, (total / 1024).toFixed(1));
  console.log('index.html 现为 %s KB', (fs.statSync(HTML).size / 1024).toFixed(1));
}

main();
