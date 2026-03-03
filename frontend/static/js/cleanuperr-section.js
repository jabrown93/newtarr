    // Add event listener to the back button to return to Apps section
    document.addEventListener('DOMContentLoaded', function() {
        const backToAppsButton = document.getElementById('backToAppsButton');
        if (backToAppsButton) {
            backToAppsButton.addEventListener('click', function() {
                // Hide Cleanuperr section
                document.getElementById('cleanuperrSection').classList.remove('active');

                // Show Apps section
                document.getElementById('appsSection').classList.add('active');

                // Update the current section in the main UI
                if (newtarrUI) {
                    newtarrUI.currentSection = 'apps';

                    // Update the page title
                    const pageTitleElement = document.getElementById('currentPageTitle');
                    if (pageTitleElement) {
                        pageTitleElement.textContent = 'Apps';
                    }

                    // Update the selected menu item
                    const menuItems = document.querySelectorAll('.nav-item');
                    menuItems.forEach(item => {
                        item.classList.remove('active');
                        if (item.getAttribute('data-section') === 'apps') {
                            item.classList.add('active');
                        }
                    });

                    // Reset the app selector to a default app (not Cleanuperr)
                    const appsAppSelect = document.getElementById('appsAppSelect');
                    if (appsAppSelect) {
                        // Set to the first option that isn't Cleanuperr
                        for (let i = 0; i < appsAppSelect.options.length; i++) {
                            if (appsAppSelect.options[i].value !== 'cleanuperr') {
                                appsAppSelect.selectedIndex = i;
                                break;
                            }
                        }
                    }
                }
            });
        }
    });

    // Load GitHub star count for Cleanuperr
    function loadCleanuperrStarCount() {
        fetch('https://api.github.com/repos/flmorg/cleanuperr')
            .then(response => {
                if (!response.ok) {
                    // Handle rate limiting or other errors
                    if (response.status === 403) {
                        console.warn('GitHub API rate limit likely exceeded.');
                        throw new Error('Rate limited');
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const starsElement = document.getElementById('cleanuperr-stars-count');
                if (starsElement && data && data.stargazers_count !== undefined) {
                    starsElement.textContent = data.stargazers_count;
                } else if (starsElement) {
                    starsElement.textContent = 'N/A';
                }
            })
            .catch(error => {
                console.error('Error loading Cleanuperr star count from GitHub:', error);
                const starsElement = document.getElementById('cleanuperr-stars-count');
                if (starsElement) {
                    starsElement.textContent = error.message === 'Rate limited' ? 'Rate Limited' : 'Error';
                }
            });
    }

    // Load star count when the page is loaded
    loadCleanuperrStarCount();
