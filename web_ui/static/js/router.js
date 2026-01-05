// Simple SPA Router
const routes = {
    '/': 'candles',
    '/fakeouts': 'fakeouts',
    '/charts': 'charts',
    '/analytics': 'analytics',
    '/ml': 'ml'
};

// Navigate to a route
function navigateTo(url) {
    history.pushState(null, null, url);
    router();
}

// Main router function
async function router() {
    const path = window.location.pathname;
    const route = routes[path] || 'candles';
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });

    // Get the app container
    const app = document.getElementById('app');

    // Route to the appropriate page
    switch(route) {
        case 'candles':
            if (typeof loadCandlesPage === 'function') {
                loadCandlesPage(app);
            } else {
                app.innerHTML = '<div class="loading"><p>Candles page loading...</p></div>';
            }
            break;
        
        case 'fakeouts':
            app.innerHTML = `
                <h1 class="page-title">Fakeouts</h1>
                <div class="info">
                    <div class="info-text">Fakeouts page coming soon...</div>
                </div>
            `;
            break;
        
        case 'charts':
            app.innerHTML = `
                <h1 class="page-title">Charts</h1>
                <div class="info">
                    <div class="info-text">Charts page coming soon...</div>
                </div>
            `;
            break;
        
        case 'analytics':
            app.innerHTML = `
                <h1 class="page-title">Analytics</h1>
                <div class="info">
                    <div class="info-text">Analytics page coming soon...</div>
                </div>
            `;
            break;
        
        case 'ml':
            app.innerHTML = `
                <h1 class="page-title">Machine Learning</h1>
                <div class="info">
                    <div class="info-text">ML page coming soon...</div>
                </div>
            `;
            break;
        
        default:
            app.innerHTML = `
                <div class="error">
                    <h2>404 - Page Not Found</h2>
                    <p>The page you're looking for doesn't exist.</p>
                </div>
            `;
    }
}

// Handle navigation clicks
document.addEventListener('DOMContentLoaded', () => {
    // Attach click handlers to all nav links
    document.querySelectorAll('[data-link]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(e.target.getAttribute('href'));
        });
    });

    // Handle browser back/forward buttons
    window.addEventListener('popstate', router);

    // Initial route
    router();
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { navigateTo, router };
}