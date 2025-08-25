// SPDX-License-Identifier: MIT
// Custom JavaScript for Git AI Reporter Documentation

document.addEventListener('DOMContentLoaded', function() {
    // Initialize table sorting if tables exist
    const tables = document.querySelectorAll('article table');
    tables.forEach(table => {
        if (typeof tablesort !== 'undefined') {
            new tablesort(table);
        }
    });
    
    // Add copy-to-clipboard functionality for CLI examples
    const cliExamples = document.querySelectorAll('.cli-example pre, .language-bash pre, .language-shell pre');
    cliExamples.forEach(pre => {
        // Check if copy button doesn't already exist
        if (!pre.parentElement.querySelector('.copy-button')) {
            const button = document.createElement('button');
            button.className = 'copy-button';
            button.textContent = 'Copy';
            button.setAttribute('aria-label', 'Copy to clipboard');
            
            button.addEventListener('click', async () => {
                const code = pre.textContent || pre.innerText;
                try {
                    await navigator.clipboard.writeText(code);
                    button.textContent = 'Copied!';
                    button.classList.add('copied');
                    setTimeout(() => {
                        button.textContent = 'Copy';
                        button.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                    button.textContent = 'Error';
                    setTimeout(() => {
                        button.textContent = 'Copy';
                    }, 2000);
                }
            });
            
            pre.parentElement.style.position = 'relative';
            pre.parentElement.appendChild(button);
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href && href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    // Update URL without jumping
                    history.pushState(null, null, href);
                }
            }
        });
    });
    
    // Add loading indicators for external links
    document.querySelectorAll('a[href^="http"]').forEach(link => {
        link.addEventListener('click', function() {
            if (!this.classList.contains('no-loading')) {
                this.classList.add('loading');
                // Remove loading class after a delay (in case page doesn't unload)
                setTimeout(() => {
                    this.classList.remove('loading');
                }, 5000);
            }
        });
    });
    
    // Enhanced search experience
    const searchInput = document.querySelector('.md-search__input');
    if (searchInput) {
        // Add keyboard shortcut hint
        searchInput.setAttribute('placeholder', 'Search (Press "/" to focus)');
        
        // Global keyboard shortcut for search
        document.addEventListener('keydown', function(e) {
            // "/" key to focus search (when not in an input)
            if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                searchInput.focus();
            }
            // Escape key to blur search
            if (e.key === 'Escape' && document.activeElement === searchInput) {
                searchInput.blur();
            }
        });
    }
    
    // Add version info to footer if available
    const footer = document.querySelector('.md-footer-meta__inner');
    if (footer && window.GIT_AI_REPORTER_VERSION) {
        const versionSpan = document.createElement('span');
        versionSpan.className = 'version-info';
        versionSpan.textContent = `v${window.GIT_AI_REPORTER_VERSION}`;
        footer.appendChild(versionSpan);
    }
    
    // Lazy load images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Add progress indicator for long pages
    const progressBar = document.createElement('div');
    progressBar.className = 'reading-progress';
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--md-primary-fg-color), var(--md-accent-fg-color));
        z-index: 1000;
        transition: width 0.2s ease;
        width: 0%;
    `;
    document.body.appendChild(progressBar);
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY;
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = (scrollTop / documentHeight) * 100;
        progressBar.style.width = `${progress}%`;
    });
    
    // Terminal animation for termage examples
    const terminalBlocks = document.querySelectorAll('.termage-output, .language-termage');
    terminalBlocks.forEach(block => {
        // Add terminal window decoration
        const terminal = document.createElement('div');
        terminal.className = 'terminal-window';
        
        const header = document.createElement('div');
        header.className = 'terminal-header';
        header.innerHTML = `
            <span class="terminal-button terminal-close"></span>
            <span class="terminal-button terminal-minimize"></span>
            <span class="terminal-button terminal-maximize"></span>
            <span class="terminal-title">Terminal - git-ai-reporter</span>
        `;
        
        block.parentElement.insertBefore(terminal, block);
        terminal.appendChild(header);
        terminal.appendChild(block);
    });
});

// Table sort initialization
document$.subscribe(function() {
    const tables = document.querySelectorAll("article table:not([class])");
    tables.forEach(table => {
        if (typeof tablesort !== 'undefined') {
            new tablesort(table);
        }
    });
});