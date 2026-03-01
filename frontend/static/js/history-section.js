    // Fixes for formatting the history items
    document.addEventListener('DOMContentLoaded', function() {
        // Simplified scrollbar setup for history section - matches logs approach
        const fixHistoryScrolling = function() {
            // Apply minimal CSS needed for proper table scrolling
            const style = document.createElement('style');
            style.id = 'history-scrollbar-fix';
            style.innerHTML = `
                /* Ensure the history container allows proper scrolling */
                .history-container {
                    overflow: visible !important;
                }

                /* Ensure the table wrapper has proper scrolling */
                .modern-table-wrapper {
                    height: calc(100vh - 200px) !important;
                    overflow-y: auto !important;
                    overflow-x: auto !important;
                }

                /* Prevent text from wrapping in table cells except for the second column */
                .modern-table td:not(:nth-child(2)), .history-table td:not(:nth-child(2)) {
                    white-space: nowrap !important;
                    overflow: hidden !important;
                    text-overflow: ellipsis !important;
                }
            `;
            document.head.appendChild(style);

            // Keep the table wrapper reference for potential future use
            const tableWrapper = document.querySelector('.modern-table-wrapper');
            if (tableWrapper) {
                // Remove any inline styles that could be interfering
                tableWrapper.style.removeProperty('overflow-y');
                tableWrapper.style.removeProperty('overflow-x');
                tableWrapper.style.removeProperty('height');
                tableWrapper.style.removeProperty('max-height');
                tableWrapper.style.removeProperty('min-height');

                // Let the CSS handle the scrollbar
                tableWrapper.classList.remove('force-scrollbar');
            }
        };

        // Run immediately for history page
        if (newtarrUI && newtarrUI.currentSection === 'history') {
            setTimeout(fixHistoryScrolling, 100);
        }

        // Add event listener for section changes
        document.addEventListener('sectionChanged', function(e) {
            if (e.detail.section === 'history') {
                setTimeout(fixHistoryScrolling, 100);
            } else {
                // Remove existing style if it exists
                const existingStyle = document.getElementById('history-scrollbar-fix');
                if (existingStyle) {
                    existingStyle.remove();
                }

                // Force the table wrapper to have a fixed height to ensure scrollbar appears
                const tableWrapper = document.querySelector('.modern-table-wrapper');
                if (tableWrapper) {
                    // Add a class to force scrollbars to be visible
                    tableWrapper.classList.add('force-scrollbar');
                }

                // Also clear inline styles
                document.querySelectorAll('#app, .main-content, body, #main, .main-content > .inner, .section-content').forEach(container => {
                    if (container) {
                        container.style.overflow = '';
                    }
                });
            }
        });

        // Original function exists in history.js
        const originalRenderHistoryData = historyModule.renderHistoryData;

        if (typeof historyModule !== 'undefined') {
            // Override the render method to apply our styling
            historyModule.renderHistoryData = function(data) {
                // Call the original render method
                originalRenderHistoryData.call(this, data);

                // After the data is rendered, format the operation status columns
                const operationCells = document.querySelectorAll('#historyTableBody tr td:nth-child(3)');
                operationCells.forEach(cell => {
                    const operationText = cell.textContent.trim();
                    const statusClass = operationText.toLowerCase() === 'success' ? 'success' :
                                 operationText.toLowerCase() === 'missing' ? 'missing' :
                                 operationText.toLowerCase() === 'upgrade' ? 'upgrade' :
                                 operationText.toLowerCase() === 'warning' ? 'warning' : 'error';

                    cell.innerHTML = `<span class="operation-status ${statusClass}">${operationText}</span>`;
                });
            };
        }
    });
