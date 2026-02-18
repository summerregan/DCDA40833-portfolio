// Load saved theme preference on page load
window.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('site-theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark');
  }
});

// Toggle theme when button is clicked
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark');
    localStorage.setItem('site-theme', isDark ? 'dark' : 'light');
  });
}
