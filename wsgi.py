"""
WSGI entry point for production deployment on Render.com

This file serves as the production WSGI application entry point.
It imports the Flask app from server.py and configures it for production use.
"""

from server import app

# The application object that WSGI servers will use
application = app

if __name__ == "__main__":
    # This block won't be executed when run via WSGI
    # but can be used for local testing of the WSGI setup
    app.run(host="0.0.0.0", port=5000)