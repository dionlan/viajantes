/* Balcão de Milhas — Interações e animações */
(function() {
  const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

  const state = {
    mode: 'sell',
    quotes: {
      updatedAt: Date.now(),
      latam: { buyPerThousand: 30.0, sellPerThousand: 24.0 },
      azul: { buyPerThousand: 26.0, sellPerThousand: 20.0 },
      smiles: { buyPerThousand: 28.0, sellPerThousand: 22.0 }
    }
  };

  const qs = (sel, ctx = document) => ctx.querySelector(sel);
  const qsa = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  function setYear() {
    const yearEl = qs('#year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
  }

  function initLucide() {
    if (window.lucide) {
      window.lucide.createIcons();
    } else {
      document.addEventListener('lucide:ready', () => window.lucide.createIcons());
    }
  }

  function initLenis() {
    if (!window.Lenis) return;
    const lenis = new window.Lenis({
      duration: 1.2,
      easing: (x) => 1 - Math.pow(1 - x, 3),
      smoothWheel: true,
      smoothTouch: false
    });
    function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
    requestAnimationFrame(raf);
    qsa('[data-scroll]').forEach((a) => {
      a.addEventListener('click', (e) => {
        const href = a.getAttribute('href');
        if (href && href.startsWith('#')) {
          e.preventDefault();
          const el = qs(href);
          if (el) lenis.scrollTo(el, { offset: -10 });
        }
      });
    });
  }

  function initGSAP() {
    if (!window.gsap) return;
    const gsap = window.gsap;
    if (window.ScrollTrigger) gsap.registerPlugin(window.ScrollTrigger);

    // Hero entrance
    gsap.from('.hero-content > *', {
      y: 20, opacity: 0, stagger: 0.08, duration: 0.8, ease: 'power3.out'
    });

    // Section headers
    qsa('.section-header').forEach((el) => {
      gsap.from(el, {
        scrollTrigger: { trigger: el, start: 'top 80%' },
        y: 18, opacity: 0, duration: 0.7, ease: 'power3.out'
      });
    });

    // Cards
    qsa('.flow-step, .quote-card, .sim-form, .insight-card').forEach((el) => {
      gsap.from(el, {
        scrollTrigger: { trigger: el, start: 'top 85%' },
        y: 18, opacity: 0, duration: 0.6, ease: 'power3.out'
      });
    });
  }

  // Animated background — particle network
  function initBackground() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = canvas.clientWidth;
    let height = canvas.clientHeight;
    let pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

    const palette = ['#a0d6b4', '#5f9ea0', '#317873'];

    function resize() {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * pixelRatio);
      canvas.height = Math.floor(height * pixelRatio);
      ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      spawnParticles();
    }

    const particles = [];
    const maxParticles = () => Math.floor((width * height) / 14000) + 30;

    function spawnParticles() {
      particles.length = 0;
      const count = maxParticles();
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.6,
          vy: (Math.random() - 0.5) * 0.6,
          r: Math.random() * 2 + 0.8,
          c: palette[Math.floor(Math.random() * palette.length)]
        });
      }
    }

    const mouse = { x: -9999, y: -9999 };
    canvas.addEventListener('pointermove', (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });
    canvas.addEventListener('pointerleave', () => {
      mouse.x = -9999; mouse.y = -9999;
    });

    function tick() {
      ctx.clearRect(0, 0, width, height);

      for (const p of particles) {
        // move
        p.x += p.vx; p.y += p.vy;
        // bounce
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;
        // mouse attraction
        const dx = p.x - mouse.x; const dy = p.y - mouse.y; const d2 = dx*dx + dy*dy;
        if (d2 < 12000) { p.vx += -dx * 0.00002; p.vy += -dy * 0.00002; }
      }

      // connections
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        ctx.fillStyle = p.c;
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x; const dy = p.y - q.y; const dist2 = dx*dx + dy*dy;
          if (dist2 < 20000) {
            const alpha = 1 - dist2 / 20000;
            ctx.globalAlpha = alpha * 0.35;
            ctx.strokeStyle = '#a3c1ad';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
      }
      ctx.globalAlpha = 1;

      requestAnimationFrame(tick);
    }

    resize();
    window.addEventListener('resize', resize);
    requestAnimationFrame(tick);
  }

  // Quotes
  async function loadQuotes() {
    try {
      const res = await fetch('assets/quotes.json', { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        if (data && data.latam && data.azul && data.smiles) {
          state.quotes = data;
        }
      }
    } catch (_) { /* use defaults */ }
    renderQuotes();
    updateSimulator();
  }

  function renderQuotes() {
    const mode = state.mode; // 'sell' or 'buy'
    const container = qs('.quote-grid');
    if (!container) return;
    qsa('.quote-card', container).forEach((card) => {
      const program = card.getAttribute('data-program');
      const meta = state.quotes[program];
      if (!meta) return;
      const value = mode === 'sell' ? meta.sellPerThousand : meta.buyPerThousand;
      const quoteEl = qs('[data-quote]', card);
      const updEl = qs('[data-updated]', card);
      if (quoteEl) quoteEl.textContent = currency.format(value);
      if (updEl) {
        const date = new Date(state.quotes.updatedAt || Date.now());
        const time = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        updEl.textContent = `Atualizado às ${time}`;
      }
    });
  }

  function setupQuoteModeToggle() {
    const toggles = qsa('.toggle');
    toggles.forEach((btn) => btn.addEventListener('click', () => {
      toggles.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.mode = btn.getAttribute('data-mode');
      renderQuotes();
      updateSimulator();
    }));
  }

  // Simulator
  function valueFor(program, op, miles) {
    const meta = state.quotes[program];
    if (!meta) return 0;
    const perThousand = op === 'sell' ? meta.sellPerThousand : meta.buyPerThousand;
    return (miles / 1000) * perThousand;
  }

  function updateSimulator() {
    const opBtn = qs('.segmented-item.active');
    const op = opBtn ? opBtn.getAttribute('data-op') : 'sell';
    const program = qs('#programa')?.value || 'latam';
    const miles = parseInt(qs('#quantidade')?.value || '0', 10) || 0;

    const perThousand = op === 'sell' ? state.quotes[program].sellPerThousand : state.quotes[program].buyPerThousand;
    const total = valueFor(program, op, miles);

    const cot = qs('#cotacao');
    const val = qs('#valor');
    if (cot) cot.textContent = currency.format(perThousand);
    if (val) val.textContent = currency.format(total);
  }

  function setupSimulator() {
    qsa('.segmented-item').forEach((b) => b.addEventListener('click', () => {
      qsa('.segmented-item').forEach((x) => x.classList.remove('active'));
      b.classList.add('active');
      state.mode = b.getAttribute('data-op');
      renderQuotes();
      updateSimulator();
    }));

    ['#programa', '#quantidade'].forEach((sel) => {
      const el = qs(sel);
      if (!el) return;
      el.addEventListener('input', updateSimulator);
      el.addEventListener('change', updateSimulator);
    });

    const conectar = qs('#cta-conectar');
    conectar?.addEventListener('click', openTraderModal);
  }

  // Trader modal
  const traders = [
    { id: 't1', name: 'Marina Costa', rating: 4.9, deals: 1280, response: '2min', badge: 'Top 1% verificado', contact: 'https://wa.me/?text=Quero%20negociar%20minhas%20milhas%20via%20Balc%C3%A3o%20de%20Milhas' },
    { id: 't2', name: 'Lucas Ribeiro', rating: 4.8, deals: 980, response: '3min', badge: 'KYC atualizado', contact: 'https://wa.me/?text=Quero%20comprar%20milhas%20via%20Balc%C3%A3o%20de%20Milhas' },
    { id: 't3', name: 'Ana Clara', rating: 5.0, deals: 1560, response: '1min', badge: 'Super host', contact: 'https://wa.me/?text=Tenho%20interesse%20em%20negociar%20milhas' }
  ];

  function openTraderModal() {
    const modal = qs('#trader-modal');
    const body = qs('#trader-details');
    const action = qs('#modal-action');
    if (!modal || !body || !action) return;

    const pick = traders[Math.floor(Math.random() * traders.length)];
    body.innerHTML = `
      <div class="trader-row">
        <div class="avatar" aria-hidden="true">${pick.name.split(' ').map(p=>p[0]).slice(0,2).join('')}</div>
        <div class="data">
          <div class="name">${pick.name} <span class="badge-mini">${pick.badge}</span></div>
          <div class="meta">
            <span>⭐ ${pick.rating.toFixed(1)}</span>
            <span>Negócios: ${pick.deals.toLocaleString('pt-BR')}</span>
            <span>Resposta: ${pick.response}</span>
          </div>
        </div>
      </div>
    `;
    action.href = pick.contact;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    // close handlers
    qsa('[data-close]', modal).forEach((el) => el.addEventListener('click', closeTraderModal));
    document.addEventListener('keydown', escToClose);
  }

  function closeTraderModal() {
    const modal = qs('#trader-modal');
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.removeEventListener('keydown', escToClose);
  }
  function escToClose(e) { if (e.key === 'Escape') closeTraderModal(); }

  function enhanceSimulatorUI() {
    // Improve number stepper UX: clamp and step 100
    const qty = qs('#quantidade');
    if (!qty) return;
    function normalize() {
      let val = parseInt(qty.value || '0', 10) || 0;
      val = Math.max(100, Math.round(val / 100) * 100);
      qty.value = String(val);
      updateSimulator();
    }
    qty.addEventListener('blur', normalize);
  }

  // Mobile menu (basic)
  function initMenu() {
    const btn = qs('.nav-menu');
    const nav = qs('.primary-nav');
    const cta = qs('.nav-cta');
    if (!btn || !nav || !cta) return;
    btn.addEventListener('click', () => {
      const open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open));
      nav.style.display = open ? 'none' : 'inline-flex';
      cta.style.display = open ? 'none' : 'inline-flex';
    });
  }

  // Init all
  function init() {
    setYear();
    initLucide();
    initLenis();
    initGSAP();
    initBackground();
    setupQuoteModeToggle();
    setupSimulator();
    enhanceSimulatorUI();
    loadQuotes();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
