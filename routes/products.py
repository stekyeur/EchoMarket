from flask import Blueprint, render_template, request, jsonify, session

from services.product_service import ProductService
from services.cart_service import CartService

products_bp = Blueprint('products', __name__)
product_service = ProductService()
cart_service = CartService()


@products_bp.route('/market')
def market():
    """Market page with product listing."""
    page = request.args.get('page', 1, type=int)
    raw_query = request.args.get('q', '').lower()

    # Get cart count
    cart_count = 0
    if 'user_id' in session:
        cart_count = cart_service.get_cart_count(session['user_id'])

    # Get products
    products = product_service.get_products_for_market(raw_query, page)

    # Welcome mode if no query and no products
    is_welcome = (not raw_query) and (not products)

    return render_template(
        'market.html',
        products=products,
        current_page=page,
        search_query=raw_query,
        cart_count=cart_count,
        welcome_mode=is_welcome
    )


@products_bp.route('/search_products', methods=['POST'])
def search_products():
    """AJAX endpoint for product search."""
    data = request.get_json()
    voice_query = data.get('query', '').lower()
    offset = data.get('offset', 0)

    # Detect filters
    is_cheapest, is_expensive, is_top_rated = product_service.detect_filters(voice_query)

    # Calculate page from offset
    page = (offset // 4) + 1

    # Search products
    products, message = product_service.search_products(
        voice_query, page, is_cheapest, is_expensive, is_top_rated
    )

    if products:
        return jsonify({
            'status': 'success',
            'products': products,
            'message_text': message
        })

    return jsonify({'status': 'empty', 'message': 'Urun bulunamadi.'})
