// SPDX-License-Identifier: MIT
// Table sorting initialization for MkDocs Material theme

document$.subscribe(function() {
    // Initialize table sorting for all tables in article content
    const tables = document.querySelectorAll("article table:not([class])");
    tables.forEach(table => {
        // Only initialize if tablesort is available and table has headers
        if (typeof tablesort !== 'undefined' && table.querySelector('thead')) {
            new tablesort(table);
            
            // Add visual indicator that table is sortable
            table.classList.add('sortable');
            
            // Add sort indicators to headers
            const headers = table.querySelectorAll('thead th');
            headers.forEach(header => {
                header.style.cursor = 'pointer';
                header.title = 'Click to sort';
            });
        }
    });
});