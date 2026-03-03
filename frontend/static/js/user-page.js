// Initialize dark mode
document.addEventListener('DOMContentLoaded', function() {
    // Apply dark theme
    document.body.classList.add('dark-theme');
    localStorage.setItem('newtarr-dark-mode', 'true');

    // Update server setting to dark mode
    fetch('/api/settings/theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ dark_mode: true })
    }).catch(error => console.error('Error saving theme:', error));
});

// Password validation function
function validatePassword(password) {
    // Only check for minimum length of 8 characters
    if (password.length < 8) {
        return 'Password must be at least 8 characters long.';
    }
    return null; // Password is valid
}
