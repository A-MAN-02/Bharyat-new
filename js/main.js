const menuToggle=document.querySelector(".menu-toggle");
const navMenu=document.querySelector(".nav-menu");
menuToggle.addEventListener("click",()=>{
menuToggle.classList.toggle("active");
navMenu.classList.toggle("active");
});

/* =====================================
   HERO SLIDER
===================================== */
const slides = document.querySelectorAll(".hero-slide");
const dots = document.querySelectorAll(".hero-pagination span");
let currentSlide = 0;

function showSlide(index){
    slides.forEach(slide=>{
        slide.classList.remove("active");
    });
    dots.forEach(dot=>{
        dot.classList.remove("active");
    });

    slides[index].classList.add("active");
    dots[index].classList.add("active");
}

function nextSlide(){
    currentSlide++;
    if(currentSlide >= slides.length){
        currentSlide = 0;
    }
    showSlide(currentSlide);
}

setInterval(nextSlide,5000);
dots.forEach((dot,index)=>{
    dot.addEventListener("click",()=>{
        currentSlide=index;
        showSlide(currentSlide);
    });
});


// =====================================
// QUANTUM AI DECISION FLOW ANIMATION
// =====================================

// 1. Cycle Cards Logic
const feedCards = [...document.querySelectorAll(".feed-card")];
const outputCards = [...document.querySelectorAll(".output-card")];
const status = document.getElementById("status");

const statuses = [
    "Reading global news and RSS feeds…",
    "Normalizing supplier and price data…",
    "Evaluating lifecycle and lead-time shifts…",
    "Calculating confidence and risk…",
    "Generating decision recommendations…"
];

let feedIndex = 0;
let outputIndex = 0;
let statusIndex = 0;

function cycleInputs() {
    if(feedCards.length === 0) return;
    feedCards.forEach(card => card.classList.remove("active"));
    feedCards[feedIndex].classList.add("active");
    feedIndex = (feedIndex + 1) % feedCards.length;
}

function cycleOutputs() {
    if(outputCards.length === 0) return;
    outputCards.forEach(card => card.classList.remove("active"));
    outputCards[outputIndex].classList.add("active");
    outputIndex = (outputIndex + 1) % outputCards.length;
}

function cycleStatus() {
    if(!status) return;
    status.textContent = statuses[statusIndex];
    statusIndex = (statusIndex + 1) % statuses.length;
}

cycleInputs();
cycleOutputs();
cycleStatus();

setInterval(cycleInputs, 1100);
setInterval(cycleOutputs, 1450);
setInterval(cycleStatus, 1800);

// 2. The Floating Scroll Animation
window.addEventListener("scroll", () => {
    const section = document.querySelector(".quantum-section");
    const pieces = document.querySelectorAll(".piece");

    if (!section || pieces.length === 0) return;

    const rect = section.getBoundingClientRect();
    
    // Adjusted logic for smoother flow without relying on header height
    const scrollableDistance = window.innerHeight * 1.5; 
    const scrolledAmount = window.innerHeight - rect.top;

    let progress = scrolledAmount / scrollableDistance;
    progress = Math.min(Math.max(progress, 0), 1);

    const isMobile = window.innerWidth <= 768;

    pieces.forEach((piece, index) => {
        // Multipliers set to make pieces move nicely but not too far
        const multiplier = isMobile ? 15 : 60; 
        const moveY = (index % 2 === 0 ? 1 : -1) * (index + 1) * multiplier * progress;
        const moveX = (index % 2 !== 0 ? 1 : -1) * (index * 10) * progress;

        piece.style.transform = `
            translate(${moveX}px, ${moveY}px)
            rotate(${progress * 45}deg)
            scale(${1 + progress * 0.2})
        `;
    });
});



// =====================================
// SOURCEQ ZIG-ZAG CONNECTION SHAPES JS
// =====================================
window.addEventListener("scroll", () => {
    const section = document.getElementById("sourceq-steps");
    const shape1 = document.querySelector(".shape-1-to-2");
    const shape2 = document.querySelector(".shape-2-to-3");

    if (!section) return;

    // Section ke hisab se kitna scroll kiya hai uski calculation
    const rect = section.getBoundingClientRect();
    const scrollDistance = window.innerHeight + rect.height;
    const scrolled = window.innerHeight - rect.top;

    // Progress 0 se 1 ke beech rahega
    let progress = Math.max(0, Math.min(scrolled / scrollDistance, 1));

    // Shape 1 (Blue): Step 1 (Right) se Step 2 (Left) ki taraf slide hoga
    if (shape1) {
        // Move Left (-X) and Down (Y)
        const moveX = -progress * 400; // Left movement
        const moveY = progress * 600;  // Down movement
        shape1.style.transform = `translate(${moveX}px, ${moveY}px) rotate(${progress * 90}deg)`;
    }

    // Shape 2 (Green): Step 2 (Left) se Step 3 (Right) ki taraf slide hoga
    if (shape2) {
        // Move Right (+X) and Down (Y)
        const moveX = progress * 400; // Right movement
        const moveY = progress * 600; // Down movement
        shape2.style.transform = `translate(${moveX}px, ${moveY}px) rotate(${-progress * 90}deg)`;
    }
});