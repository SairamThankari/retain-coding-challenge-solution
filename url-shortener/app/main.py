from flask import Flask, jsonify, request, redirect, url_for
from .models import url_store
from .utils import (
    validate_url, 
    generate_unique_short_code, 
    sanitize_url, 
    format_short_url
)

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """
    Shorten a URL endpoint
    
    Expected JSON payload:
    {
        "url": "https://www.example.com/very/long/url"
    }
    
    Returns:
    {
        "short_code": "abc123",
        "short_url": "http://localhost:5000/abc123"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "URL is required"}), 400
        
        # Sanitize and validate URL
        original_url = sanitize_url(data['url'])
        is_valid, error_message = validate_url(original_url)
        
        if not is_valid:
            return jsonify({"error": error_message}), 400
        
        # Generate unique short code
        try:
            short_code = generate_unique_short_code(url_store)
        except RuntimeError as e:
            return jsonify({"error": "Unable to generate short code. Please try again."}), 500
        
        # Create URL mapping
        try:
            url_data = url_store.create_url_mapping(short_code, original_url)
        except ValueError as e:
            return jsonify({"error": str(e)}), 409
        
        # Return response
        short_url = format_short_url(short_code)
        
        return jsonify({
            "short_code": short_code,
            "short_url": short_url
        }), 201
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """
    Redirect to original URL
    
    Args:
        short_code: The short code to redirect
        
    Returns:
        Redirect to original URL or 404 if not found
    """
    try:
        # Get URL mapping
        url_data = url_store.get_url_mapping(short_code)
        
        if not url_data:
            return jsonify({"error": "Short code not found"}), 404
        
        # Increment click count
        url_store.increment_clicks(short_code)
        
        # Redirect to original URL
        return redirect(url_data['original_url'], code=302)
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/stats/<short_code>')
def get_url_stats(short_code):
    """
    Get analytics for a URL
    
    Args:
        short_code: The short code to get stats for
        
    Returns:
    {
        "url": "https://www.example.com/very/long/url",
        "clicks": 5,
        "created_at": "2024-01-01T10:00:00"
    }
    """
    try:
        # Get stats
        stats = url_store.get_stats(short_code)
        
        if not stats:
            return jsonify({"error": "Short code not found"}), 404
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)