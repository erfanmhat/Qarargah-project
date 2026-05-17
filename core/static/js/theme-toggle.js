// theme-toggle.js
(function() {
    'use strict';

    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    const themeIcon = themeToggle.querySelector('i');

    // بارگذاری تم ذخیره شده از localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    // رویداد کلیک روی دکمه تغییر تم
    themeToggle.addEventListener('click', function() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);

        // تغییر آیکون
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-moon';
            themeToggle.setAttribute('aria-label', 'تغییر به تم روشن');
        } else {
            themeIcon.className = 'fas fa-sun';
            themeToggle.setAttribute('aria-label', 'تغییر به تم تاریک');
        }
    }
})();
