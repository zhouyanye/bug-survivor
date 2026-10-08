// 一次性体检：无头浏览器里验证角色选择条 / 角色属性 / 新素材是否真的挂上
// 用法: node tools/check_heroes.js
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const probe = `
(function(){
  const out = [];
  const cards = [...document.querySelectorAll('#heroBox .hcard')];
  out.push('英雄卡=' + cards.length);
  const hb = document.getElementById('heroBox'), st = document.getElementById('start');
  const r = hb.getBoundingClientRect(), sr = st.getBoundingClientRect();
  out.push('布局 角色条' + Math.round(r.width) + 'x' + Math.round(r.height)
      + ' / 开始屏' + Math.round(sr.width) + 'x' + Math.round(sr.height)
      + ' / 内容高' + st.scrollHeight + ' 可视高' + st.clientHeight
      + ' / 溢出=' + (r.width > sr.width + 1 || st.scrollHeight > st.clientHeight + 1 ? '有!⚠' : '无'));
  out.push('各块高度 ' + [...st.children].map(c =>
    (c.className || c.tagName) + '=' + Math.round(c.getBoundingClientRect().height)).join(' | '));
  out.push('三块面板 ' + [...document.querySelectorAll('#start .panels > .pnl')].map(p =>
    p.querySelector('h3').textContent.trim() + '=' + Math.round(p.getBoundingClientRect().height)).join(' | '));
  out.push('解锁条=' + Math.round(document.getElementById('unlockBox').getBoundingClientRect().height)
      + ' 解锁内容=' + document.getElementById('unlockBox').scrollHeight
      + ' 玩法文=' + Math.round(document.querySelector('#start .pnl:nth-child(2) .descmini').getBoundingClientRect().height));
  out.push('默认选中=' + ((document.querySelector('#heroBox .hcard.on')||{dataset:{}}).dataset.h));
  out.push('卡片=' + cards.map(c => c.dataset.h + '/' + c.querySelector('.hn').textContent.trim()
      + '/' + c.querySelector('.hw').textContent.trim()
      + '/' + c.querySelector('canvas').width + 'px').join(' | '));
  const shot = h => {
    document.querySelector('#heroBox .hcard[data-h="' + h + '"]').click();
    __T.Game.reset();
    const P = __T.Game.player;
    return h + ': HP' + P.maxHp + ' 速' + P.speed.toFixed(0) + ' 攻速' + P.asp
      + ' 伤' + P.dmgMult + ' 经验' + P.expMult.toFixed(2) + ' 拾取' + P.pickup.toFixed(0)
      + ' 甲' + P.armor + ' 起手[' + P.weapons.map(w => w.id).join(',') + ']';
  };
  ['dev','fe','be','ops','qa'].forEach(h => out.push(shot(h)));
  out.push('数量 英雄' + __T.HEROES.length + ' 敌人' + __T.ENEMIES.length
      + ' BOSS' + __T.BOSS_DEFS.length + ' 被动' + __T.PASSIVES.length);
  out.push('新敌人图=' + ['worm','inject','zombie','cache']
      .map(i => i + (!!__T.SPR['e_' + i] ? '✔' : '✘')).join(' '));
  out.push('BOSS图=' + __T.BOSS_DEFS.map(b => b.id + (!!__T.SPR['e_' + b.id] ? '✔' : '✘')).join(' '));
  out.push('角色图=' + __T.HEROES.map(h => h.id + (h.spr ? (!!__T.SPR[h.spr] ? '✔' : '✘') : 'proc')).join(' '));
  out.push('被动图标=' + ['ai','shield','backup'].map(i => i + (!!__T.SPR['i_' + i] ? '✔' : '✘')).join(' '));
  out.push('序列帧=' + (typeof ANIM !== 'undefined' ? JSON.stringify(ANIM) : '无'));
  document.title = 'R::' + out.join('\\n');
})();
`;

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')
  .replace('</body>', '<script>setTimeout(function(){' + probe + '},1200)</script></body>');
const tmp = path.join(ROOT, '_check.html');
fs.writeFileSync(tmp, html);

const dom = execFileSync(CHROME, [
  '--headless=new', '--disable-gpu', '--hide-scrollbars',
  '--window-size=1280,760', '--virtual-time-budget=5000',
  '--dump-dom', 'file:///' + tmp.replace(/\\/g, '/'),
], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });

fs.unlinkSync(tmp);
const m = dom.match(/R::([\s\S]*?)<\/title>/);
console.log(m ? m[1].replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>') : '（没拿到结果）');
