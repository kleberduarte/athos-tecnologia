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

