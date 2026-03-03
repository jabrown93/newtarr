document.addEventListener('DOMContentLoaded', function() {
            // Make sure the navigation link is active
            const schedulingNav = document.getElementById('schedulingNav');
            if (schedulingNav) schedulingNav.classList.add('active');

            // Apply scrolling fixes immediately and after a delay
            function applyScrollingFixes() {
                // Fix body and main content scrolling using CSS classes (CSP-safe)
                document.body.classList.add('scheduling-scroll-body');
                document.documentElement.classList.add('scheduling-scroll-root');

                const mainContent = document.querySelector('.main-content');
                if (mainContent) {
                    mainContent.classList.add('scheduling-scroll-main');
                }

                const schedulingPage = document.getElementById('schedulingPage');
                if (schedulingPage) {
                    schedulingPage.classList.add('scheduling-scroll-page');
                }

                // Fix all scheduler containers
                const containers = document.querySelectorAll('.scheduler-container, .scheduler-panel, .panel-content, #schedulesContainer');
                containers.forEach(container => {
                    container.classList.add('scheduling-scroll-container');
                });
            }

            // Apply immediately and after a short delay
            applyScrollingFixes();
            setTimeout(applyScrollingFixes, 500);
            setTimeout(applyScrollingFixes, 1000);

            // Also apply on window resize
            window.addEventListener('resize', applyScrollingFixes);
        });
