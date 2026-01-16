"""
EchoMarket - Voice-Enabled E-Commerce Application

This is the main application entry point.
Architecture: Layered Architecture (Presentation -> Service -> Repository -> Database)
"""

from flask import Flask
from config.settings import get_config
from routes import register_blueprints


def create_app():
    """Application factory pattern."""
    # Initialize Flask app
    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.secret_key = config.SECRET_KEY

    # Register all blueprints (routes)
    register_blueprints(app)

    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
