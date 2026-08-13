/* =====================================
   OPTIMIZED SINGLE SCROLL EVENT HANDLER
   (Navbar Hide/Show + Quantum AI + Zig-Zag Shapes)
===================================== */
let lastScrollPosition = window.pageYOffset;
const siteHeader = document.querySelector(".site-header");
let tickingViewport = false;

window.addEventListener("scroll", () => {
    let currentScrollPosition = window.pageYOffset;

    // --- 1. NAVBAR HIDE / SHOW LOGIC ---
    if (currentScrollPosition > lastScrollPosition && currentScrollPosition > 100) {
        siteHeader.classList.add("nav-hidden");
    } else {
        siteHeader.classList.remove("nav-hidden");
    }
    lastScrollPosition = currentScrollPosition;

    // --- 2. QUANTUM AI & ZIG-ZAG ANIMATIONS (Throttled using rAF) ---
    if (!tickingViewport) {
        window.requestAnimationFrame(() => {
            // Quantum AI Pieces Animation
            const quantumSection = document.querySelector(".quantum-section");
            const pieces = document.querySelectorAll(".piece");
            const systemViewport = document.getElementById("solar-system-viewport");

            if (systemViewport) {
                systemViewport.style.opacity = "1";
            }

            if (quantumSection && pieces.length > 0) {
                const qRect = quantumSection.getBoundingClientRect();
                const qScrollableDistance = window.innerHeight * 1.5;
                const qScrolledAmount = window.innerHeight - qRect.top;

                let qProgress = Math.min(Math.max(qScrolledAmount / qScrollableDistance, 0), 1);
                const isMobile = window.innerWidth <= 768;

                pieces.forEach((piece, index) => {
                    const multiplier = isMobile ? 60 : 200;
                    const moveY = (index % 2 === 0 ? 1 : -1) * (index + 1) * multiplier * (1 - qProgress);
                    const moveX = (index % 2 !== 0 ? 1 : -1) * (index * 25) * (1 - qProgress);
                    const currentScale = 0.2 + (qProgress * 0.8);

                    piece.style.transform = `
                        translate(${moveX}px, ${moveY}px)
                        rotate(${qProgress * 620}deg)
                        scale(${currentScale})
                    `;
                    piece.style.opacity = qProgress;
                });
            }

            // SourceQ Zig-Zag Connection Shapes
            const zigZagSection = document.getElementById("sourceq-steps");
            const shape1 = document.querySelector(".shape-1-to-2");
            const shape2 = document.querySelector(".shape-2-to-3");

            if (zigZagSection) {
                const zRect = zigZagSection.getBoundingClientRect();
                const zScrollDistance = window.innerHeight + zRect.height;
                const zScrolled = window.innerHeight - zRect.top;

                let zProgress = Math.max(0, Math.min(zScrolled / zScrollDistance, 1));

                if (shape1) {
                    const moveX = -zProgress * 400;
                    const moveY = zProgress * 600;
                    shape1.style.transform = `translate(${moveX}px, ${moveY}px) rotate(${zProgress * 90}deg)`;
                }

                if (shape2) {
                    const moveX = zProgress * 400;
                    const moveY = zProgress * 600;
                    shape2.style.transform = `translate(${moveX}px, ${moveY}px) rotate(${-zProgress * 90}deg)`;
                }
            }

            tickingViewport = false;
        });
        tickingViewport = true;
    }
}, { passive: true });

// Trigger scroll once on load
window.dispatchEvent(new Event('scroll'));

/* =====================================
   MOBILE MENU TOGGLE
===================================== */
const menuToggle = document.querySelector(".menu-toggle");
const navMenu = document.querySelector(".nav-menu");
if (menuToggle && navMenu) {
    menuToggle.addEventListener("click", () => {
        menuToggle.classList.toggle("active");
        navMenu.classList.toggle("active");
    });
}

/* =====================================
   HERO SLIDER
===================================== */
const slides = document.querySelectorAll(".hero-slide");
const dots = document.querySelectorAll(".hero-pagination span");
let currentSlide = 0;

