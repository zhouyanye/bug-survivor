/**
 * 无头截图：跑一段游戏内画面，用来人工/多模态验收美术与 HUD。
 * 用法: node tools/shot.js [秒数] [角色id] [难度id] [输出文件]
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const sec = parseFloat(process.argv[2] || '45');
const hero = process.argv[3] || 'dev';
const diff = process.argv[4] || 'normal';
const out = process.argv[5] || '_shot_play.png';

// 在页面里快进：开局 → 用简单绕圈 AI 跑 N 秒 → 定格渲染
const probe = `
(function(){
  const T = window.__T, G = T.Game;
  G.heroId = ${JSON.stringify(hero)};
  G.diffId = ${JSON.stringify(diff)};
  G.diff = T.DIFFS.find(d => d.id === G.diffId) || T.DIFFS[1];
  T.UI.startGame();
  let t = Math.cos(G.t);
  T.Input.axis = () => ({ x: Math.cos(G.t * 0.7), y: Math.sin(G.t * 0.9), len: 1 });
  const steps = Math.round(${sec} * 60);
  for (let i = 0; i < steps; i++) {
    if (G.state === 'level') { T.UI.choose(0); continue; }
    if (G.state !== 'play') break;
    try { T.step(1/60); } catch (e) { document.title = 'ERR::' + e.message; return; }
  }
  // 定格：把状态切出 'play'，主循环就不会再推进逻辑，但仍会每帧重绘
  // （不能直接 cancelAnimationFrame —— 截图前若发生 resize，画布被清空后就没人补画了）
  G.state = 'shot';
  try { T.updateCamera(); T.render(); T.UI.syncHud(); } catch (e) {}
  document.title = 'OK::' + G.t.toFixed(0) + 's Lv.' + G.player.lv
    + ' 怪' + G.enemies.length + ' 击杀' + G.kills;
})();
`;

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')
  .replace('</body>', '<script>setTimeout(function(){' + probe + '},1300)</script></body>');
const tmp = path.join(ROOT, '_shot.html');
fs.writeFileSync(tmp, html);

execFileSync(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
  '--window-size=1280,760', '--virtual-time-budget=60000',
  '--screenshot=' + path.join(ROOT, out),
  'file:///' + tmp.replace(/\\/g, '/'),
], { stdio: ['ignore', 'ignore', 'ignore'] });
fs.unlinkSync(tmp);
console.log('已截图 -> ' + out + '（角色 ' + hero + ' / ' + diff + ' / ' + sec + 's）');
