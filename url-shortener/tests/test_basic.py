import pytest
import json
import threading
import time
from app.main import app
from app.models import url_store

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear the URL store before each test
        url_store._urls.clear()
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'URL Shortener API'

def test_api_health(client):
    """Test API health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['message'] == 'URL Shortener API is running'

def test_shorten_url_success(client):
    """Test successful URL shortening"""
    response = client.post('/api/shorten',
                          json={'url': 'https://www.example.com/very/long/url'},
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data
    assert len(data['short_code']) == 6
    assert data['short_url'] == f"http://localhost:5000/{data['short_code']}"

def test_shorten_url_missing_content_type(client):
    """Test URL shortening without proper content type"""
    response = client.post('/api/shorten',
                          data='{"url": "https://www.example.com"}')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Content-Type must be application/json'

def test_shorten_url_missing_url(client):
    """Test URL shortening without URL in payload"""
    response = client.post('/api/shorten',
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'URL is required'

def test_shorten_url_invalid_url(client):
    """Test URL shortening with invalid URL"""
    response = client.post('/api/shorten',
                          json={'url': 'not-a-url'},
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'URL must start with http:// or https://' in data['error']

def test_shorten_url_empty_url(client):
    """Test URL shortening with empty URL"""
    response = client.post('/api/shorten',
                          json={'url': ''},
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'URL cannot be empty'

def test_redirect_success(client):
    """Test successful URL redirection"""
    # First create a short URL
    create_response = client.post('/api/shorten',
                                 json={'url': 'https://www.google.com'},
                                 content_type='application/json')
    short_code = create_response.get_json()['short_code']
    
    # Test redirect
    response = client.get(f'/{short_code}')
    assert response.status_code == 302
    assert response.location == 'https://www.google.com'

def test_redirect_not_found(client):
    """Test redirect with non-existent short code"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Short code not found'

def test_get_stats_success(client):
    """Test getting URL statistics"""
    # First create a short URL
    create_response = client.post('/api/shorten',
                                 json={'url': 'https://www.github.com'},
                                 content_type='application/json')
    short_code = create_response.get_json()['short_code']
    
    # Get stats before any clicks
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['url'] == 'https://www.github.com'
    assert data['clicks'] == 0
    assert 'created_at' in data
    
    # Click the URL
    client.get(f'/{short_code}')
    
    # Get stats after click
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['clicks'] == 1

def test_get_stats_not_found(client):
    """Test getting stats for non-existent short code"""
    response = client.get('/api/stats/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Short code not found'

def test_multiple_clicks_tracking(client):
    """Test that multiple clicks are properly tracked"""
    # Create a short URL
    create_response = client.post('/api/shorten',
                                 json={'url': 'https://www.stackoverflow.com'},
                                 content_type='application/json')
    short_code = create_response.get_json()['short_code']
    
    # Click multiple times
    for _ in range(5):
        client.get(f'/{short_code}')
    
    # Check stats
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['clicks'] == 5

def test_concurrent_requests(client):
    """Test handling of concurrent requests using direct store access"""
    # Create a short URL
    create_response = client.post('/api/shorten',
                                 json={'url': 'https://www.python.org'},
                                 content_type='application/json')
    short_code = create_response.get_json()['short_code']
    
    # Test thread safety by directly accessing the store
    def increment_clicks():
        url_store.increment_clicks(short_code)
    
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=increment_clicks)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check final stats
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['clicks'] == 10

def test_url_validation_various_formats(client):
    """Test URL validation with various formats"""
    valid_urls = [
        'https://www.example.com',
        'http://example.com',
        'https://subdomain.example.com/path?param=value',
        'https://example.com:8080/path'
    ]
    
    invalid_urls = [
        'not-a-url',
        'ftp://example.com',
        'example.com',
        '',
        'https://',
        'http://'
    ]
    
    # Test valid URLs
    for url in valid_urls:
        response = client.post('/api/shorten',
                              json={'url': url},
                              content_type='application/json')
        assert response.status_code == 201
    
    # Test invalid URLs
    for url in invalid_urls:
        response = client.post('/api/shorten',
                              json={'url': url},
                              content_type='application/json')
        assert response.status_code == 400

def test_short_code_uniqueness(client):
    """Test that generated short codes are unique"""
    urls = [
        'https://www.example1.com',
        'https://www.example2.com',
        'https://www.example3.com',
        'https://www.example4.com',
        'https://www.example5.com'
    ]
    
    short_codes = set()
    
    for url in urls:
        response = client.post('/api/shorten',
                              json={'url': url},
                              content_type='application/json')
        assert response.status_code == 201
        short_code = response.get_json()['short_code']
        assert short_code not in short_codes
        short_codes.add(short_code)

def test_error_handlers(client):
    """Test error handlers"""
    # Test 404
    response = client.get('/nonexistent/endpoint')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Resource not found'
    
    # Test 405 (Method Not Allowed)
    response = client.post('/')
    assert response.status_code == 405
    data = response.get_json()
    assert data['error'] == 'Method not allowed'