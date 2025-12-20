document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const togglePassword = document.getElementById('togglePassword');
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            const passwordInput = document.getElementById('id_password');
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    }

    // Form validation
    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            const loginBtn = document.getElementById('loginBtn');
            const btnText = document.getElementById('btnText');
            const btnLoading = document.getElementById('btnLoading');

            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            } else {
                // Show loading state
                if(btnText && btnLoading && loginBtn) {
                    btnText.classList.add('d-none');
                    btnLoading.classList.remove('d-none');
                    loginBtn.disabled = true;
                }
            }
            
            form.classList.add('was-validated');
        });
    }

    // Display current time
    const currentTimeEl = document.getElementById('currentTime');
    if (currentTimeEl) {
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('fr-FR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            currentTimeEl.textContent = timeString;
        }
        
        updateTime();
        setInterval(updateTime, 60000);
    }

    // Auto-focus on username field
    const usernameField = document.getElementById('id_username');
    if (usernameField) {
        usernameField.focus();
    }

    // Enter key to submit form
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.target.matches('textarea, [contenteditable]')) {
            const activeElement = document.activeElement;
            if (activeElement.tagName === 'INPUT' && activeElement.type !== 'submit') {
                e.preventDefault();
                const loginBtn = document.getElementById('loginBtn');
                if(loginBtn) {
                    loginBtn.click();
                }
            }
        }
    });
});
