// BingSpendSync — Main JavaScript

document.addEventListener('DOMContentLoaded', function () {

    // Auto-dismiss flash messages after 4 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 4000);
    });

    // Highlight active nav link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = '#6366f1';
            link.style.fontWeight = '700';
        }
    });

    // Confirm delete actions
    document.querySelectorAll('form[onsubmit]').forEach(function (form) {
        // Already handled inline
    });

});
