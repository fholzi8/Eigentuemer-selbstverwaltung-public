document.addEventListener('DOMContentLoaded', function() {
    // Für alle Select-Elemente mit dem Attribut data-autosubmit
    const autoSubmitSelects = document.querySelectorAll('select[data-autosubmit]');
    autoSubmitSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });
});