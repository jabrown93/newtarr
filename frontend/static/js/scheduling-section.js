    document.addEventListener('DOMContentLoaded', function() {
        // Add event listener for the Yes/No dropdown
        const yesNoDropdown = document.getElementById('yesNoDropdown');
        if (yesNoDropdown) {
            yesNoDropdown.addEventListener('change', function() {
                console.debug('Selected option: ' + this.value); // Keep at DEBUG level per user preference
            });
        }
    });
