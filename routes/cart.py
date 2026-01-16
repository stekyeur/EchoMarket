from flask import Blueprint, render_template, request, jsonify, session, redirect

from services.cart_service import CartService

cart_bp = Blueprint('cart', __name__)
cart_service = CartService()


@cart_bp.route('/cart')
def cart():
    """Cart page."""
    if 'user_id' not in session:
        return redirect('/login')

    cart_items, total = cart_service.get_cart_items(session['user_id'])
    cart_count = cart_service.get_cart_count(session['user_id'])

    return render_template(
        'cart.html',
        cart_items=cart_items,
        total_amount=total,
        cart_count=cart_count
    )


@cart_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add product to cart (AJAX)."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giris yapin'})

    data = request.get_json()
    product_id = data.get('product_id')

    success, cart_count, message = cart_service.add_to_cart(
        session['user_id'],
        product_id
    )

    if success:
        return jsonify({'status': 'success', 'cart_count': cart_count})

    return jsonify({'status': 'error', 'message': message})


@cart_bp.route('/update_cart', methods=['POST'])
def update_cart():
    """Update cart item quantity (AJAX)."""
    if 'user_id' not in session:
        return jsonify({'status': 'error'})

    data = request.get_json()
    product_id = data.get('product_id')
    action = data.get('action')  # 'increase' or 'decrease'

    success, cart_count, message = cart_service.update_cart_item(
        session['user_id'],
        product_id,
        action
    )

    if success:
        return jsonify({'status': 'success', 'cart_count': cart_count})

    return jsonify({'status': 'error', 'message': message})


@cart_bp.route('/remove_cart_item', methods=['POST'])
def remove_cart_item():
    """Remove item from cart (AJAX)."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giris yapin'})

    product_id = request.form.get("product_id") or request.json.get("product_id")

    success, message = cart_service.remove_item(session['user_id'], product_id)

    if success:
        return jsonify({'status': 'success'})

    return jsonify({'status': 'error', 'message': message})


@cart_bp.route('/clear_cart', methods=['POST'])
def clear_cart():
    """Clear all items from cart (AJAX)."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giris yapin'})

    success, message = cart_service.clear_cart(session['user_id'])

    if success:
        return jsonify({'status': 'success'})

    return jsonify({'status': 'error', 'message': message})
