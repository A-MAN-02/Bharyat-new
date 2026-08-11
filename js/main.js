const menuToggle = document.querySelector(".menu-toggle");
const navMenu = document.querySelector(".nav-menu");
menuToggle.addEventListener("click", () => {
    menuToggle.classList.toggle("active");
    navMenu.classList.toggle("active");
});

/* =====================================
   HERO SLIDER
===================================== */
const slides = document.querySelectorAll(".hero-slide");
const dots = document.querySelectorAll(".hero-pagination span");
let currentSlide = 0;

function showSlide(index) {
    slides.forEach(slide => { slide.classList.remove("active"); });
    dots.forEach(dot => { dot.classList.remove("active"); });
    slides[index].classList.add("active");
    dots[index].classList.add("active");
}

function nextSlide() {
    currentSlide++;
    if (currentSlide >= slides.length) { currentSlide = 0; }
    showSlide(currentSlide);
}

setInterval(nextSlide, 5000);
dots.forEach((dot, index) => {
    dot.addEventListener("click", () => {
        currentSlide = index;
        showSlide(currentSlide);
    });
});

/* =====================================
   ALL SCROLL ANIMATIONS (COMBINED)
===================================== */
let tickingViewport = false;

window.addEventListener("scroll", () => {
    
// --- QUANTUM AI PIECES ZOOM-IN & FLOAT ANIMATION ---
const quantumSection = document.querySelector(".quantum-section");
const pieces = document.querySelectorAll(".piece");
const systemViewport = document.getElementById("solar-system-viewport");

if (systemViewport) {
    systemViewport.style.opacity = "1";
}

if (!tickingViewport) {
    window.requestAnimationFrame(() => {
        if (quantumSection && pieces.length > 0) {
            const qRect = quantumSection.getBoundingClientRect();
            const qScrollableDistance = window.innerHeight * 1.5; 
            const qScrolledAmount = window.innerHeight - qRect.top;
            
            // Progress 0 se 1 tak calculate hogi
            let qProgress = Math.min(Math.max(qScrolledAmount / qScrollableDistance, 0), 1);
            const isMobile = window.innerWidth <= 768;

            pieces.forEach((piece, index) => {
                // 1. Translation multiplier bada diya taaki pieces zyada dur se travel karke aayein
                const multiplier = isMobile ? 60 : 200; 
                
                // Start mein pieces thodi dur (offset position) par rahengi aur scroll ke sath 0 (center/final pos) par aayengi
                const moveY = (index % 2 === 0 ? 1 : -1) * (index + 1) * multiplier * (1 - qProgress);
                const moveX = (index % 2 !== 0 ? 1 : -1) * (index * 25) * (1 - qProgress);

                // 2. Scale ko 0.2 (bahut chota/dur) se shuru karke 1 (normal size) tak laana
                const currentScale = 0.2 + (qProgress * 0.8); // 0.2 se start hokar 1.0 tak jayega

                // Apply cinematic zoom-in transform
                piece.style.transform = `
                    translate(${moveX}px, ${moveY}px)
                    rotate(${qProgress * 620}deg)
                    scale(${currentScale})
                `;
                
                // Optional: Jab tak dur hain tab tak opacity kam rahe, paas aate hi clear ho jaye
                piece.style.opacity = qProgress;
            });
        }
        tickingViewport = false;
    });
    tickingViewport = true;
}

    // --- 2. SOURCEQ ZIG-ZAG CONNECTION SHAPES ---
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
});

// Trigger scroll once on load
window.dispatchEvent(new Event('scroll'));

document.addEventListener("DOMContentLoaded", () => {
    const mockupCard = document.getElementById('mockupCard');
    const searchIconBtn = document.getElementById('searchIconBtn');
    const searchBar = document.getElementById('searchBar');
    const closeSearchBtn = document.getElementById('closeSearchBtn');
    const inlineSearchInput = document.getElementById('inlineSearchInput');

    if (searchIconBtn && mockupCard) {
        // Open search bar on clicking green icon
        searchIconBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            mockupCard.classList.add('search-active');
            inlineSearchInput.focus();
        });

        // Close on clicking 'X' button
        closeSearchBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            mockupCard.classList.remove('search-active');
            inlineSearchInput.value = '';
        });

        // Close when clicking anywhere else on the screen
        document.addEventListener('click', (e) => {
            if (mockupCard.classList.contains('search-active')) {
                if (!searchBar.contains(e.target) && !searchIconBtn.contains(e.target)) {
                    mockupCard.classList.remove('search-active');
                    inlineSearchInput.value = '';
                }
            }
        });
    }
});

// Handle search and redirect to second page
function handleInlineSearch(event) {
    event.preventDefault();
    const query = document.getElementById('inlineSearchInput').value.trim();
    if (query) {
        window.location.href = `search-results.html?q=${encodeURIComponent(query)}`;
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


