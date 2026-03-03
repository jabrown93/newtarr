const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const errorMessage = document.getElementById('errorMessage');
const togglePassword = document.getElementById('togglePassword');
const twoFactorContainer = document.getElementById('twoFactorContainer');
let otpInput = null;
let twoFactorMode = false;

// Toggle password visibility
togglePassword.addEventListener('click', function() {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.classList.toggle('fa-eye');
    this.classList.toggle('fa-eye-slash');
});

loginForm.addEventListener('submit', function(e) {
    e.preventDefault();

    // Clear previous errors
    errorMessage.style.display = 'none';
    errorMessage.textContent = '';

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        showError('Please enter both username and password.');
        return;
    }

    // Check if we're in 2FA mode and validate the 2FA code
    if (twoFactorMode && otpInput) {
        const otpCode = otpInput.value.trim();
        if (!otpCode) {
            showError('Please enter your two-factor authentication code.');
            return;
        }

        if (otpCode.length !== 6 || !/^\d+$/.test(otpCode)) {
            showError('Two-factor code must be 6 digits.');
            return;
        }
    }

    // Show loading state on button
    const loginButton = document.getElementById('loginButton');
    const originalText = loginButton.innerHTML;
    loginButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    loginButton.disabled = true;

    // Prepare login data
    const loginData = {
        username: username,
        password: password,
        rememberMe: document.getElementById('rememberMe').checked
    };

    // Add 2FA code if we're in 2FA mode
    if (twoFactorMode && otpInput) {
        loginData.twoFactorCode = otpInput.value.trim();
    }

    // Submit the form data
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData)
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(({ status, body }) => {
        console.log('Login response:', status, body);

        // Check for 2FA requirement
        const requires2FA = body.requires_2fa || body.requiresTwoFactor || body.requires2fa || body.requireTwoFactor || false;

        if (status === 200 && body.success) {
            // Login successful
            window.location.href = body.redirect || '/';
        } else if (status === 401 && requires2FA) {
            // 2FA is required
            console.log('2FA required, showing 2FA input field');
            twoFactorMode = true;

            // Add 2FA field
            twoFactorContainer.innerHTML = `
            <div class="form-group" id="twoFactorGroup">
                <label for="twoFactorCode">
                    <i class="fas fa-shield-alt"></i>
                    <span>Two-Factor Code</span>
                </label>
                <input type="text" id="twoFactorCode" name="twoFactorCode"
                       placeholder="Enter your 6-digit code" maxlength="6"
                       class="two-factor-input">
            </div>`;

            // Update reference to the new input
            otpInput = document.getElementById('twoFactorCode');
            if (otpInput) {
                otpInput.focus();

                // Add input validation
                otpInput.addEventListener('input', function() {
                    // Only allow digits
                    this.value = this.value.replace(/[^0-9]/g, '');
                });
            }

            // Reset button
            loginButton.innerHTML = originalText;
            loginButton.disabled = false;

            // Show message
            showError('Please enter your two-factor authentication code.');
        } else {
            // Show error message
            showError(body.error || 'Invalid username or password.');

            // Reset button
            loginButton.innerHTML = originalText;
            loginButton.disabled = false;
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        showError('An error occurred during login. Please try again.');

        // Reset button
        loginButton.innerHTML = originalText;
        loginButton.disabled = false;
    });
});

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}
