// Toggle password visibility
document.querySelectorAll('.toggle-password').forEach(function(toggle) {
    toggle.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const target = document.getElementById(targetId);
        
        if (target.type === 'password') {
            target.type = 'text';
            this.classList.remove('fa-eye');
            this.classList.add('fa-eye-slash');
        } else {
            target.type = 'password';
            this.classList.remove('fa-eye-slash');
            this.classList.add('fa-eye');
        }
    });
});

// Copy secret key to clipboard
function copySecretKey() {
    const secretKey = document.getElementById('secretKey').textContent;
    navigator.clipboard.writeText(secretKey).then(function() {
        const copyButton = document.querySelector('.copy-button');
        const originalText = copyButton.innerHTML;
        
        copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
        
        setTimeout(function() {
            copyButton.innerHTML = originalText;
        }, 2000);
    });
}

document.getElementById('copySecretKeyBtn').addEventListener('click', copySecretKey);
