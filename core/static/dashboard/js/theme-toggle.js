(function() {
    'use strict';
    
    // Check for saved theme preference or default to dark
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply theme on load
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    // Wait for DOM to be ready
    function initThemeToggle() {
        const themeToggle = document.getElementById('themeToggle') || document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', function(e) {
                e.preventDefault();
                const current = document.documentElement.getAttribute('data-theme') || 'dark';
                const newTheme = current === 'dark' ? 'light' : 'dark';
                
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateThemeIcon(newTheme);
            });
        }
    }
    
    function updateThemeIcon(theme) {
        const themeToggle = document.getElementById('themeToggle') || document.querySelector('.theme-toggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.className = 'fas fa-moon';
                    icon.setAttribute('title', 'تغییر به تم روشن');
                    themeToggle.setAttribute('title', 'تغییر به تم روشن');
                } else {
                    icon.className = 'fas fa-sun';
                    icon.setAttribute('title', 'تغییر به تم تیره');
                    themeToggle.setAttribute('title', 'تغییر به تم تیره');
                }
            }
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeToggle);
    } else {
        initThemeToggle();
    }
})();

