# URL Shortener Service

A simple URL shortening service similar to bit.ly or tinyurl, built with Flask.

## Features

- **URL Shortening**: Convert long URLs to short 6-character codes
- **URL Redirection**: Redirect short codes to original URLs
- **Click Tracking**: Track and display click statistics for each shortened URL
- **Analytics**: Get detailed statistics including click count and creation timestamp
- **Input Validation**: Comprehensive URL validation and error handling
- **Thread Safety**: Handles concurrent requests properly
- **RESTful API**: Clean, RESTful API design with proper HTTP status codes

## Setup

### Prerequisites
- Python 3.8+

### Installation
```bash
# Clone/download this repository
cd url-shortener

# Install dependencies
pip install -r requirements.txt

# Start the application
python -m flask --app app.main run

# The API will be available at http://localhost:5000
```

### Running Tests
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_basic.py
```

## API Endpoints

### Health Check
```http
GET /
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "URL Shortener API"
}
```

### Shorten URL
```http
POST /api/shorten
Content-Type: application/json

{
  "url": "https://www.example.com/very/long/url"
}
```

**Response:**
```json
{
  "short_code": "abc123",
  "short_url": "http://localhost:5000/abc123"
}
```

### Redirect to Original URL
```http
GET /{short_code}
```

**Response:** 302 Redirect to the original URL

### Get URL Statistics
```http
GET /api/stats/{short_code}
```

**Response:**
```json
{
  "url": "https://www.example.com/very/long/url",
  "clicks": 5,
  "created_at": "2024-01-01T10:00:00"
}
```

## Example Usage

### Using curl

#### Shorten a URL
```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/very/long/url"}'
```

#### Use the short URL (redirects)
```bash
curl -L http://localhost:5000/abc123
```

#### Get analytics
```bash
curl http://localhost:5000/api/stats/abc123
```

### Using Python requests

```python
import requests

# Shorten a URL
response = requests.post('http://localhost:5000/api/shorten', 
                        json={'url': 'https://www.example.com'})
data = response.json()
short_code = data['short_code']

# Get stats
stats = requests.get(f'http://localhost:5000/api/stats/{short_code}').json()
print(f"Clicks: {stats['clicks']}")
```

## Implementation Details

### Architecture

The service is built with a clean, modular architecture:

- **`app/main.py`**: Flask application with route handlers
- **`app/models.py`**: Data models and in-memory storage
- **`app/utils.py`**: Utility functions for URL validation and code generation

### Data Storage

- **In-memory storage**: Uses a thread-safe dictionary for URL mappings
- **Thread safety**: All operations are protected with locks to handle concurrent requests
- **Persistence**: Data is lost on application restart (can be extended with database storage)

### URL Validation

The service validates URLs using the following criteria:
- Must start with `http://` or `https://`
- Must have a valid domain name
- Must be properly formatted

### Short Code Generation

- **Length**: 6 characters (configurable)
- **Characters**: Alphanumeric (A-Z, a-z, 0-9)
- **Uniqueness**: Automatically generates unique codes
- **Collision handling**: Retries up to 10 times to find a unique code

### Error Handling

The service provides comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Short code doesn't exist
- **405 Method Not Allowed**: Invalid HTTP method
- **500 Internal Server Error**: Server-side errors

## Testing

The service includes comprehensive tests covering:

- ✅ URL shortening functionality
- ✅ URL redirection
- ✅ Analytics and click tracking
- ✅ Input validation
- ✅ Error handling
- ✅ Concurrent request handling
- ✅ Short code uniqueness
- ✅ Various URL formats

Run tests with:
```bash
pytest -v
```

## Technical Requirements Met

- ✅ **URL Validation**: Comprehensive URL format validation
- ✅ **6-character Short Codes**: Alphanumeric codes of exactly 6 characters
- ✅ **Concurrent Request Handling**: Thread-safe operations with proper locking
- ✅ **Error Handling**: Proper HTTP status codes and error messages
- ✅ **5+ Tests**: 16 comprehensive tests covering all functionality

## API Design

### RESTful Principles
- Uses appropriate HTTP methods (GET, POST)
- Returns proper HTTP status codes
- Provides consistent JSON responses
- Follows REST conventions

### Response Format
All responses are in JSON format with consistent structure:
- Success responses include relevant data
- Error responses include error messages
- Status codes indicate the result

## Future Enhancements

With more time, the following improvements could be made:

1. **Database Storage**: Replace in-memory storage with PostgreSQL/MySQL
2. **User Authentication**: Add user accounts and private URLs
3. **Custom Short Codes**: Allow users to specify custom codes
4. **Rate Limiting**: Implement API rate limiting
5. **URL Expiration**: Add expiration dates for URLs
6. **Advanced Analytics**: Track referrers, user agents, geographic data
7. **Web Interface**: Add a simple web UI for URL management
8. **API Documentation**: Add Swagger/OpenAPI documentation

## Performance Considerations

- **Memory Usage**: In-memory storage is fast but limited by available RAM
- **Concurrency**: Thread-safe operations handle multiple simultaneous requests
- **Scalability**: Can be extended with database storage and load balancing
- **Caching**: Could add Redis for improved performance

## Security Considerations

- **Input Validation**: All URLs are validated before processing
- **No SQL Injection**: Uses in-memory storage (no SQL queries)
- **Error Information**: Limited error details to prevent information leakage
- **URL Sanitization**: URLs are sanitized before processing

## License

This project is part of a coding challenge and is provided as-is for demonstration purposes.