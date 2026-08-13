// ——— Header scroll ———
const header = document.getElementById('siteHeader');
window.addEventListener('scroll', () => {
  header.classList.toggle('is-scrolled', window.scrollY > 30);
}, { passive: true });

// ——— Nav mobile ———
const toggle  = document.getElementById('navToggle');
const nav     = document.getElementById('mainNav');
const overlay = document.getElementById('navOverlay');

function closeNav() {
  nav.classList.remove('is-open');
  overlay.classList.remove('is-open');
  toggle.setAttribute('aria-expanded', 'false');
}

toggle.addEventListener('click', () => {
  const open = nav.classList.toggle('is-open');
  overlay.classList.toggle('is-open', open);
  toggle.setAttribute('aria-expanded', open);
});

overlay.addEventListener('click', closeNav);

nav.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', (e) => {
    const href = a.getAttribute('href');
    if (!href || !href.startsWith('#')) { closeNav(); return; }
    e.preventDefault();
    closeNav();
    setTimeout(() => {
      const target = document.getElementById(href.slice(1));
      if (!target) return;
      target.classList.add('is-visible');
      let top = 0;
      let node = target;
      while (node && node !== document.body) {
        top += node.offsetTop || 0;
        node = node.offsetParent;
      }
      window.scrollTo(0, Math.max(0, top - 84));
    }, 100);
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
}, { threshold: 0.05 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// ——— Ano footer ———
const y = document.getElementById('y');
if (y) y.textContent = new Date().getFullYear();

// ——— Grade animada no Hero ———
(function () {
  const canvas = document.getElementById('heroGrid');
  if (!canvas) return;

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    canvas.style.display = 'none';
    return;
  }

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

// ——— WhatsApp modal ———
(function () {
  const btn      = document.getElementById('whatsappBtn');
  const modal    = document.getElementById('whatsappModal');
  const backdrop = document.getElementById('whatsappBackdrop');
  const closeBtn = document.getElementById('whatsappModalClose');
  if (!btn || !modal) return;

  function openModal() {
    modal.hidden    = false;
    backdrop.hidden = false;
    closeBtn.focus();
  }
  function closeModal() {
    modal.hidden    = true;
    backdrop.hidden = true;
    btn.focus();
  }

  btn.addEventListener('click', openModal);
  closeBtn.addEventListener('click', closeModal);
  backdrop.addEventListener('click', closeModal);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !modal.hidden) closeModal(); });

  const cta = modal.querySelector('.wa-modal__cta');
  if (cta) cta.addEventListener('click', closeModal);
})();

// ——— Formulário de contato (Formspree AJAX) ———
(function () {
  const form    = document.getElementById('contactForm');
  if (!form) return;

  const btn     = document.getElementById('cfSubmit');
  const success = document.getElementById('cfSuccess');
  const errBox  = document.getElementById('cfError');

  const MSGS = {
    required:  'Campo obrigatório.',
    email:     'Informe um e-mail válido.',
    minlength: n => `Mínimo de ${n} caracteres.`,
  };

  function validateField(input) {
    const group = input.closest('.athos-form-group');
    const errEl = group && group.querySelector('.athos-form-error-msg');
    let msg = '';

    if (input.validity.valueMissing)     msg = MSGS.required;
    else if (input.validity.typeMismatch) msg = MSGS.email;
    else if (input.validity.tooShort)    msg = MSGS.minlength(input.minLength);

    group && group.classList.toggle('is-invalid', !!msg);
    if (errEl) errEl.textContent = msg;
    return !msg;
  }

  form.querySelectorAll('input, select, textarea').forEach(el => {
    el.addEventListener('blur',   () => validateField(el));
    el.addEventListener('change', () => validateField(el));
    el.addEventListener('input',  () => {
      if (el.closest('.athos-form-group')?.classList.contains('is-invalid')) validateField(el);
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errBox.hidden = true;

    const fields = [...form.querySelectorAll('input:not([name="_honey"]), select, textarea')];
    const allValid = fields.map(validateField).every(Boolean);
    if (!allValid) {
      const firstErr = form.querySelector('.is-invalid input, .is-invalid select, .is-invalid textarea');
      firstErr && firstErr.focus();
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Enviando...';

    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
      });

      if (res.ok) {
        form.hidden = true;
        success.hidden = false;
        success.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        throw new Error('server_error');
      }
    } catch {
      errBox.hidden = false;
      btn.disabled = false;
      btn.textContent = 'Enviar mensagem';
    }
  });
})();
