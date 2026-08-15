/**
 * StratLearn UI Client-Side Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // Mobile Sidebar Toggle
    const toggleBtn = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('app-sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
            if (overlay) overlay.classList.toggle('hidden');
        });
    }

    if (overlay && sidebar) {
        overlay.addEventListener('click', () => {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        });
    }

    // Auto-dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

/**
 * Quick-fill login credentials for demo test accounts
 */
function fillCredentials(username, password) {
    const userInput = document.getElementById('username');
    const passInput = document.getElementById('password');
    if (userInput && passInput) {
        userInput.value = username;
        passInput.value = password;
        
        // Add subtle flash animation on inputs
        userInput.classList.add('ring-2', 'ring-brand-500');
        passInput.classList.add('ring-2', 'ring-brand-500');
        setTimeout(() => {
            userInput.classList.remove('ring-2', 'ring-brand-500');
            passInput.classList.remove('ring-2', 'ring-brand-500');
        }, 600);
    }
}
