// 无尽模式逻辑验证
const fs = require('fs'), vm = require('vm');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
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
vm.runInContext(code, vm.createContext(g));
const T = g.__T, G = T.Game, S = T.Save;

// 模拟：开始界面选了无尽模式
S.data.mode = 'endless'; S.flush();
G.diffId = 'normal'; G.diff = T.DIFFS[1]; G.heroId = 'dev';
T.UI.startGame();
console.log('endless flag:', G.endless);

// 无敌跑过 600s，确认不会胜利结算
G.player.inv = 1e9;
T.Input.axis = () => ({ x:0.3, y:0.2, len:1 });
const dt = 1/60;
let bossAt600 = 0;
for (let i = 0; i < 640*60 && G.state === 'play'; i++){
  try { T.step(dt); } catch(e){ console.log('ERR @' + G.t.toFixed(1), e.message); break; }
  if (G.state === 'level') { try { T.UI.choose(0); } catch(e){ console.log('choose ERR', e.message); break; } }
  if (!bossAt600 && G.t >= 600) bossAt600 = G.bossSpawned;
}
console.log('t=' + G.t.toFixed(0), 'state=' + G.state, '(应为 play)');
console.log('600s时 bossSpawned=' + bossAt600, '结束时=' + G.bossSpawned);

// 死亡结算文字
G.player.inv = 0; G.player.hp = 1;
const e0 = G.enemies[0];
try {
  for (let i = 0; i < 600 && (G.state === 'play' || G.state === 'level'); i++) {
    if (G.state === 'level') { try { T.UI.choose(0); } catch(e){} continue; }
    T.step(dt);
  }
} catch(e){ console.log('die ERR', e.message); }
console.log('死后 state=' + G.state, 'title=' + getEl('overTitle').textContent,
  '| sub=' + getEl('overSub').textContent.slice(0, 34));
console.log('timeText=' + getEl('timeText').textContent, 'timeSub=' + getEl('timeSub').textContent);
