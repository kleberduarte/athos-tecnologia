// ——— Header scroll ———
const header = document.getElementById('siteHeader');
window.addEventListener('scroll', () => {
  header.classList.toggle('is-scrolled', window.scrollY > 30);
}, { passive: true });

// ——— Nav mobile ———
const toggle = document.getElementById('navToggle');
const nav    = document.getElementById('mainNav');
toggle.addEventListener('click', () => {
  const open = nav.classList.toggle('is-open');
  toggle.setAttribute('aria-expanded', open);
});
nav.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  });
});

// ——— Reveal ———
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('is-visible');
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// ——— Ano footer ———
const y = document.getElementById('y');
if (y) y.textContent = new Date().getFullYear();

// ——— Grade animada no Hero ———
(function () {
  const canvas = document.getElementById('heroGrid');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let raf, t = 0;

  function resize() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const spacing = 40;
    const offset  = (t * 0.3) % spacing;
    ctx.strokeStyle = 'rgba(0,255,136,0.055)';
    ctx.lineWidth   = 0.5;

    for (let x = -spacing + offset; x < canvas.width + spacing; x += spacing) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let yy = -spacing + offset; yy < canvas.height + spacing; yy += spacing) {
      ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(canvas.width, yy); ctx.stroke();
    }

    // Neon radial glow sweeping slowly
    const gx = canvas.width * 0.5 + Math.sin(t * 0.008) * canvas.width * 0.15;
    const gy = canvas.height * 0.5;
    const grad = ctx.createRadialGradient(gx, gy, 0, gx, gy, canvas.width * 0.55);
    grad.addColorStop(0,   'rgba(0,255,136,0.045)');
    grad.addColorStop(1,   'rgba(0,255,136,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    t++;
    raf = requestAnimationFrame(draw);
  }

  resize();
  draw();

  const ro = new ResizeObserver(resize);
  ro.observe(canvas);

  // Pausa quando fora da tela para economizar CPU
  const pauseObserver = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { if (!raf) draw(); }
      else { cancelAnimationFrame(raf); raf = null; }
    });
  });
  pauseObserver.observe(canvas);
})();

// ——— Contadores animados ———
(function () {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;

  function easeOutQuart(t) {
    return 1 - Math.pow(1 - t, 4);
  }

  function animateCounter(el) {
    const target   = parseInt(el.dataset.count, 10);
    const prefix   = el.dataset.prefix || '';
    const suffix   = el.dataset.suffix || '';
    const duration = 1600;
    const start    = performance.now();

    function step(now) {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const value    = Math.round(easeOutQuart(progress) * target);
      el.textContent = prefix + value + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const counterObserver = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCounter(e.target);
        counterObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => counterObserver.observe(el));
})();

// ——— Botão flutuante de CTA ———
(function () {
  const floatBar  = document.getElementById('floatBar');
  if (!floatBar) return;

  let visible = false;

  function updateFloat() {
    const shouldShow = window.scrollY > 400;
    if (shouldShow !== visible) {
      visible = shouldShow;
      floatBar.classList.toggle('is-visible', visible);
      floatBar.setAttribute('aria-hidden', String(!visible));
    }
  }

  window.addEventListener('scroll', updateFloat, { passive: true });
  updateFloat();
})();
