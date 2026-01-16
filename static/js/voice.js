// EchoMarket - Voice Command Handler

class VoiceHandler {
    constructor() {
        this.isListening = false;
        this.voiceBtn = null;
        this.searchOffset = 0;
    }

    init() {
        this.voiceBtn = document.getElementById('voiceBtn');
        if (this.voiceBtn) {
            this.voiceBtn.addEventListener('click', () => this.startListening());
        }
    }

    async startListening() {
        if (this.isListening) return;

        this.isListening = true;
        this.updateButtonState(true);

        try {
            const response = await fetch('/dinle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            this.handleResponse(data);

        } catch (error) {
            console.error('Voice error:', error);
            this.showMessage('Ses hatasi olustu.', 'error');
        } finally {
            this.isListening = false;
            this.updateButtonState(false);
        }
    }

    handleResponse(data) {
        if (data.status === 'error') {
            this.showMessage(data.message, 'error');
            return;
        }

        // Show recognized command
        this.showMessage(data.message || `Algilanan: ${data.command}`, 'success');

        // Handle actions
        if (data.action === 'redirect' && data.redirect_url) {
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        } else if (data.action === 'next_page') {
            this.searchOffset += 4;
            this.loadNextProducts();
        } else if (data.state === 'LIST_PRODUCTS' && data.query) {
            this.searchProducts(data.query);
        }
    }

    async searchProducts(query) {
        try {
            const response = await fetch('/search_products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, offset: this.searchOffset })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.displayProducts(data.products);
                this.showMessage(data.message_text, 'success');
            } else {
                this.showMessage('Urun bulunamadi.', 'error');
            }

        } catch (error) {
            console.error('Search error:', error);
        }
    }

    async loadNextProducts() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput ? searchInput.value : '';
        await this.searchProducts(query);
    }

    displayProducts(products) {
        const container = document.getElementById('productGrid');
        if (!container) return;

        container.innerHTML = products.map(product => `
            <div class="product-card">
                <img src="${product.image}" alt="${product.name}" class="product-image">
                <div class="product-info">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-price">${product.price.toFixed(2)} TL</p>
                    <div class="product-rating">${'★'.repeat(Math.round(product.rating))}${'☆'.repeat(5 - Math.round(product.rating))}</div>
                    <button onclick="addToCart(${product.id})" class="btn btn-primary">Sepete Ekle</button>
                </div>
            </div>
        `).join('');
    }

    updateButtonState(listening) {
        if (this.voiceBtn) {
            this.voiceBtn.classList.toggle('listening', listening);
            this.voiceBtn.innerHTML = listening ? '🔴' : '🎤';
        }
    }

    showMessage(message, type = 'info') {
        // Remove existing messages
        const existing = document.querySelector('.voice-message');
        if (existing) existing.remove();

        // Create message element
        const msgDiv = document.createElement('div');
        msgDiv.className = `voice-message alert alert-${type}`;
        msgDiv.textContent = message;
        msgDiv.style.cssText = `
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1001;
            padding: 15px 30px;
            border-radius: 10px;
            animation: fadeIn 0.3s;
        `;

        document.body.appendChild(msgDiv);

        // Auto remove after 3 seconds
        setTimeout(() => msgDiv.remove(), 3000);
    }
}

// Initialize voice handler
const voiceHandler = new VoiceHandler();
document.addEventListener('DOMContentLoaded', () => voiceHandler.init());

// Global function for adding to cart
async function addToCart(productId) {
    try {
        const response = await fetch('/add_to_cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Update cart count in header
            const cartCount = document.getElementById('cartCount');
            if (cartCount) {
                cartCount.textContent = data.cart_count;
            }
            voiceHandler.showMessage('Urun sepete eklendi!', 'success');
        } else {
            voiceHandler.showMessage(data.message || 'Hata olustu.', 'error');
        }

    } catch (error) {
        console.error('Add to cart error:', error);
        voiceHandler.showMessage('Baglanti hatasi.', 'error');
    }
}
