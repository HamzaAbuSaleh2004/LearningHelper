/**
 * LearnPath AI — Frontend JavaScript
 * Star ratings, animations, and UI interactions
 */

// ═══ DOM Ready ═══════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    animateProgressBars();
    autoHideFlashMessages();
    initScrollAnimations();
});


// ═══ Animate progress bars on scroll into view ═══════════════════
function animateProgressBars() {
    const bars = document.querySelectorAll('.progress-fill');
    if (!bars.length) return;
    
    setTimeout(() => {
        bars.forEach(bar => {
            if (bar.dataset.width) {
                bar.style.width = bar.dataset.width;
            }
        });
    }, 400);
}


// ═══ Auto-hide flash messages ════════════════════════════════════
function autoHideFlashMessages() {
    const flashContainer = document.getElementById('flash-messages');
    if (!flashContainer) return;
    
    setTimeout(() => {
        flashContainer.style.transition = 'opacity 0.5s, transform 0.5s';
        flashContainer.style.opacity = '0';
        flashContainer.style.transform = 'translateY(-10px)';
        setTimeout(() => flashContainer.remove(), 500);
    }, 4000);
}


// ═══ Scroll-triggered animations ═════════════════════════════════
function initScrollAnimations() {
    if (!('IntersectionObserver' in window)) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // Observe elements that should animate on scroll
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}


// ═══ Course search client-side filter ════════════════════════════
function filterCourses(searchText) {
    const cards = document.querySelectorAll('#courses-grid > div');
    const term = searchText.toLowerCase();
    
    cards.forEach(card => {
        const title = card.querySelector('h3')?.textContent?.toLowerCase() || '';
        card.style.display = title.includes(term) ? '' : 'none';
    });
}


// ═══ Smooth number counter animation ═════════════════════════════
function animateCounter(element, target, duration = 1500) {
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        
        element.textContent = current + '%';
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}
