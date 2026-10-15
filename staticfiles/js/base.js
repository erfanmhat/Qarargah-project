// dashboard/js/base.js
document.addEventListener('DOMContentLoaded', function () {
    // === Persian Datepicker (DATE ONLY, SAFE) ===
    if (window.jQuery && $.fn && $.fn.persianDatepicker) {
        document.querySelectorAll('.jalali-date').forEach(function (input) {
            var altField = input.dataset.altField;

            $(input).persianDatepicker({
                observer: true,
                format: 'YYYY/MM/DD',
                altField: altField || undefined,
                altFormat: 'YYYY-MM-DD',  // for hidden miladi field
                timePicker: { enabled: false },
                calendarType: 'persian',
                initialValue: !!input.value
            });

            // Prevent manual typing
            input.setAttribute('readonly', 'readonly');
        });
    }

    // === Sidebar Collapse ===
    var sidebarToggle = document.getElementById('sidebarToggle');
    var body = document.body;

    // Apply saved state
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        body.classList.add('sidebar-collapsed');
    }

    // Click handler
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            body.classList.toggle('sidebar-collapsed');
            localStorage.setItem(
                'sidebar-collapsed',
                body.classList.contains('sidebar-collapsed')
            );
        });
    }
});
