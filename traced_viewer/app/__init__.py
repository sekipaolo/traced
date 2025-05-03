"""
Flask application factory for traced viewer.
"""

import os
import logging
from flask import Flask


def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config: Test configuration to override default config
        
    Returns:
        Configured Flask application
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE_PATH=os.environ.get('TRACED_DB_PATH', '/data/traces.db')
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Register blueprints
    from app.views import bp as views_bp
    app.register_blueprint(views_bp)

    # Create a simple route to ensure the app is working
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {'status': 'ok'}

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)