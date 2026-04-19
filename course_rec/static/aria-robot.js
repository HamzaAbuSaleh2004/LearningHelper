/**
 * ARIA — Animated Robot Learning Companion v3
 * =============================================
 * - Sits still by default (not distracting)
 * - Eyes always follow the mouse cursor
 * - Dances / shakes / bounces ONLY when an event is triggered
 *
 * SETUP (2 steps):
 *   1. Add a container div:      <div id="aria-stage"></div>
 *   2. Include this script:      <script src="aria-robot.js"></script>
 *
 * PUBLIC API:
 *   ARIA.correct()      — correct answer  (bounce + green particles + XP)
 *   ARIA.wrong()        — wrong answer    (shake + red particles)
 *   ARIA.hint()         — hint            (gentle bob + purple particles)
 *   ARIA.levelUp()      — level up        (dance + spin + gold particles)
 *   ARIA.idle()         — idle state      (slow bob, dimmed colors)
 *   ARIA.say(text)      — custom speech bubble
 *   ARIA.addXP(n)       — add n XP manually
 *
 * CUSTOMIZATION:
 *   Edit ARIA_CONFIG below — colors, messages, size, background.
 */

const ARIA_CONFIG = {
  containerId:  'aria-stage',
  stageHeight:  240,
  robotWidth:   75,
  robotHeight:  115,
  bgColor:      'transparent',
  starCount:    0,
  messages: {
    correct: ["YES! Nailed it!", "Perfect! +10 XP!", "You're on fire!", "Brilliant answer!"],
    wrong:   ["Hmm, not quite...", "Try again!", "Almost! Think harder.", "Don't give up!"],
    hint:    ["Hmm, let me think...", "Try breaking it down...", "What if...?", "Take your time."],
    levelup: ["LEVEL UP!!", "New level unlocked!", "Unstoppable!", "You're a genius!"],
    idle:    ["Zzz... tap me!", "Resting circuits...", "Wake me when ready!"],
    click:   ["Hey! That tickles!", "Tap again, I dare you!", "Hello there!", "My circuits!"],
    welcome: ["Hi! Move your cursor near me...", "Ready to learn together!"],
  },
};

