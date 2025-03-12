// Mobile-Optimierungen für JavaScript

// Bessere Tooltip-Konfiguration für mobile Geräte
document.addEventListener('DOMContentLoaded', function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        // Mobile-freundliche Tooltip-Einstellungen
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            container: 'body',
            boundary: 'window',
            trigger: window.innerWidth < 768 ? 'click' : 'hover focus', // Auf mobilen Geräten nur bei Klick zeigen
            delay: { show: 50, hide: 100 }
        });
    });
    
    // Passe DataTables für Mobile an
    if ($('#transaktion-tabelle').length > 0) {
        const isMobile = window.innerWidth < 768;
        
        $('#transaktion-tabelle').DataTable({
            "paging": false,
            "searching": false,
            "info": false,
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.4/i18n/de-DE.json"
            },
            "order": [[0, "desc"]],
            "columnDefs": [
                { "orderable": false, "targets": [6] },
                // Auf Mobilgeräten weniger Spalten standardmäßig anzeigen/sortieren
                { "responsivePriority": 1, "targets": [0, 1, 5] }, // Datum, Beschreibung, Betrag als wichtigste Spalten
                { "responsivePriority": 2, "targets": 6 }, // Aktionen-Spalte
                { "responsivePriority": 3, "targets": [2, 3, 4] } // Weniger wichtige Spalten
            ],
            // Responsive-Option für DataTables (falls du die DataTables Responsive-Erweiterung nutzt)
            // "responsive": true
        });
    }
    
    // Automatisches Schließen des Navbar-Menüs nach Klick auf Mobilgeräten
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                // Bootstrap 5 Methode zum Schließen der Navbar
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        });
    });
});

// Optimierungen für Formulare auf Mobilgeräten
if (window.innerWidth < 768) {
    // Fokus auf Input-Felder automatisch verschieben
    document.querySelectorAll('input, select, textarea').forEach(function(el) {
        el.addEventListener('blur', function() {
            // Kurze Verzögerung vor dem Scrollen
            setTimeout(function() {
                window.scrollBy(0, 1);
                window.scrollBy(0, -1);
            }, 100);
        });
    });
    
    // Bei Klick auf Label zu Input-Feld scrollen
    document.querySelectorAll('label[for]').forEach(function(label) {
        label.addEventListener('click', function() {
            const input = document.getElementById(this.getAttribute('for'));
            if (input) {
                // Zum Input-Element scrollen
                setTimeout(function() {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 100);
            }
        });
    });
}