from flask import Blueprint, render_template, request, jsonify, session, redirect

from services.order_service import OrderService
from services.cart_service import CartService

orders_bp = Blueprint('orders', __name__)
order_service = OrderService()
cart_service = CartService()


@orders_bp.route('/checkout', methods=['POST'])
def checkout():
    """Create order from cart (AJAX)."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giris yapin'})

    success, order_id, message = order_service.create_order(session['user_id'])

    if success:
        return jsonify({'status': 'success', 'order_id': order_id})

    return jsonify({'status': 'error', 'message': message})


@orders_bp.route('/order_success/<int:order_id>')
def order_success(order_id):
    """Order success page."""
    if 'user_id' not in session:
        return redirect('/login')

    order, items = order_service.get_order_details(order_id, session['user_id'])

    if not order:
        return "Siparis bulunamadi", 404

    cart_count = cart_service.get_cart_count(session['user_id'])

    return render_template(
        'order_success.html',
        order=order,
        items=items,
        cart_count=cart_count
    )
