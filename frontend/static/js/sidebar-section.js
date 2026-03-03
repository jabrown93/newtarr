// Function to set active nav item based on the current hash
function setActiveNavItem() {
    // Get all navigation items
    const navItems = document.querySelectorAll('.nav-item');

    // Remove active class from all items
    navItems.forEach(item => {
        item.classList.remove('active');
    });

    // Get current hash, or default to home if no hash
    let currentHash = window.location.hash;
    if (!currentHash) {
        currentHash = '#home';
    }

    // Set the appropriate nav item as active
    const selector = currentHash === '#home' ? '#homeNav' :
                     currentHash === '#history' ? '#historyNav' :
                     currentHash === '#logs' ? '#logsNav' :
                     currentHash === '#apps' ? '#appsNav' :
                     currentHash === '#cleanuperr' ? '#appsNav' : // Cleanuperr uses the apps nav
                     currentHash === '#settings' ? '#settingsNav' :
                     currentHash === '#scheduling' ? '#schedulingNav' : '#homeNav';

    const activeItem = document.querySelector(selector);
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

// Set active on page load
document.addEventListener('DOMContentLoaded', setActiveNavItem);

// Update active when hash changes
window.addEventListener('hashchange', setActiveNavItem);
