# PII Backend

FastAPI backend for PII encryption system that provides REST API endpoints for secure PII operations through AWS Lambda integration.

## Features

- **Three-tier PII classification system** (Level 1, 2, 3)
- **AWS Lambda integration** for secure PII operations
- **API key authentication** for secure access
- **CORS middleware** for frontend integration
- **Comprehensive request/response validation** with Pydantic
- **Environment-based configuration**
- **Health check endpoints**
- **Audit trail support**

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment with uv
uv sync

# Copy environment configuration
cp .env.example .env

# Edit .env with your AWS configuration
```

### 2. Configure AWS

Ensure you have AWS credentials configured:

```bash
# Using AWS CLI (recommended)
aws configure

# This creates ~/.aws/credentials and ~/.aws/config files
# No need to set environment variables manually
```

### 3. Run Development Server

```bash
# Start the FastAPI development server
uv run uvicorn src.pii_backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check (includes Lambda connectivity)

### User Management

- `POST /users` - Create a new user with PII data
- `GET /users/{user_id}` - Get user by ID
- `GET /users` - List users (paginated)
- `DELETE /users/{user_id}` - Delete user

### Audit

- `GET /users/{user_id}/audit` - Get audit trail for specific user
- `GET /audit` - Get system-wide audit trail

## Authentication

All endpoints (except root and health) require API key authentication:

```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/users
```

Set your API key in the `.env` file:

```
PII_API_KEY=your-production-api-key
```

## Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/pii_backend tests/

# Run specific test
uv run pytest tests/test_main.py::test_root_endpoint -v
```

## Configuration

The backend uses environment variables for configuration. Key settings:

### Required Settings

- `PII_API_KEY` - API key for authentication
- `PII_LAMBDA_FUNCTION_NAME` - AWS Lambda function name
- `AWS_REGION` - AWS region for Lambda calls

### Optional Settings

- `PII_ENVIRONMENT` - Environment (development/production)
- `PII_DEBUG` - Enable debug mode
- `PII_ALLOWED_ORIGINS` - CORS allowed origins (JSON array)
- `PII_LAMBDA_TIMEOUT` - Lambda timeout (seconds)
- `PII_LAMBDA_RETRY_ATTEMPTS` - Number of retry attempts
- `PII_LOG_LEVEL` - Logging level

## Project Structure

```
backend/
├── src/pii_backend/
│   ├── main.py           # FastAPI application and routes
│   ├── models.py         # Pydantic models for validation
│   ├── lambda_client.py  # AWS Lambda integration
│   ├── config.py         # Configuration management
│   └── security.py       # Authentication and security
├── tests/
│   ├── __init__.py
│   └── test_main.py      # API endpoint tests
├── deploy/
│   ├── terraform/        # AWS App Runner deployment
│   ├── push-to-ecr.sh   # ECR build and push script
│   ├── deploy.sh        # Terraform deployment script
│   └── README.md        # Deployment guide
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Local container testing
├── apprunner.yaml      # App Runner configuration
├── .env                # Environment configuration
├── .env.example        # Environment template
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## Development

### Adding New Endpoints

1. Define Pydantic models in `models.py`
2. Add the endpoint to `main.py`
3. Add corresponding Lambda client method in `lambda_client.py`
4. Write tests in `tests/`

### Error Handling

The API provides structured error responses:

```json
{
  "success": false,
  "error": "Validation failed",
  "detail": "Email field is required",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Production Deployment

### AWS App Runner (Recommended for Prototypes)

The backend is containerized and ready for deployment to AWS App Runner, a fully managed service for containerized web applications.

**Quick Deployment:**

1. **Build and push to ECR:**
   ```bash
   cd deploy
   ./push-to-ecr.sh us-east-1 pii-backend latest
   ```

2. **Configure and deploy:**
   ```bash
   cp deploy/terraform/terraform.tfvars.example deploy/terraform/terraform.tfvars
   # Edit terraform.tfvars with your settings
   
   ./deploy.sh apply
   ```

See [deploy/README.md](deploy/README.md) for complete deployment guide.

**App Runner Benefits:**
- Fully managed (no servers)
- Auto-scaling (0 to hundreds of instances)
- Built-in HTTPS and load balancing
- Cost-effective (pay per use)
- Zero-downtime deployments

### Manual Deployment

For other deployment targets:

1. Set production environment variables
2. Use a production WSGI server:

```bash
uv run gunicorn src.pii_backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

3. Configure reverse proxy (nginx/ALB)
4. Set up proper logging and monitoring

## Security Considerations

- **No PII encryption in backend** - All encryption is handled by Lambda
- **API keys stored securely** - Use environment variables
- **CORS configured** for specific origins only
- **Input validation** with Pydantic models
- **Error messages** do not expose sensitive information