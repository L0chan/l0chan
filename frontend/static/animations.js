document.addEventListener("DOMContentLoaded", () => {
    // 1. Advanced Scroll Reveals (Staggered & Scaled)
    const elementsToReveal = document.querySelectorAll('.product-card, .stat-card, .card, .panel, .form-panel, .box, .section-head, .hero-copy');
    
    // Set initial state
    elementsToReveal.forEach(el => el.classList.add('reveal-hidden'));

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Stagger delay based on index in current viewport
                setTimeout(() => {
                    entry.target.classList.remove('reveal-hidden');
                    entry.target.classList.add('reveal-visible');
                }, (index % 6) * 100);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    elementsToReveal.forEach(el => revealObserver.observe(el));

    // 2. Vanilla-Tilt 3D Effect for Cards
    const tiltElements = document.querySelectorAll('.product-card, .stat-card, .card');
    
    tiltElements.forEach(el => {
        el.addEventListener('mousemove', (e) => {
            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate rotation (max 15 degrees)
            const rotateX = ((y - centerY) / centerY) * -10;
            const rotateY = ((x - centerX) / centerX) * 10;
            
            el.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            
            // Dynamic glare effect
            el.style.background = `
                radial-gradient(circle at ${x}px ${y}px, rgba(255, 255, 255, 0.15) 0%, transparent 60%),
                var(--glass-hover)
            `;
        });
        
        el.addEventListener('mouseleave', () => {
            el.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
            el.style.background = 'var(--glass-base)';
            // Smooth reset
            el.style.transition = 'transform 0.5s ease, background 0.5s ease';
            setTimeout(() => { el.style.transition = ''; }, 500); // Remove transition to avoid lag on enter
        });
        
        el.addEventListener('mouseenter', () => {
            el.style.transition = 'none';
        });
    });

    // 3. Magnetic Hover Effect for Buttons
    const magneticButtons = document.querySelectorAll('.primary-btn, .search-btn, .buy-btn, .btn.primary');
    
    magneticButtons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            // Move button slightly towards cursor
            btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px) scale(1.05)`;
        });
        
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = `translate(0px, 0px) scale(1)`;
            btn.style.transition = 'transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1)';
            setTimeout(() => { btn.style.transition = ''; }, 400);
        });
        
        btn.addEventListener('mouseenter', () => {
            btn.style.transition = 'none';
        });
    });

    // 4. Parallax Hero Floating Elements
    const heroVisual = document.querySelector('.hero-visual');
    const authLogo = document.querySelector('.auth-logo');
    
    window.addEventListener('scroll', () => {
        const scroll = window.scrollY;
        if (heroVisual) {
            heroVisual.style.transform = `translateY(${scroll * -0.15}px) rotate(${scroll * 0.02}deg)`;
        }
        if (authLogo) {
            authLogo.style.transform = `translateY(${scroll * -0.1}px)`;
        }
    });
});
