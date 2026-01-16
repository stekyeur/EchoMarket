from flask import Blueprint, render_template, request, jsonify, session, redirect

from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication."""
    if request.method == 'POST':
        data = request.get_json()

        success, user_data, message = auth_service.login(
            data.get('email', ''),
            data.get('password', '')
        )

        if success:
            session['user_id'] = user_data['id']
            session['name'] = user_data['name']
            return jsonify({'status': 'success', 'message': message})

        return jsonify({'status': 'error', 'message': message})

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and user creation."""
    if request.method == 'POST':
        data = request.get_json()

        success, message = auth_service.register(
            full_name=data.get('full_name', ''),
            email=data.get('email', ''),
            password=data.get('password', ''),
            phone=data.get('phone'),
            street=data.get('street'),
            city=data.get('city'),
            zipcode=data.get('zipcode')
        )

        status = 'success' if success else 'error'
        return jsonify({'status': status, 'message': message})

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect('/')


@auth_bp.route('/account', methods=['GET', 'POST'])
def account():
    """Account page and profile update."""
    if 'user_id' not in session:
        return redirect('/login')

    from services.cart_service import CartService
    from services.order_service import OrderService

    cart_service = CartService()
    order_service = OrderService()

    msg = None
    msg_type = "success"

    if request.method == 'POST':
        success, message = auth_service.update_profile(
            user_id=session['user_id'],
            name=request.form.get('name', ''),
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            street=request.form.get('street'),
            city=request.form.get('city'),
            zipcode=request.form.get('zipcode'),
            new_password=request.form.get('new_password')
        )
        msg = message
        msg_type = "success" if success else "error"

    # Get user data
    user_info, address_info = auth_service.get_user_profile(session['user_id'])
    orders = order_service.get_user_orders(session['user_id'])
    cart_count = cart_service.get_cart_count(session['user_id'])

    return render_template(
        'account.html',
        user=user_info,
        address=address_info if address_info else ("", "", ""),
        orders=orders,
        msg=msg,
        msg_type=msg_type,
        cart_count=cart_count
    )
