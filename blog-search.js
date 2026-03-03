// Blog search functionality
function searchArticles() {
    const query = document.getElementById('search-input').value.toLowerCase();
    const cards = document.querySelectorAll('.article-card');
    
    cards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const excerpt = card.querySelector('.excerpt').textContent.toLowerCase();
        const tags = card.querySelector('.tags').textContent.toLowerCase();
        
        if (title.includes(query) || excerpt.includes(query) || tags.includes(query)) {
            card.style.display = 'block';
        } else {
            card.style.display = query ? 'none' : 'block';
        }
    });
    
    document.getElementById('search-count').textContent = 
        Array.from(cards).filter(c => c.style.display !== 'none').length;
}