function showSlide(index) {
    if (slides.length === 0) return;
    slides.forEach(slide => { slide.classList.remove("active"); });
    dots.forEach(dot => { dot.classList.remove("active"); });
    slides[index].classList.add("active");
    if (dots[index]) dots[index].classList.add("active");
}

function nextSlide() {
    if (slides.length === 0) return;
    currentSlide++;
    if (currentSlide >= slides.length) { currentSlide = 0; }
    showSlide(currentSlide);
}

if (slides.length > 0) {
    setInterval(nextSlide, 5000);
    dots.forEach((dot, index) => {
        dot.addEventListener("click", () => {
            currentSlide = index;
            showSlide(currentSlide);
        });
    });
}

/* =====================================
   FLOATING SEARCH INPUT & BLUR HANDLER
===================================== */
document.addEventListener("DOMContentLoaded", () => {
    const mockupCard = document.getElementById('mockupCard');
    const inlineSearchInput = document.getElementById('inlineSearchInput');

    if (inlineSearchInput && mockupCard) {
        // Jab user search box par click ya focus kare toh background blur ho jaye
        inlineSearchInput.addEventListener('focus', () => {
            mockupCard.classList.add('search-active');
        });

        // Jab user focus hataaye toh blur hat jaye
        inlineSearchInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (document.activeElement !== inlineSearchInput) {
                    mockupCard.classList.remove('search-active');
                }
            }, 200);
        });
    }
});

// Handle search and redirect to second page
function handleInlineSearch(event) {
    event.preventDefault();
    const inputField = document.getElementById('inlineSearchInput');
    if (inputField) {
        const query = inputField.value.trim();
        if (query) {
            window.location.href = `search-results.html?q=${encodeURIComponent(query)}`;
        }
    }
}

/* =====================================
   CONSULTING MODAL FORM HANDLER
===================================== */
const consultingBtn = document.getElementById("consultingBtn");
const consultingModal = document.getElementById("consultingModal");
const closeModal = document.getElementById("closeModal");

if (consultingBtn && consultingModal && closeModal) {
    consultingBtn.addEventListener("click", (e) => {
        e.preventDefault();
        consultingModal.classList.add("active");
    });

    closeModal.addEventListener("click", () => {
        consultingModal.classList.remove("active");
    });

    consultingModal.addEventListener("click", (e) => {
        if (e.target === consultingModal) {
            consultingModal.classList.remove("active");
        }
    });
}

/* =====================================
   LIVE RECOMMENDATION TICKER (2 LINES)
===================================== */
document.addEventListener("DOMContentLoaded", () => {
    const track1 = document.getElementById('tickerTrack1');
    const track2 = document.getElementById('tickerTrack2');
    if (!track1 || !track2) return;

    fetch('recommendations.json')
        .then(response => response.json())
        .then(data => {
            let htmlContent1 = '';
            let htmlContent2 = '';

            const mid = Math.ceil(data.length / 2);
            const list1 = data.slice(0, mid);
            const list2 = data.slice(mid);

            // Content ko 4 baar repeat karte hain taaki track lamba bane aur -50% loop seamless ho
            for (let i = 0; i < 4; i++) {
                list1.forEach(item => {
                    htmlContent1 += `
                        <span class="tick">
                            <img src="${item.flag}" alt="Flag" class="ticker-flag-icon">
                            <span class="category-badge">${item.category}</span>
                            <span class="recommendation-text">${item.recommendation}</span>
                        </span>
                    `;
                });

                list2.forEach(item => {
                    htmlContent2 += `
                        <span class="tick">
                            <img src="${item.flag}" alt="Flag" class="ticker-flag-icon">
                            <span class="category-badge">${item.category}</span>
                            <span class="recommendation-text">${item.recommendation}</span>
                        </span>
                    `;
                });
            }

            track1.innerHTML = htmlContent1;
            track2.innerHTML = htmlContent2;
        })
        .catch(error => {
            console.error('Error loading recommendations JSON:', error);
            track1.innerHTML = '<span class="tick">⚠️ Failed to load stream.</span>';
            track2.innerHTML = '<span class="tick">⚠️ Failed to load stream.</span>';
        });
});