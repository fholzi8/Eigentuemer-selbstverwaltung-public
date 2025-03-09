// Datei: static/js/password-strength.js

document.addEventListener('DOMContentLoaded', function() {
    var passwordInput = document.getElementById('password');
    if (!passwordInput) return;

    var strengthMeter = document.createElement('div');
    strengthMeter.className = 'password-strength-meter mt-2';
    strengthMeter.innerHTML = '<div class="progress" style="height: 5px;"><div class="progress-bar" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div></div><small class="text-muted password-strength-text mt-1"></small>';
    
    passwordInput.parentNode.insertBefore(strengthMeter, passwordInput.nextSibling);
    
    var progressBar = strengthMeter.querySelector('.progress-bar');
    var strengthText = strengthMeter.querySelector('.password-strength-text');
    
    passwordInput.addEventListener('input', function() {
        var password = this.value;
        var strength = calculatePasswordStrength(password);
        
        updateStrengthMeter(strength, progressBar, strengthText);
    });
    
    function calculatePasswordStrength(password) {
        if (!password) return 0;
        
        var score = 0;
        
        // Länge
        if (password.length >= 8) score += 20;
        if (password.length >= 12) score += 10;
        
        // Komplexität
        if (/[A-Z]/.test(password)) score += 20; // Großbuchstaben
        if (/[a-z]/.test(password)) score += 20; // Kleinbuchstaben
        if (/[0-9]/.test(password)) score += 20; // Ziffern
        if (/[^a-zA-Z0-9]/.test(password)) score += 20; // Sonderzeichen
        
        return score;
    }
    
    function updateStrengthMeter(strength, progressBar, strengthText) {
        progressBar.style.width = strength + '%';
        
        if (strength < 40) {
            progressBar.className = 'progress-bar bg-danger';
            strengthText.textContent = 'Schwach';
        } else if (strength < 80) {
            progressBar.className = 'progress-bar bg-warning';
            strengthText.textContent = 'Mittel';
        } else {
            progressBar.className = 'progress-bar bg-success';
            strengthText.textContent = 'Stark';
        }
        
        // Zeige spezifische Anforderungen an
        var requirements = [];
        var password = document.getElementById('password').value;
        
        if (password.length < 8) requirements.push('Mindestens 8 Zeichen');
        if (!/[A-Z]/.test(password)) requirements.push('Großbuchstaben');
        if (!/[a-z]/.test(password)) requirements.push('Kleinbuchstaben');
        if (!/[0-9]/.test(password)) requirements.push('Ziffern');
        if (!/[^a-zA-Z0-9]/.test(password)) requirements.push('Sonderzeichen');
        
        if (requirements.length > 0) {
            strengthText.innerHTML = strengthText.textContent + ' - Es fehlt: ' + requirements.join(', ');
        }
    }
});