import os
from college_rag_app import create_app

# Create the application instance using the factory
app = create_app()

if __name__ == "__main__":
    # Get debug mode from environment variables
    debug_mode = os.getenv("FLASK_DEBUG", "False")
    
    # Run the Flask app
    # For development only. Use Gunicorn in production.
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)