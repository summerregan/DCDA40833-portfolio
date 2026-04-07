function setupMobileNav(nav) {
  const toggleButton = nav.querySelector('.nav-toggle');
  const navMenu = nav.querySelector('.nav-menu');

  if (!toggleButton || !navMenu) {
    return;
  }

  toggleButton.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('is-open');
    toggleButton.setAttribute('aria-expanded', String(isOpen));
  });

  navMenu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      nav.classList.remove('is-open');
      toggleButton.setAttribute('aria-expanded', 'false');
    });
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      nav.classList.remove('is-open');
      toggleButton.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('click', (event) => {
    const isClickInsideNav = nav.contains(event.target);
    if (!isClickInsideNav && nav.classList.contains('is-open')) {
      nav.classList.remove('is-open');
      toggleButton.setAttribute('aria-expanded', 'false');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.site-nav').forEach(setupMobileNav);
});
