document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const steps = document.querySelectorAll('.step');
    const screens = document.querySelectorAll('.setup-section');
    const errorMessage = document.getElementById('errorMessage');

    // Account setup elements
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const accountNextButton = document.getElementById('accountNextButton');

    // 2FA setup elements
    const qrCodeElement = document.getElementById('qrCode');
    const secretKeyElement = document.getElementById('secretKey');
    const verificationCodeInput = document.getElementById('verificationCode');
    const skip2FALink = document.getElementById('skip2FALink');
    const twoFactorNextButton = document.getElementById('twoFactorNextButton');

    // Auth Mode setup elements
    const authModeSelect = document.getElementById('auth_mode');
    const authModeNextButton = document.getElementById('authModeNextButton');
    const authModeErrorMessage = document.getElementById('authModeErrorMessage');

    // Complete setup elements
    const finishSetupButton = document.getElementById('finishSetupButton');

    // Current step tracking
    let currentStep = 1;
    let accountCreated = false;
    let twoFactorEnabled = false;

    // Store user data
    let userData = {
        username: '',
        password: ''
    };

    // Show a specific step
    function showStep(step) {
        steps.forEach((s, index) => {
            if (index + 1 < step) {
                s.classList.remove('active');
                s.classList.add('completed');
            } else if (index + 1 === step) {
                s.classList.add('active');
                s.classList.remove('completed');
            } else {
                s.classList.remove('active');
                s.classList.remove('completed');
            }
        });

        // For the four sections: Account, 2FA, Auth Mode, Complete
        if (step === 1) {
            document.getElementById('accountSetup').classList.add('active');
            document.getElementById('twoFactorSetup').classList.remove('active');
            document.getElementById('authModeSetup').classList.remove('active');
            document.getElementById('setupComplete').classList.remove('active');
        } else if (step === 2) {
            document.getElementById('accountSetup').classList.remove('active');
            document.getElementById('twoFactorSetup').classList.add('active');
            document.getElementById('authModeSetup').classList.remove('active');
            document.getElementById('setupComplete').classList.remove('active');
        } else if (step === 3) {
            document.getElementById('accountSetup').classList.remove('active');
            document.getElementById('twoFactorSetup').classList.remove('active');
            document.getElementById('authModeSetup').classList.add('active');
            document.getElementById('setupComplete').classList.remove('active');
        } else if (step === 4) {
            document.getElementById('accountSetup').classList.remove('active');
            document.getElementById('twoFactorSetup').classList.remove('active');
            document.getElementById('authModeSetup').classList.remove('active');
            document.getElementById('setupComplete').classList.add('active');
        }

        currentStep = step;
    }

    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';

        // Hide after 5 seconds
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }

    // Password validation function
    function validatePassword(password) {
        // Only check for minimum length of 8 characters
        if (password.length < 8) {
            return 'Password must be at least 8 characters long.';
        }
        return null; // Password is valid
    }

    // Account creation
    accountNextButton.addEventListener('click', function() {
        const username = usernameInput.value.trim(); // Trim whitespace
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        // No longer needed here - will be captured in step 3

        if (!username || !password || !confirmPassword) {
            showError('All fields are required');
            return;
        }

        // Add username length validation
        if (username.length < 3) {
            showError('Username must be at least 3 characters long');
            return;
        }

        if (password !== confirmPassword) {
            showError('Passwords do not match');
            return;
        }

        // Validate password complexity
        const passwordError = validatePassword(password);
        if (passwordError) {
            showError(passwordError);
            return;
        }

        // Store user data
        userData.username = username;
        userData.password = password;

        if (accountCreated) {
            // If account already created, just move to next step
            showStep(2);
            return;
        }

        // Create user account with improved error handling
        fetch('/setup', { // Corrected endpoint from /api/setup to /setup
            method: 'POST',
            redirect: 'error', // Add this line to prevent following redirects
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                confirm_password: confirmPassword // Keep confirm_password if backend expects it, otherwise remove
            })
        })
        .then(response => {
            // Check if response is ok before parsing JSON
            if (!response.ok) {
                // Check content type to see if it's likely JSON
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    // If it seems like JSON, try to parse it for an error message
                    return response.json().then(data => {
                        // Use data.error first, then data.message as fallback
                        throw new Error(data.error || data.message || `Server error: ${response.status}`);
                    });
                } else {
                    // If not JSON (e.g., HTML error page), throw a generic HTTP error
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }
            // If response is ok, parse the JSON body
            return response.json();
        })
        .then(data => { // This block only runs if response.ok was true and response.json() succeeded
            if (data.success) {
                accountCreated = true;
                console.log('Account created successfully. User credentials should be saved to credentials.json');

                // Generate 2FA setup - Use the correct endpoint and method
                fetch('/api/user/2fa/setup', { method: 'POST' }) // Specify POST method
                    .then(response => {
                        // Check for unauthorized specifically
                        if (response.status === 401) {
                            throw new Error('Unauthorized - Session likely not established yet.');
                        }
                        if (!response.ok) {
                            // Try to parse error from JSON response
                            return response.json().then(errData => {
                                throw new Error(errData.error || `Server error: ${response.status}`);
                            }).catch(() => {
                                // Fallback if response is not JSON
                                throw new Error(`Server error: ${response.status}`);
                            });
                        }
                        return response.json();
                    })
                    .then(twoFactorData => {
                        if (twoFactorData.success) {
                            // Use the correct property 'qr_code_url' and set the img src directly
                            const qrCodeImg = qrCodeElement.querySelector('img'); // Find the img tag within the div
                            if (qrCodeImg) {
                                 qrCodeImg.src = twoFactorData.qr_code_url; // Set src directly
                                 qrCodeImg.classList.add('is-visible'); // Ensure it's visible via CSS class
                            } else {
                                // Fallback if img tag wasn't there initially
                                qrCodeElement.innerHTML = `<img src="${twoFactorData.qr_code_url}" alt="QR Code" class="qr-code-img is-visible">`;
                            }
                            secretKeyElement.textContent = twoFactorData.secret;
                            showStep(2);
                        } else {
                            // Use .error if available, otherwise provide a default
                            showError('Failed to generate 2FA setup: ' + (twoFactorData.error || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error generating 2FA:', error);
                        // Display the specific error message caught
                        showError('Failed to generate 2FA setup: ' + error.message);
                    });
            } else {
                showError(data.error || 'Failed to create account'); // Use .error
            }
        })
        .catch(error => { // Catches errors thrown from the .then blocks above or network errors
            console.error('Setup error:', error);
            showError('Error: ' + error.message); // Display the error message
        });
    });

    // 2FA setup navigation
    twoFactorNextButton.addEventListener('click', function() {
        const code = verificationCodeInput.value;
        if (!code || code.length !== 6 || !/^\d{6}$/.test(code)) { // Add validation
            showError('Please enter a valid 6-digit verification code');
            return;
        }

        // Verify 2FA code - Use the correct endpoint
        fetch('/api/user/2fa/verify', { // Corrected endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: code })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                twoFactorEnabled = true;
                showStep(3); // Go to Auth Mode step
            } else {
                showError(data.message || 'Invalid verification code');
            }
        })
        .catch(error => {
            console.error('Error verifying 2FA code:', error);
            showError('Failed to verify code');
        });
    });

    // Skip 2FA setup
    skip2FALink.addEventListener('click', function() {
        showStep(3); // Go to Auth Mode step
    });

    // Auth Mode setup navigation
    authModeNextButton.addEventListener('click', function() {
        // Get the selected auth mode
        const selectedAuthMode = authModeSelect.value;

        // Save the authentication mode settings
        fetch('/api/settings/general', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                auth_mode: selectedAuthMode,
                local_access_bypass: selectedAuthMode === 'local_bypass',
                proxy_auth_bypass: selectedAuthMode === 'no_login'
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `Error: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Proceed to the finish step
            showStep(4);
        })
        .catch(error => {
            console.error('Error saving auth mode settings:', error);
            authModeErrorMessage.textContent = error.message || 'Error saving authentication settings';
            authModeErrorMessage.style.display = 'block';

            // Hide after 5 seconds
            setTimeout(() => {
                authModeErrorMessage.style.display = 'none';
            }, 5000);
        });
    });

    // Complete setup navigation
    finishSetupButton.addEventListener('click', function() {
        window.location.href = '/';
    });

    // Allow pressing Enter to continue
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission
            if (currentStep === 1 && document.activeElement !== accountNextButton) {
                accountNextButton.click();
            } else if (currentStep === 2 && document.activeElement !== twoFactorNextButton) {
                twoFactorNextButton.click();
            } else if (currentStep === 3 && document.activeElement !== authModeNextButton) {
                authModeNextButton.click();
            } else if (currentStep === 4 && document.activeElement !== finishSetupButton) {
                finishSetupButton.click();
            }
        }
    });

    // Always use dark mode
    document.body.classList.add('dark-theme');
    localStorage.setItem('newtarr-dark-mode', 'true');
});
