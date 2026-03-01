document.addEventListener('DOMContentLoaded', function() {
            // Make sure the navigation link is active
            const schedulingNav = document.getElementById('schedulingNav');
            if (schedulingNav) schedulingNav.classList.add('active');

            // Apply scrolling fixes immediately and after a delay
            function applyScrollingFixes() {
                // Fix body and main content scrolling
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';

                const mainContent = document.querySelector('.main-content');
                if (mainContent) {
                    mainContent.style.overflowY = 'auto';
                    mainContent.style.height = 'auto';
                }

                const schedulingPage = document.getElementById('schedulingPage');
                if (schedulingPage) {
                    schedulingPage.style.overflowY = 'auto';
                    schedulingPage.style.height = 'auto';
                    schedulingPage.style.maxHeight = 'none';
                }

                // Fix all scheduler containers
                const containers = document.querySelectorAll('.scheduler-container, .scheduler-panel, .panel-content, #schedulesContainer');
                containers.forEach(container => {
                    container.style.overflow = 'visible';
                    container.style.height = 'auto';
                    container.style.maxHeight = 'none';
                });
            }

            // Apply immediately and after a short delay
            applyScrollingFixes();
            setTimeout(applyScrollingFixes, 500);
            setTimeout(applyScrollingFixes, 1000);

            // Also apply on window resize
            window.addEventListener('resize', applyScrollingFixes);
        });