(function () {

  const style = document.createElement('style');
  style.textContent = `
    #aria-stage {
      position: relative;
      width: 100%;
      height: ${ARIA_CONFIG.stageHeight}px;
      background: ${ARIA_CONFIG.bgColor};
      overflow: visible;
      cursor: default;
      font-family: system-ui, sans-serif;
    }
    #aria-stars  { position: absolute; inset: 0; pointer-events: none; }
    #aria-robot  {
      position: absolute;
      width: ${ARIA_CONFIG.robotWidth}px;
      height: ${ARIA_CONFIG.robotHeight}px;
      left: 50%; top: 50%;
      transform: translate(-50%, -60%);
      cursor: pointer;
      transition: filter 0.2s;
    }
    #aria-robot:hover { filter: brightness(1.15); }
    #aria-bubble {
      position: absolute;
      background: #fff;
      color: #0a0e1a;
      font-size: 13px;
      font-weight: 500;
      padding: 8px 13px;
      border-radius: 12px;
      max-width: 200px;
      text-align: center;
      line-height: 1.4;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.25s;
      z-index: 10;
      left: 50%;
      transform: translateX(-50%);
      top: 36px;
    }
    #aria-bubble::after {
      content: '';
      position: absolute;
      bottom: -7px; left: 50%;
      transform: translateX(-50%);
      border: 7px solid transparent;
      border-top: 7px solid #fff;
    }
    #aria-hud { position: absolute; top: 12px; left: 16px; display: flex; align-items: center; gap: 8px; }
    #aria-xp-track { width: 100px; height: 5px; background: rgba(255,255,255,0.12); border-radius: 3px; overflow: hidden; }
    #aria-xp-fill  { height: 100%; width: 30%; background: #378ADD; border-radius: 3px; transition: width 0.5s cubic-bezier(.4,0,.2,1); }
    #aria-xp-txt   { font-size: 11px; color: rgba(255,255,255,0.5); }
    #aria-streak   { position: absolute; top: 12px; right: 16px; font-size: 11px; color: rgba(255,255,255,0.5); }
    .aria-prt { position: absolute; border-radius: 50%; pointer-events: none; width: 6px; height: 6px; animation: ariaPoof 0.72s ease-out forwards; }
    @keyframes ariaPoof { 0%{opacity:1;transform:translate(0,0) scale(1)} 100%{opacity:0;transform:translate(var(--tx),var(--ty)) scale(0)} }
    @keyframes aria-bounce { 0%,100%{transform:translate(-50%,-60%)} 25%{transform:translate(-50%,-73%)} 50%{transform:translate(-50%,-58%)} 75%{transform:translate(-50%,-69%)} }
    @keyframes aria-shake  { 0%,100%{transform:translate(-50%,-60%)} 20%{transform:translate(-55%,-60%)} 40%{transform:translate(-45%,-60%)} 60%{transform:translate(-55%,-60%)} 80%{transform:translate(-45%,-60%)} }
    @keyframes aria-dance  { 0%,100%{transform:translate(-50%,-60%) rotate(0)} 15%{transform:translate(-53%,-65%) rotate(-8deg)} 30%{transform:translate(-47%,-65%) rotate(8deg)} 45%{transform:translate(-53%,-61%) rotate(-5deg)} 60%{transform:translate(-47%,-61%) rotate(5deg)} 75%{transform:translate(-50%,-65%) rotate(-3deg)} 90%{transform:translate(-50%,-57%) rotate(3deg)} }
    @keyframes aria-spin   { 0%{transform:translate(-50%,-60%) rotate(0)} 100%{transform:translate(-50%,-60%) rotate(360deg)} }
    @keyframes aria-think  { 0%,100%{transform:translate(-50%,-60%)} 50%{transform:translate(-50%,-64%)} }
  `;
  document.head.appendChild(style);

  function init() {
    const stage = document.getElementById(ARIA_CONFIG.containerId);
    if (!stage) { console.warn('ARIA: #' + ARIA_CONFIG.containerId + ' not found.'); return; }

    stage.innerHTML = `
      <canvas id="aria-stars"></canvas>
      <div id="aria-hud">
        <div id="aria-xp-track"><div id="aria-xp-fill"></div></div>
        <span id="aria-xp-txt">Lv1 · 30xp</span>
      </div>
      <div id="aria-streak"></div>
      <div id="aria-bubble"></div>
      <div id="aria-robot">
        <svg id="aria-svg" viewBox="0 0 110 170" xmlns="http://www.w3.org/2000/svg"
             width="${ARIA_CONFIG.robotWidth}" height="${ARIA_CONFIG.robotHeight}"></svg>
      </div>
    `;

    const robotEl  = document.getElementById('aria-robot');
    const svgEl    = document.getElementById('aria-svg');
    const bubbleEl = document.getElementById('aria-bubble');
    const canvas   = document.getElementById('aria-stars');
    const ctx      = canvas.getContext('2d');

    let W, H, stars = [];
    let mx = 0, my = 0;
    let mood = 'happy';
    let xp = 30, level = 1, streak = 0;
    let bubbleTimer = null;
    let blinkT = 0, antennaT = 0, chestT = 0;

    const MOOD_COLORS = {
      happy:   { body:'#1a2540', face:'#1e3a6e', eyes:'#378ADD', mouth:'smile',  chest:'#378ADD' },
      correct: { body:'#0f2d1a', face:'#1a4a2e', eyes:'#1D9E75', mouth:'grin',   chest:'#1D9E75' },
      wrong:   { body:'#2d1010', face:'#4a1a1a', eyes:'#E24B4A', mouth:'sad',    chest:'#E24B4A' },
      hint:    { body:'#1a1a3a', face:'#2a2a5e', eyes:'#7F77DD', mouth:'think',  chest:'#7F77DD' },
      levelup: { body:'#2d2000', face:'#4a3800', eyes:'#EF9F27', mouth:'grin',   chest:'#EF9F27' },
      idle:    { body:'#141820', face:'#1a2030', eyes:'#444441', mouth:'flat',   chest:'#333' },
    };

    function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

    function getEyeOffset(eyeCx, eyeCy) {
      const rect  = robotEl.getBoundingClientRect();
      const sRect = stage.getBoundingClientRect();
      const worldX = rect.left - sRect.left + eyeCx * (rect.width  / 110);
      const worldY = rect.top  - sRect.top  + eyeCy * (rect.height / 170);
      const dx = mx - worldX, dy = my - worldY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const maxR = 2.5;
      if (dist === 0) return { ox: 0, oy: 0 };
      return {
        ox: (dx / dist) * Math.min(maxR, dist / 28),
        oy: (dy / dist) * Math.min(maxR, dist / 28),
      };
    }

    function buildRobot(m) {
      const c = MOOD_COLORS[m] || MOOD_COLORS.happy;
      const blink = Math.sin(blinkT) > 0.97 ? 0.08 : 1;
      const aY    = (Math.sin(antennaT) * 3).toFixed(1);
      const cg    = (0.6 + Math.sin(chestT) * 0.35).toFixed(2);
      const mouths = { smile:'M38 66 Q55 76 72 66', grin:'M35 64 Q55 78 75 64', sad:'M38 72 Q55 64 72 72', think:'M40 68 Q55 68 70 68', flat:'M40 68 L70 68' };
      const mp = mouths[c.mouth] || mouths.smile;
      const e1 = getEyeOffset(38, 50);
      const e2 = getEyeOffset(65, 50);
      svgEl.innerHTML = `
        <g transform="translate(0,${aY})">
          <line x1="55" y1="6" x2="55" y2="24" stroke="#444" stroke-width="2" stroke-linecap="round"/>
          <circle cx="55" cy="5" r="5" fill="${c.eyes}" opacity="0.9"/>
          <circle cx="55" cy="5" r="2.5" fill="#fff" opacity="0.5"/>
        </g>
        <rect x="22" y="24" width="66" height="58" rx="14" fill="${c.body}"/>
        <rect x="27" y="28" width="56" height="50" rx="11" fill="${c.face}"/>
        <g transform="scale(1,${blink})" style="transform-origin:38px 50px">
          <rect x="31" y="43" width="14" height="14" rx="4" fill="${c.body}"/>
          <rect x="33" y="45" width="10" height="10" rx="2.5" fill="${c.eyes}"/>
          <circle cx="${(41+e1.ox).toFixed(2)}" cy="${(49+e1.oy).toFixed(2)}" r="2.5" fill="#fff" opacity="0.9"/>
          <circle cx="${(42+e1.ox*0.7).toFixed(2)}" cy="${(50+e1.oy*0.7).toFixed(2)}" r="1.2" fill="#000" opacity="0.55"/>
        </g>
        <g transform="scale(1,${blink})" style="transform-origin:65px 50px">
          <rect x="58" y="43" width="14" height="14" rx="4" fill="${c.body}"/>
          <rect x="60" y="45" width="10" height="10" rx="2.5" fill="${c.eyes}"/>
          <circle cx="${(68+e2.ox).toFixed(2)}" cy="${(49+e2.oy).toFixed(2)}" r="2.5" fill="#fff" opacity="0.9"/>
          <circle cx="${(69+e2.ox*0.7).toFixed(2)}" cy="${(50+e2.oy*0.7).toFixed(2)}" r="1.2" fill="#000" opacity="0.55"/>
        </g>
        <path d="${mp}" fill="none" stroke="${c.eyes}" stroke-width="2.5" stroke-linecap="round"/>
        <circle cx="22" cy="53" r="5" fill="${c.body}" stroke="#333" stroke-width="0.5"/>
        <circle cx="88" cy="53" r="5" fill="${c.body}" stroke="#333" stroke-width="0.5"/>
        <rect x="47" y="82" width="16" height="9" rx="3" fill="#333"/>
        <rect x="14" y="91" width="18" height="46" rx="8" fill="${c.body}"/>
        <circle cx="23" cy="140" r="7" fill="${c.face}"/>
        <rect x="78" y="91" width="18" height="46" rx="8" fill="${c.body}"/>
        <circle cx="87" cy="140" r="7" fill="${c.face}"/>
        <rect x="18" y="91" width="74" height="58" rx="10" fill="${c.body}"/>
        <rect x="25" y="98" width="60" height="44" rx="7" fill="${c.face}"/>
        <circle cx="55" cy="113" r="9" fill="${c.chest}" opacity="${cg}"/>
        <circle cx="55" cy="113" r="4.5" fill="#fff" opacity="0.3"/>
        <rect x="28" y="130" width="14" height="5" rx="2.5" fill="${c.body}" opacity="0.7"/>
        <rect x="46" y="130" width="14" height="5" rx="2.5" fill="${c.body}" opacity="0.7"/>
        <rect x="64" y="130" width="14" height="5" rx="2.5" fill="${c.body}" opacity="0.7"/>
        <rect x="36" y="149" width="18" height="20" rx="5" fill="${c.body}"/>
        <rect x="56" y="149" width="18" height="20" rx="5" fill="${c.body}"/>
        <rect x="32" y="163" width="26" height="8" rx="4" fill="#222"/>
        <rect x="52" y="163" width="26" height="8" rx="4" fill="#222"/>
      `;
    }

    function resize() {
      W = stage.offsetWidth; H = stage.offsetHeight;
      canvas.width = W; canvas.height = H;
      stars = Array.from({ length: ARIA_CONFIG.starCount }, () => ({
        x: Math.random()*W, y: Math.random()*H, r: Math.random()*1.4+0.3, a: Math.random(),
      }));
    }

    function renderStars() {
      ctx.clearRect(0, 0, W, H);
      stars.forEach(s => {
        s.a += 0.005; if (s.a > 1) s.a = 0;
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI*2);
        ctx.fillStyle = `rgba(180,210,255,${(0.25+Math.sin(s.a*Math.PI)*0.4).toFixed(2)})`;
        ctx.fill();
      });
    }

    function spawnParticles(color) {
      const rect  = robotEl.getBoundingClientRect();
      const sRect = stage.getBoundingClientRect();
      const ox = rect.left - sRect.left + 55;
      const oy = rect.top  - sRect.top  + 85;
      for (let i = 0; i < 14; i++) {
        const p = document.createElement('div');
        p.className = 'aria-prt';
        const a = (i/14)*Math.PI*2, d = 30+Math.random()*45;
        p.style.cssText = `background:${color};left:${ox}px;top:${oy}px;--tx:${(Math.cos(a)*d).toFixed(0)}px;--ty:${(Math.sin(a)*d-18).toFixed(0)}px`;
        stage.appendChild(p);
        setTimeout(() => p.remove(), 750);
      }
    }

    function say(text) {
      bubbleEl.textContent = text; bubbleEl.style.opacity = '1';
      clearTimeout(bubbleTimer);
      bubbleTimer = setTimeout(() => bubbleEl.style.opacity = '0', 3500);
    }

    function addXP(n) {
      xp += n; if (xp >= 100) { xp -= 100; level++; }
      document.getElementById('aria-xp-fill').style.width = xp + '%';
      document.getElementById('aria-xp-txt').textContent = `Lv${level} · ${xp}xp`;
    }

    function playAnim(name, duration) {
      robotEl.style.animation = 'none';
      void robotEl.offsetWidth;
      robotEl.style.animation = `aria-${name} ${duration}ms ease`;
      setTimeout(() => { robotEl.style.animation = ''; }, duration);
    }

    function triggerMood(m) {
      mood = m;
      const msgs = ARIA_CONFIG.messages[m] || [];
      if (msgs.length) say(pick(msgs));
      if (m === 'correct') { addXP(10); streak++; spawnParticles('#1D9E75'); playAnim('bounce', 700); }
      if (m === 'wrong')   { streak = 0; spawnParticles('#E24B4A'); playAnim('shake', 500); }
      if (m === 'hint')    { spawnParticles('#7F77DD'); playAnim('think', 1000); }
      if (m === 'levelup') { addXP(50); spawnParticles('#EF9F27'); playAnim('dance', 1200); setTimeout(() => playAnim('spin', 600), 400); }
      if (m === 'idle')    { playAnim('think', 800); }
      document.getElementById('aria-streak').textContent = streak > 1 ? `${streak}x streak` : '';
      if (m !== 'idle') setTimeout(() => { mood = 'happy'; }, 3200);
    }

    robotEl.addEventListener('click', () => {
      say(pick(ARIA_CONFIG.messages.click));
      spawnParticles('#378ADD');
      playAnim('bounce', 500);
      addXP(2);
    });

    stage.addEventListener('mousemove', e => {
      const r = stage.getBoundingClientRect();
      mx = e.clientX - r.left;
      my = e.clientY - r.top;
    });

    function loop() {
      blinkT += 0.04; antennaT += 0.05; chestT += 0.04;
      renderStars();
      buildRobot(mood);
      requestAnimationFrame(loop);
    }

    resize();
    window.addEventListener('resize', resize);
    say(pick(ARIA_CONFIG.messages.welcome));
    requestAnimationFrame(loop);

    window.ARIA = {
      correct: () => triggerMood('correct'),
      wrong:   () => triggerMood('wrong'),
      hint:    () => triggerMood('hint'),
      levelUp: () => triggerMood('levelup'),
      idle:    () => triggerMood('idle'),
      say:     (text) => say(text),
      addXP:   (n) => addXP(n),
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
