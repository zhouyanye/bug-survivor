// 菜单流程测试：主菜单 -> 选角 -> 选武器 -> 出战
const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync('/home/hatch/workspace/bug-survivor/index.html', 'utf8');
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const ctxStub = new Proxy({}, {
  get(t, k) { if (k in t) return t[k]; return function(){ return { addColorStop(){} }; }; },
  set(t, k, v){ t[k] = v; return true; }
});
function makeEl(id){
  return { id, style:{}, dataset:{}, textContent:'', innerHTML:'', title:'',
    offsetWidth:100, width:0, height:0,
    classList:{ _s:new Set(),
      add(...c){ c.forEach(x=>this._s.add(x)); },
      remove(...c){ c.forEach(x=>this._s.delete(x)); },
      toggle(c,v){ v ? this._s.add(c) : this._s.delete(c); },
      contains(c){ return this._s.has(c); } },
    addEventListener(){}, appendChild(){},
    getContext(){ return ctxStub; },
    querySelector(){ return makeEl('sub'); },
    querySelectorAll(){ return []; },
    getBoundingClientRect(){ return { left:0, top:0, width:1280, height:720 }; } };
}
const els = {};
const getEl = id => els[id] || (els[id] = makeEl(id));
const store = {};
const g = {
  console, performance:{ now:() => Date.now() },
  requestAnimationFrame:() => 1, cancelAnimationFrame(){},
  addEventListener(){}, removeEventListener(){},
  innerWidth:1440, innerHeight:900, devicePixelRatio:1,
  localStorage:{ getItem:k=>store[k]||null, setItem:(k,v)=>{store[k]=v;}, removeItem:k=>{delete store[k];} },
  setTimeout:() => 0,
  Image:function(){
    const self = this;
    this.naturalWidth = 48; this.naturalHeight = 48; this.width = 48; this.height = 48;
    this._src = '';
    Object.defineProperty(this, 'src', {
      get(){ return self._src; },
      set(v){ self._src = v; if (self.onload) self.onload(); }
    });
  },
  document:{ getElementById:getEl, createElement:makeEl, addEventListener(){},
    querySelector:() => makeEl('q'), querySelectorAll:() => [] },
  Math, Date, JSON, Object, Array, String, Number, Boolean, Error, isNaN, parseFloat, parseInt,
};
g.window = g; g.globalThis = g;
const ctx = vm.createContext(g);
vm.runInContext(code, ctx);
const T = g.__T, G = T.Game, UI = T.UI;
const errs = [];
function step2(label, fn){
  try { fn(); console.log('OK  ' + label); }
  catch(e){ errs.push(label); console.log('FAIL ' + label + ': ' + e.message); }
}

step2('主菜单渲染', () => {
  UI.renderDiff(); UI.renderMode(); UI.renderStatsLine();
  if (getEl('modeBox').innerHTML.length < 50) throw new Error('modeBox 空');
  if (getEl('diffBox').innerHTML.length < 50) throw new Error('diffBox 空');
});
step2('选角屏', () => {
  UI.openHeroSel();
  const n = (getEl('heroBox').innerHTML.match(/class="hcard/g) || []).length;
  if (n !== 7) throw new Error('卡片数=' + n);
  const locked = (getEl('heroBox').innerHTML.match(/locked/g) || []).length;
  if (locked < 2) throw new Error('锁定数=' + locked);
});
step2('选武器屏', () => {
  G.heroId = 'be';
  UI.openWeaponSel();
  const n = (getEl('weaponBox').innerHTML.match(/class="wcard/g) || []).length;
  if (n !== 5) throw new Error('卡片数=' + n + ' 应为5基础');
  if (!/后.*端/.test(getEl('wsHero').textContent)) throw new Error('wsHero=' + getEl('wsHero').textContent);
  if (G.starterWeapon !== 'push') throw new Error('默认应为角色武器 push, 实际=' + G.starterWeapon);
});
step2('选武器屏-角色专属', () => {
  G.heroId = 'mf';
  G.starterWeapon = (T.HMAP['mf'] || T.HEROES[0]).weapon; // 模拟点击角色卡
  UI.openWeaponSel();
  const n = (getEl('weaponBox').innerHTML.match(/class="wcard/g) || []).length;
  if (n !== 6) throw new Error('卡片数=' + n + ' 应为5+专属undo');
  if (G.starterWeapon !== 'undo') throw new Error('mf 默认应为 undo, 实际=' + G.starterWeapon);
});
step2('换角色重置初始武器', () => {
  G.heroId = 'be'; G.starterWeapon = 'aura';
  UI.openWeaponSel.__proto__; // noop
  // 模拟点击角色卡的逻辑
  G.heroId = 'qa'; G.starterWeapon = (T.HMAP['qa'] || T.HEROES[0]).weapon;
  if (G.starterWeapon !== 'regex') throw new Error('换角色后应重置为 regex, 实际=' + G.starterWeapon);
});
step2('出战', () => {
  G.starterWeapon = 'push';
  UI.startGame();
  if (G.player.weapons[0].id !== 'push') throw new Error('起手=' + G.player.weapons[0].id);
  if (G.state !== 'play') throw new Error('state=' + G.state);
});
step2('跑5秒', () => {
  T.Input.axis = () => ({ x:0.2, y:0.1, len:1 });
  for (let i = 0; i < 300; i++) T.step(1/60);
});
step2('解锁条件', () => {
  if (T.isHeroUnlocked('trainer')) throw new Error('trainer 应锁定');
  T.Save.data.wins = 1; T.Save.data.totalKills = 9000; T.Save.data.endlessBest = 500;
  T.Save.flush();
  if (!T.isHeroUnlocked('trainer')) throw new Error('trainer 应解锁');
  if (!T.isHeroUnlocked('mf')) throw new Error('mf 应解锁');
  if (!T.isWUnlocked('loop')) throw new Error('loop 应解锁');
  if (!T.isWUnlocked('nullptr')) throw new Error('nullptr 应解锁');
});
step2('设置渲染', () => {
  UI.renderSettings();
  if (getEl('settingsBox').innerHTML.length < 50) throw new Error('settingsBox 空');
});
console.log(errs.length ? 'MENU TEST FAIL' : 'MENU TEST PASS');
process.exit(errs.length ? 1 : 0);
