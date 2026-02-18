document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('themeToggle');

  const applyTheme = (theme) => {
    const isDark = theme === 'dark';
    document.body.classList.toggle('dark', isDark);

    if (themeToggle) {
      themeToggle.setAttribute('aria-pressed', String(isDark));
      themeToggle.textContent = isDark ? 'Dark Mode: On' : 'Dark Mode';
    }
  };

  const savedTheme = localStorage.getItem('site-theme');
  applyTheme(savedTheme === 'dark' ? 'dark' : 'light');

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const nextTheme = document.body.classList.contains('dark') ? 'light' : 'dark';
      applyTheme(nextTheme);
      localStorage.setItem('site-theme', nextTheme);
    });
  }
});
