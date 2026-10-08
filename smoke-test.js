// 无头冒烟测试：用最小 DOM/Canvas stub 驱动游戏逻辑跑满一局
// 用法: node smoke-test.js [局数]
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];

// ---- Canvas 2D stub ----
const ctxStub = new Proxy({}, {
  get(t, k) {
    if (k in t) return t[k];
    return function(){ return { addColorStop(){} }; };
  },
  set(t, k, v){ t[k] = v; return true; }
});

// ---- 通用元素 stub ----
function makeEl(id) {
  return {
    id, style:{}, dataset:{}, textContent:'', innerHTML:'', title:'',
    offsetWidth: 100, width: 0, height: 0,
    classList:{ _s:new Set(),
      add(...c){ c.forEach(x=>this._s.add(x)); },
      remove(...c){ c.forEach(x=>this._s.delete(x)); },
      toggle(c,v){ v ? this._s.add(c) : this._s.delete(c); },
      contains(c){ return this._s.has(c); } },
    addEventListener(){}, appendChild(){},
    getContext(){ return ctxStub; },
    querySelector(){ return makeEl('sub'); },
    querySelectorAll(){ return []; },
    getBoundingClientRect(){ return { left:0, top:0, width:960, height:540 }; },
  };
}
const els = {};
function getEl(id){ if (!els[id]) els[id] = makeEl(id); return els[id]; }

const store = {};
const g = {
  console,
  performance: { now: () => Date.now() },
  requestAnimationFrame: () => 1,
  cancelAnimationFrame(){},
  addEventListener(){}, removeEventListener(){},
  innerWidth: 1440, innerHeight: 900, devicePixelRatio: 1,
  localStorage: { getItem:k=>store[k]||null, setItem:(k,v)=>{store[k]=v;}, removeItem:k=>{delete store[k];} },
  setTimeout: () => 0,
  // 内嵌精灵用的 Image：给 src 赋值时同步回调 onload，
  // 这样 loadArt/applyArt 这条覆盖路径也能被测到（不会真解码，只验逻辑不抛错）
  Image: function(){
    const self = this;
    this.naturalWidth = 48; this.naturalHeight = 48;
    this.width = 48; this.height = 48;
    this._src = '';
    Object.defineProperty(this, 'src', {
      get(){ return self._src; },
      set(v){ self._src = v; if (self.onload) self.onload(); }
    });
  },
  document: {
    getElementById: getEl,
    createElement: makeEl,
    addEventListener(){},
    querySelector: () => makeEl('q'),
    querySelectorAll: () => [],
  },
  Math, Date, JSON, Object, Array, String, Number, Boolean, Error, isNaN, parseFloat, parseInt,
};
g.window = g; g.globalThis = g;

vm.runInContext(code, vm.createContext(g));
const T = g.__T, G = T.Game;

const errors = [];
function guard(label, fn){ try { fn(); } catch(e){ errors.push(label + ': ' + e.message); } }

// ---- 类真人 AI：逃离怪群 + 顺路捡宝石 + 靠近宝箱 ----
function makeAI(){
  return function(){
    const p = G.player;
    let sx = 0, sy = 0;
    for (const e of G.enemies) {
      const dx = p.x - e.x, dy = p.y - e.y, d2 = dx*dx + dy*dy;
      if (d2 < 240*240 && d2 > 1) { const d = Math.sqrt(d2), w = (240 - d) / 240;
        sx += dx/d*w*w; sy += dy/d*w*w; }
    }
    for (const g2 of G.gems) {
      const dx = g2.x - p.x, dy = g2.y - p.y, d2 = dx*dx + dy*dy;
      if (d2 < 320*320 && d2 > 1) { const d = Math.sqrt(d2); sx += dx/d*0.35; sy += dy/d*0.35; }
    }
    for (const c of G.chests) {
      if (c.dead) continue;
      const dx = c.x - p.x, dy = c.y - p.y, d2 = dx*dx + dy*dy;
      if (d2 < 460*460 && d2 > 1) { const d = Math.sqrt(d2); sx += dx/d*0.42; sy += dy/d*0.42; }
    }
    if (Math.abs(p.x) > 1900) sx -= Math.sign(p.x) * 1.4;
    if (Math.abs(p.y) > 1900) sy -= Math.sign(p.y) * 1.4;
    const m = Math.hypot(sx, sy);
    if (m < 0.001) return { x:Math.cos(G.t), y:Math.sin(G.t), len:1 };
    return { x:sx/m, y:sy/m, len:1 };
  };
}

