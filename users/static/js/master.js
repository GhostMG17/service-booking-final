// Simple animation for cards when they come into view
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.barber-card');

    function checkCards() {
        cards.forEach(card => {
            const cardTop = card.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;

            if(cardTop < windowHeight - 100) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    }

    // Set initial state
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'all 0.6s ease-out';
    });

    window.addEventListener('scroll', checkCards);
    checkCards(); // Check on load
});