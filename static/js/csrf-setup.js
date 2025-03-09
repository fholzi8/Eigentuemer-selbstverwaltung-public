// CSRF-Token für AJAX-Anfragen
document.addEventListener('DOMContentLoaded', function() {
    // CSRF-Token aus Meta-Tag extrahieren
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (!metaTag) return; // Keine CSRF-Metadaten gefunden
    
    const csrfToken = metaTag.getAttribute('content');
    
    // Vor jedem AJAX-Request das CSRF-Token setzen (Vanilla JS)
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function() {
        originalOpen.apply(this, arguments);
        this.setRequestHeader('X-CSRFToken', csrfToken);
    };
    
    // Für Fetch API
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Standardwerte setzen, wenn nicht vorhanden
        options = options || {};
        options.headers = options.headers || {};
        
        // CSRF-Token nur bei bestimmten Methoden hinzufügen
        const method = options.method || 'GET';
        if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method.toUpperCase())) {
            options.headers['X-CSRFToken'] = csrfToken;
        }
        
        return originalFetch.call(this, url, options);
    };
    
    // Für jQuery, falls es noch verwendet wird
    if (typeof $ !== 'undefined' && $.ajaxSetup) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });
    }
});