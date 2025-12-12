document.addEventListener('DOMContentLoaded', () => {
  // === Persian Datepicker (DATE ONLY, POPUP) ===
  document.querySelectorAll('.jalali-date').forEach((el) => {
    const altField = el.getAttribute('data-alt-field'); // like "#start_from"

    $(el).persianDatepicker({
      format: 'YYYY/MM/DD',
      initialValue: false,
      autoClose: true,
      observer: true,
      timePicker: { enabled: false },

      // If you use hidden inputs (you do), wire them correctly:
      altField: altField || undefined,
      altFormat: 'YYYY/MM/DD',

      // safer for bootstrap cards/rtl layouts
      container: 'body'
    });

    // prevent manual typing but still allow click to open picker
    el.setAttribute('readonly', 'readonly');
  });

  // === Sidebar Collapse ===
  const sidebarToggle = document.getElementById('sidebarToggle');
  const body = document.body;

  if (localStorage.getItem('sidebar-collapsed') === 'true') {
    body.classList.add('sidebar-collapsed');
  }

  sidebarToggle?.addEventListener('click', () => {
    body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('sidebar-collapsed', body.classList.contains('sidebar-collapsed'));
  });
});
