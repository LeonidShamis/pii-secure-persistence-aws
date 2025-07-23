# PII Encryption System Frontend

React-based frontend for the PII Encryption System with visual security indicators and three-tier encryption workflow.

## Features

- **Visual PII Level Indicators**: Color-coded fields (Green/Orange/Red) showing encryption levels
- **Security Badges**: Clear labeling of PII sensitivity levels with lock icons
- **Data Masking**: Level 3 sensitive data is masked by default with reveal toggle
- **Real-time Validation**: Form validation with security-focused error messages
- **Responsive Design**: Works on desktop and mobile devices
- **No Client-side Encryption**: All encryption handled server-side for security

## PII Classification System

### Level 1 - Low Sensitivity (🟢)
- **Fields**: Email, First Name, Last Name, Phone
- **Encryption**: RDS at-rest encryption only
- **Color**: Green indicators

### Level 2 - Medium Sensitivity (🟠)  
- **Fields**: Address, Date of Birth, IP Address
- **Encryption**: AWS KMS field-level encryption
- **Color**: Orange indicators

### Level 3 - High Sensitivity (🔴)
- **Fields**: SSN, Bank Account, Credit Card
- **Encryption**: Double encryption (Application + KMS)
- **Color**: Red indicators with masking

## Development Setup

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Access to deployed FastAPI backend

### Installation

```bash
# Clone repository and navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file and configure
cp .env.example .env
# Edit .env with your backend URL and API key

# Start development server
npm run dev
```

### Environment Variables

Create `.env` file with:

```bash
# Backend API configuration
VITE_API_BASE_URL=https://your-app-runner-url.awsapprunner.com
VITE_API_KEY=your-api-key-here

# Development settings
VITE_ENVIRONMENT=development
VITE_DEBUG=true
```

## Project Structure

```
src/
├── components/
│   ├── UserForm.jsx          # Data entry form with PII indicators
│   ├── UserDisplay.jsx       # Data viewing with masking
│   ├── PIIField.jsx          # Reusable field component
│   └── SecurityInfo.jsx      # System information
├── services/
│   └── api.js               # Backend API integration
├── App.jsx                  # Main application component
├── App.css                  # Security-focused styling
└── main.jsx                 # Application entry point
```

## Security Features

### Visual Security Indicators
- **Color Coding**: Green (L1), Orange (L2), Red (L3)
- **Security Badges**: Level indicators with encryption descriptions
- **Lock Icons**: Visual representation of encryption strength
- **Border Indicators**: Left border colors on focused fields

### Data Protection
- **No Local Storage**: No sensitive data cached in browser
- **HTTPS Only**: All communication encrypted in transit
- **Server-side Encryption**: No encryption keys or sensitive operations in frontend
- **Input Masking**: Level 3 fields masked by default

### User Experience
- **Progressive Disclosure**: Reveal sensitive data only on explicit action
- **Real-time Feedback**: Immediate validation and error messages
- **Audit Transparency**: View audit trail for data access
- **Responsive Design**: Consistent experience across devices

## API Integration

The frontend connects to the FastAPI backend using:
- **Axios HTTP client** with automatic authentication
- **Environment-based configuration** for different deployment stages
- **Error handling** with user-friendly messages
- **Request/response logging** for debugging

### API Endpoints Used
- `POST /users` - Create user with PII encryption
- `GET /users/{id}` - Retrieve and decrypt user data
- `GET /users/{id}/audit` - Get audit trail
- `GET /health` - System health check

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

The build process:
1. **Optimizes assets** and bundles for production
2. **Minifies CSS/JS** for faster loading
3. **Generates static files** ready for deployment
4. **Includes security headers** and configurations

## Deployment Options

### Static Hosting
- **AWS S3 + CloudFront**: Static website hosting
- **Netlify/Vercel**: Automated deployment from Git
- **GitHub Pages**: Simple static hosting

### Container Deployment
- **Docker**: Containerized with nginx
- **AWS App Runner**: Container-based deployment
- **Kubernetes**: Scalable container orchestration

## Testing

```bash
# Run component tests
npm run test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## Security Considerations

### Development
- **Environment Variables**: Never commit real API keys
- **HTTPS Required**: Backend must use HTTPS in production
- **API Key Rotation**: Regularly rotate authentication keys
- **Input Validation**: Client-side validation is for UX only

### Production
- **Content Security Policy**: Configure CSP headers
- **HTTPS Only**: Enforce HTTPS for all requests
- **Domain Restrictions**: Limit CORS to specific domains
- **Error Handling**: No sensitive data in error messages

## Troubleshooting

### Common Issues

**API Connection Errors**
- Verify `VITE_API_BASE_URL` is correct
- Check API key in `VITE_API_KEY`
- Ensure backend is running and accessible

**Visual Indicators Not Working**
- Check PII field names match classification
- Verify CSS classes are loading correctly
- Test with browser developer tools

**Form Validation Issues**
- Check required fields are filled
- Verify date formats (YYYY-MM-DD)
- Test phone/SSN format validation

### Development Mode
- Enable `VITE_DEBUG=true` for detailed logging
- Use browser network tab to monitor API calls
- Check console for component errors

## License

This project is for educational and demonstration purposes.
