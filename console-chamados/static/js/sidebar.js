(function () {
  var toggle  = document.getElementById('sidebar-toggle');
  var closeBtn= document.getElementById('sidebar-close');
  var overlay = document.getElementById('sidebar-overlay');
  var sidebar = document.getElementById('sidebar');
  if (!toggle || !sidebar) return;

  function openSidebar()  { sidebar.classList.add('open');    overlay.classList.add('active'); }
  function closeSidebar() { sidebar.classList.remove('open'); overlay.classList.remove('active'); }

  toggle.addEventListener('click', openSidebar);
  closeBtn.addEventListener('click', closeSidebar);
  overlay.addEventListener('click', closeSidebar);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeSidebar(); });

  // Marcar item ativo
  var current = window.location.pathname;
  document.querySelectorAll('.sidebar-item').forEach(function(a) {
    var href = a.getAttribute('href');
    if (!href) return;
    if (href === current || (href !== '/' && current.startsWith(href))) {
      a.classList.add('active');
    }
  });
})();
