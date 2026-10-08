/**
 * 无头探针：快进一局，然后采样画布像素，确认实体真的画在屏幕上。
 * 用法: node tools/probe_play.js [秒数] [角色id]
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const sec = parseFloat(process.argv[2] || '45');
const hero = process.argv[3] || 'ops';

const probe = `
(function(){
  const T = window.__T, G = T.Game;
  G.heroId = ${JSON.stringify(hero)};
  T.UI.startGame();
  T.Input.axis = () => ({ x: Math.cos(G.t * 0.7), y: Math.sin(G.t * 0.9), len: 1 });
  for (let i = 0; i < ${sec} * 60; i++) {
    if (G.state === 'level') { T.UI.choose(0); continue; }
    if (G.state !== 'play') break;
    T.step(1/60);
  }
  T.updateCamera(); T.render();
  const cv = document.getElementById('game'), cx = cv.getContext('2d');
  const W = cv.width, H = cv.height;
  const out = ['画布 ' + W + 'x' + H];
  const sample = (px, py, rad) => {
    const a = cx.getImageData(Math.round(px - rad), Math.round(py - rad), rad * 2, rad * 2).data;
    let n = 0;
    for (let i = 0; i < a.length; i += 4) if (a[i] > 60 || a[i+1] > 60 || a[i+2] > 60) n++;
    return (100 * n / (a.length / 4)).toFixed(1) + '%';
  };
  out.push('中心(玩家位) ' + sample(W/2, H/2, 45));
  out.push('左上 ' + sample(W*0.25, H*0.3, 45));
  out.push('右下 ' + sample(W*0.75, H*0.7, 45));
  const r = cv.getBoundingClientRect();
  out.push('画布位置 (' + r.left.toFixed(0) + ',' + r.top.toFixed(0) + ') ' +
           r.width.toFixed(0) + 'x' + r.height.toFixed(0));
  out.push('虚拟视口 ' + T.LW + 'x' + T.LH);
  out.push('玩家世界 (' + G.player.x.toFixed(0) + ',' + G.player.y.toFixed(0) + ')');
  out.push('玩家屏幕 x' + (parseFloat(getComputedStyle(cv).width)));
  out.push('怪 ' + G.enemies.length + ' / 宝石 ' + G.gems.length + ' / 弹 ' + G.bullets.length);
  document.title = 'R::' + out.join(' | ');
})();
`;

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')
  .replace('</body>', '<script>setTimeout(function(){' + probe + '},1300)</script></body>');
const tmp = path.join(ROOT, '_dbg.html');
fs.writeFileSync(tmp, html);

const dom = execFileSync(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
  '--window-size=1280,760', '--virtual-time-budget=60000',
  '--dump-dom', 'file:///' + tmp.replace(/\\/g, '/'),
], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
fs.unlinkSync(tmp);
const m = dom.match(/R::([^<]*)/);
console.log(m ? m[1] : '（没拿到结果）');
