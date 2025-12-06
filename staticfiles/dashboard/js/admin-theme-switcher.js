function toggleTheme() {
    const lightCss = document.getElementById('theme-css');
    const icon = document.getElementById('theme-icon');
    if (lightCss.disabled) {
        lightCss.disabled = false;
        document.body.classList.add('theme-light');
        localStorage.setItem('admin-theme', 'light');
        icon.innerHTML = 'sun';
    } else {
        lightCss.disabled = true;
        document.body.classList.remove('theme-light');
        localStorage.setItem('admin-theme', 'dark');
        icon.innerHTML = 'moon';
    }
}