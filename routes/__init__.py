from .auth import auth_bp
from .products import products_bp
from .cart import cart_bp
from .orders import orders_bp
from .voice import voice_bp

__all__ = ['auth_bp', 'products_bp', 'cart_bp', 'orders_bp', 'voice_bp']


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(voice_bp)