// ---- 跑一局 ----
function runOne(diffId, verbose){
  errors.length = 0;                       // 每局独立统计，避免错误串场
  G.diffId = diffId || 'normal';
  G.diff = T.DIFFS.find(d => d.id === G.diffId) || T.DIFFS[1];
  T.UI.startGame();
  T.Input.axis = makeAI();
  let frames = 0, levelUps = 0, maxEnemies = 0, dashes = 0;
  const dt = 1/60;
  while ((G.state === 'play' || G.state === 'level') && frames < 60*700) {
    if (G.state === 'level') { T.UI.choose(0); levelUps++; continue; }
    const p = G.player;
    let near = 0;
    for (const e of G.enemies) { const dx=e.x-p.x, dy=e.y-p.y; if (dx*dx+dy*dy < 90*90) near++; }
    if (near >= 4 && p.dashCd <= 0) { T.Input.keys.ShiftLeft = true; dashes++; }
    else T.Input.keys.ShiftLeft = false;
    guard('step', () => T.step(dt));
    frames++;
    maxEnemies = Math.max(maxEnemies, G.enemies.length);
    if (errors.length) break;
  }
  guard('render', () => { T.updateCamera(); T.render(); });

  const res = {
    diff: G.diffId, t: G.t, lv: G.player.lv, levelUps,
    kills: G.kills, dmg: G.dmgDealt, maxEnemies, dashes,
    chests: G.chestsOpen, comboMax: G.comboMax, tp: G.tp, boss: G.bossSpawned,
    win: G.t >= T.RUN_TIME,
    weapons: G.player.weapons.map(w => w.id + ':' + w.lv).join(' '),
    passives: G.player.passives.map(b => b.id + ':' + b.lv).join(' '),
  };
  if (verbose) {
    console.log('  [' + res.diff + '] ' + (res.win ? '通关 ✔' : '阵亡 ✘') +
      ' @ ' + res.t.toFixed(0) + 's | Lv.' + res.lv + ' (升级' + res.levelUps + ')' +
      ' | 击杀 ' + res.kills + ' | 连击峰 ' + res.comboMax + ' | 宝箱 ' + res.chests +
      ' | BOSS ' + res.boss + ' | 同屏峰 ' + res.maxEnemies);
    console.log('        武器 ' + res.weapons);
    console.log('        被动 ' + (res.passives || '无'));
  }
  return res;
}

// ---- 主流程 ----
const runs = Math.max(1, parseInt(process.argv[2] || '3', 10));
console.log('BUG 幸存者 v2 · 无头冒烟测试（normal ' + runs + ' 局 + hell 1 局）');
console.log('开局 HP = ' + G.player.hp + ' | 起手武器 = ' + G.player.weapons.map(w=>w.id).join(','));

const all = [];
for (let i = 0; i < runs; i++) all.push(runOne('normal', true));

for (const d of ['easy','hard','hell']) {
  const r = runOne(d, false);
  console.log('  [' + d.padEnd(6) + '] ' + (r.win ? '通关 ✔' : '阵亡 ✘') + ' @ ' +
    r.t.toFixed(0) + 's | Lv.' + r.lv + ' | 击杀 ' + r.kills + ' | 同屏峰 ' + r.maxEnemies);
}

// ---- 角色平衡巡检：每个角色各跑一局 normal ----
console.log('--- 角色巡检 ---');
const heroRes = {};
for (const h of T.HEROES) {
  G.heroId = h.id;
  const r = runOne('normal', false);
  heroRes[h.id] = r;
  console.log('  [' + h.id.padEnd(4) + '] ' + (r.win ? '通关 ✔' : '阵亡 ✘') +
    ' @ ' + r.t.toFixed(0) + 's | Lv.' + r.lv + ' | 击杀 ' + r.kills +
    ' | 起手 ' + r.weapons.split(' ')[0]);
}
G.heroId = 'dev';

console.log('---');
const wins = all.filter(r => r.win).length;
const avgT = all.reduce((s, r) => s + r.t, 0) / all.length;
const avgLv = all.reduce((s, r) => s + r.lv, 0) / all.length;
console.log('normal 通关率   ' + wins + '/' + runs);
console.log('平均存活       ' + avgT.toFixed(0) + 's / 600s');
console.log('平均等级       Lv.' + avgLv.toFixed(1));
console.log('逻辑错误       ' + (errors.length ? errors.join(' | ') : '无'));

const ok = errors.length === 0 && all.every(r => r.kills > 40) &&
  T.HEROES.every(h => heroRes[h.id].kills > 40);
console.log('\n结果: ' + (ok ? 'PASS ✔' : 'FAIL ✘'));
process.exit(ok ? 0 : 1);
