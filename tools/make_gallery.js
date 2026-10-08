/**
 * 生成素材画廊 —— 单文件 HTML，base64 内嵌所有精灵，用来人工验收 AI 素材质量。
 * 用法: node tools/make_gallery.js
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SRC = path.join(ROOT, '_art', 'out');

const GROUPS = [
  { title: 'v2.4 · 可选角色（5 选 1）', items: [
    ['hero.png',      '全栈工程师（默认 / 程序化三向）'],
    ['hero_fe.png',   '前端切图仔 · 攻速↑ 生命↓'],
    ['hero_be.png',   '后端扛把子 · 生命↑ 护甲↑ 移速↓'],
    ['hero_ops.png',  '运维背锅侠 · 移速↑ 拾取↑ 攻速↓'],
    ['hero_qa.png',   '测试找茬王 · 经验↑ 伤害↓'],
  ]},
  { title: '玩家 / 敌人 / BOSS', items: [
    ['hero.png',           '程序员（玩家）'],
    ['enemy_npe.png',      '空指针异常'],
    ['enemy_leak.png',     '内存泄漏'],
    ['enemy_loop.png',     '死循环'],
    ['enemy_race.png',     '竞态条件'],
    ['enemy_deadlock.png', '线程死锁'],
    ['enemy_segfault.png', '段错误'],
    ['enemy_conflict.png', '依赖冲突'],
    ['boss_debt.png',      'BOSS · 技术债恶魔'],
    ['boss_require.png',   'BOSS · 需求变更兽'],
  ]},
  { title: 'v2.4 · 新增敌人 / BOSS', items: [
    ['enemy_worm.png',   '蠕虫病毒（分裂）'],
    ['enemy_inject.png', 'SQL 注入（突进）'],
    ['enemy_zombie.png', '僵尸进程（厚血慢速）'],
    ['enemy_cache.png',  '缓存雪崩（突进 · 后期）'],
    ['boss_prod.png',    'BOSS · 线上 P0 事故（9.3 分钟）'],
  ]},
  { title: '道具 / 掉落', items: [
    ['gem.png',    '经验宝石'],
    ['chest.png',  '宝箱'],
    ['coffee.png', '咖啡（回血）'],
    ['magnet.png', '全局搜索（吸附）'],
    ['bomb.png',   '炸弹'],
    ['clock.png',  '时钟（冻结）'],
  ]},
  { title: 'v2.4 · 新增被动图标', items: [
    ['item_ai.png',     'Copilot 助手 · 伤害 +12%'],
    ['item_shield.png', 'WAF 防火墙 · 定时护盾'],
    ['item_backup.png', '代码备份 · 倒下时回滚复活'],
  ]},
  { title: 'v2.5 · 新增敌人 / BOSS', items: [
    ['enemy_frag.png',  '内存碎片（高速小怪）'],
    ['enemy_stack.png', '栈溢出（突进）'],
    ['enemy_cors.png',  '跨域请求（远程风筝）'],
    ['boss_rmrf.png',   'BOSS · 删库魔君（3.3 分钟）'],
  ]},
  { title: 'v2.6 · 武器专属贴图（弹道 + 图标共用）', items: [
    ['shot_log.png',      'print 调试 · 终端日志弹'],
    ['shot_aura.png',     '断点光环 · 光环图标'],
    ['shot_orb.png',      '单元测试 · 测试通过球'],
    ['shot_regex.png',     '正则散射 · 星爆弹'],
    ['shot_undo.png',      'Ctrl+Z 回滚 · 回旋箭'],
    ['shot_hammer.png',    '重构巨锤 · 飞锤'],
    ['shot_mine.png',     '编译报错 · 地雷（本体同步重绘）'],
    ['shot_push.png',     'Git Push · 推送箭'],
    ['shot_overflow.png', '栈溢出 · 栈块弹'],
    ['shot_review.png',   '代码评审 · 评论气泡'],
    ['shot_docker.png',   'Docker 容器 · 集装箱'],
    ['turret.png',        'Docker 炮台（本体同步重绘）'],
  ]},
  { title: '武器实体 / 特效', items: [
    ['mine.png',   '地雷（编译报错）'],
    ['turret.png', 'Docker 炮台'],
    ['boom.png',   '爆炸贴图（单帧 + 代码动画）'],
  ]},
  { title: '背景', tile: true, items: [
    ['bg_tile.png', 'PCB 电路板地砖'],
  ]},
];

// 子弹用灰度贴图 + 运行时染色，这里用同样的算法把各武器的实际配色渲染出来验收
const TINT_DEMO = [
  ['log', 'print 调试', '#38bdf8'],
  ['regex', '正则散射', '#fbbf24'],
  ['hammer', '重构巨锤', '#fb923c'],
  ['mine', '编译报错', '#ef4444'],
  ['push', 'Git Push', '#22d3ee'],
  ['undo', 'Ctrl+Z 回滚', '#f472b6'],
  ['aura', '断点光环', '#a78bfa'],
  ['orb', '单元测试', '#4ade80'],
];

function uri(f) {
  return 'data:image/png;base64,' + fs.readFileSync(path.join(SRC, f)).toString('base64');
}

function card(file, label) {
  const u = uri(file);
  return `
    <div class="card">
      <div class="big"><img src="${u}" alt="${label}"></div>
      <div class="nm">${label}</div>
      <div class="row">
        <span class="lab">游戏内</span>
        <span class="mini dark"><img src="${u}" alt=""></span>
        <span class="mini mid"><img src="${u}" alt=""></span>
      </div>
    </div>`;
}

function tileCard(file, label) {
  const u = uri(file);
  // 三块并排：砖本身 / 3x3 平铺看接缝 / 模拟游戏内压暗后的样子
  return `
    <div class="tilewrap">
      <div class="tcard">
        <div class="t single" style="background-image:url(${u})"></div>
        <div class="tn">单块 128px</div>
      </div>
      <div class="tcard">
        <div class="t repeat" style="background-image:url(${u})"></div>
        <div class="tn">3×3 平铺（看有没有缝）</div>
      </div>
      <div class="tcard">
        <div class="t repeat game"><div class="inner" style="background-image:url(${u})"></div></div>
        <div class="tn">游戏内实际亮度</div>
      </div>
      <div class="tlabel">${label}</div>
    </div>`;
}

const html = `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>BUG 幸存者 · AI 像素素材验收</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;background:#070b14;color:#e6edf7;
    font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;padding:26px 30px 40px}
  h1{font-size:22px;margin:0 0 4px;letter-spacing:1px}
  .sub{font-size:12.5px;color:#7f93b3;margin-bottom:22px;line-height:1.7}
  h2{font-size:14px;color:#7dd3fc;margin:24px 0 12px;letter-spacing:1px;
    border-left:3px solid #22d3ee;padding-left:9px}
  .grid{display:flex;flex-wrap:wrap;gap:14px}
  .card{width:150px;background:rgba(255,255,255,.04);border:1px solid rgba(120,160,255,.16);
    border-radius:12px;padding:12px 10px 10px;text-align:center}
  .big{height:104px;display:flex;align-items:center;justify-content:center;
    background:radial-gradient(ellipse at center,rgba(56,189,248,.10),rgba(0,0,0,0) 70%);
    border-radius:8px}
  .big img{image-rendering:pixelated;height:96px;width:96px;object-fit:contain}
  .nm{font-size:12px;font-weight:700;margin-top:9px;letter-spacing:.5px}
  .row{margin-top:8px;display:flex;align-items:center;justify-content:center;gap:7px}
  .lab{font-size:10px;color:#63779a}
  .mini{width:26px;height:26px;border-radius:5px;display:flex;align-items:center;justify-content:center}
  .mini img{image-rendering:pixelated;width:20px;height:20px;object-fit:contain}
  .dark{background:#0b1220}.mid{background:#3a4a63}
  .note{margin-top:26px;font-size:12px;color:#8fa3c0;line-height:1.8;
    border-top:1px solid rgba(120,160,255,.14);padding-top:14px}
  .tilewrap{display:flex;gap:14px;align-items:flex-end;flex-wrap:wrap;
    background:rgba(255,255,255,.04);border:1px solid rgba(120,160,255,.16);
    border-radius:12px;padding:14px}
  .tcard{text-align:center}
  .t{border-radius:8px;background-size:128px 128px;image-rendering:pixelated}
  .t.single{width:128px;height:128px}
  .t.repeat{width:288px;height:216px;background-repeat:repeat}
  .t.game{position:relative;overflow:hidden}
  .t.game .inner{position:absolute;left:0;top:0;width:100%;height:100%;
    background-size:128px 128px;background-repeat:repeat}
  .t.game::after{content:'';position:absolute;left:0;top:0;width:100%;height:100%;
    background:rgba(4,7,14,.30)}
  .t.game::before{content:'';position:absolute;left:0;top:0;width:100%;height:100%;
    background:radial-gradient(ellipse at center,rgba(4,7,14,0) 18%,rgba(4,7,14,.38) 78%);z-index:2}
  .tn{font-size:11px;color:#8fa3c0;margin-top:7px}
  .tlabel{font-size:12px;font-weight:700;margin-left:6px;color:#7dd3fc}
  .graybox{width:128px;height:128px;border-radius:8px;display:flex;align-items:center;
    justify-content:center;background:#151b26}
  .graybox img{image-rendering:pixelated;width:96px;height:96px;object-fit:contain}
  .sw{width:12px;height:12px;border-radius:3px;display:inline-block}
  .playbox{width:150px;height:150px;border-radius:8px;display:flex;align-items:center;
    justify-content:center;background:#151b26}
  .playbox img{image-rendering:pixelated;height:120px;object-fit:contain}
  .filmstrip{max-width:560px;display:flex;flex-wrap:wrap;gap:3px;align-items:center}
  .filmstrip img{image-rendering:pixelated;height:64px}
  .filmstrip .gap{width:14px}
  .pb{background:rgba(255,255,255,.10);border:1px solid rgba(120,160,255,.3);
    color:#cfe0f5;border-radius:6px;padding:2px 9px;font-size:11px;cursor:pointer;
    font-family:inherit}
  .pb:hover{background:rgba(255,255,255,.18)}
</style></head><body>
<h1>BUG 幸存者 · AI 像素素材</h1>
<div class="sub">
  全部由 AI 生成后经统一后处理：抠背景 → 硬像素 alpha → 统一深色描边 → 24 色量化 → 索引色压缩。<br>
  左侧大图是放大 4 倍的样子，右下两个小方块是它在游戏里分别在暗背景 / 亮地面上的实际尺寸。
</div>
${GROUPS.map(gp => `<h2>${gp.title}</h2><div class="grid">${
  gp.tile ? gp.items.map(([f, l]) => tileCard(f, l)).join('')
          : gp.items.map(([f, l]) => card(f, l)).join('')
}</div>`).join('')}
<h2>爆炸序列帧（来自 GIF，16 帧重排）</h2>
<div class="tilewrap">
  <div class="tcard">
    <div class="playbox"><img id="bp" alt="爆炸播放"></div>
    <div class="tn"><button id="bt" class="pb">暂停</button> 循环播放</div>
  </div>
  <div class="tcard">
    <div class="filmstrip" id="strip"></div>
    <div class="tn">16 帧全展开</div>
  </div>
</div>
<script>
const BOOM = [${Array.from({length:16}, (_,i)=>JSON.stringify(uri(`anim/boom_${String(i).padStart(2,'0')}.png`))).join(',')}];
const FLAME = [${Array.from({length:4}, (_,i)=>JSON.stringify(uri(`anim/flame_${String(i).padStart(2,'0')}.png`))).join(',')}];
const bp = document.getElementById('bp');
let bi = 0, playing = true, timer = null;
function tick(){ bi = (bi + 1) % BOOM.length; bp.src = BOOM[bi]; }
function start(){ timer = setInterval(tick, 62); }
function stop(){ clearInterval(timer); timer = null; }
bp.src = BOOM[0]; start();
document.getElementById('bt').onclick = function(){
  playing = !playing;
  this.textContent = playing ? '暂停' : '播放';
  playing ? start() : stop();
};
document.getElementById('strip').innerHTML =
  BOOM.map(u => '<img src="' + u + '" style="height:64px">').join('') +
  '<span class="gap"></span>' +
  FLAME.map(u => '<img src="' + u + '" style="height:64px">').join('');
</script>
<h2>子弹 · 灰度贴图 + 运行时染色</h2>
<div class="tilewrap">
  <div class="tcard">
    <div class="graybox"><img id="g0" alt="灰度原图"></div>
    <div class="tn">AI 灰度原图</div>
  </div>
  <div class="tcard">
    <div class="graybox"><img id="g1" alt="球体灰度图"></div>
    <div class="tn">能量球灰度图</div>
  </div>
</div>
<div class="grid" id="tints" style="margin-top:14px"></div>
<script>
const SHOT = '${uri('shot_energy.png')}';
const ORB  = '${uri('shot_orb.png')}';
const DEMO = ${JSON.stringify(TINT_DEMO)};
document.getElementById('g0').src = SHOT;
document.getElementById('g1').src = ORB;
function tint(src, color){
  const im = new Image(); im.src = src;
  return new Promise(res => {
    im.onload = () => {
      const c = document.createElement('canvas');
      c.width = im.naturalWidth; c.height = im.naturalHeight;
      const g = c.getContext('2d');
      g.drawImage(im, 0, 0);
      g.globalCompositeOperation = 'multiply';
      g.fillStyle = color; g.fillRect(0, 0, c.width, c.height);
      g.globalCompositeOperation = 'lighter';
      g.globalAlpha = 0.5; g.drawImage(im, 0, 0); g.globalAlpha = 1;
      g.globalCompositeOperation = 'destination-in';
      g.drawImage(im, 0, 0);
      res(c);
    };
  });
}
const useOrb = ${JSON.stringify(['orb', 'aura', 'overflow'])};
Promise.all(DEMO.map(([id, name, color]) =>
  tint(useOrb.indexOf(id) >= 0 ? ORB : SHOT, color).then(c => ({ name, color, c }))
)).then(list => {
  document.getElementById('tints').innerHTML = list.map(x => {
    const u = x.c.toDataURL();
    return '<div class="card"><div class="big"><img src="' + u +
      '" style="height:56px;width:56px"></div>' +
      '<div class="nm">' + x.name + '</div>' +
      '<div class="row"><span class="sw" style="background:' + x.color + '"></span>' +
      '<span class="lab">' + x.color + '</span></div></div>';
  }).join('');
});
</script>
<div class="note">
  武器 / 被动的小图标仍是程序化生成的 —— 16px 下 AI 生成的图标会糊成一团，程序化的符号反而更清晰可读。<br>
  角色与道具走 AI 位图，图标走程序化，是刻意做的混合方案。
</div>
</body></html>`;

const out = path.join(ROOT, '_art', 'gallery.html');
fs.writeFileSync(out, html);
console.log('画廊已生成:', out, '(' + (fs.statSync(out).size / 1024).toFixed(1) + ' KB)');
