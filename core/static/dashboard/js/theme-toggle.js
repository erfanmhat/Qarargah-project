(function() {
    'use strict';
    
    // Check for saved theme preference or default to dark
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply theme on load
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    // Theme toggle button
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        const icon = document.querySelector('.theme-toggle i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'fas fa-moon';
                icon.title = 'تغییر به تم روشن';
            } else {
                icon.className = 'fas fa-sun';
                icon.title = 'تغییر به تم تیره';
            }
        }
    }
})();

