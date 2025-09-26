# Frontend - React Chat Interface

## Overview

This frontend is a React-based single-page application (SPA) that provides a unified chat interface for all user types in the BRS (Banner Registration System) prototype. The interface dynamically adapts based on the user's JWT token and role.

## Technology Stack

- **React**: JavaScript library for building user interfaces
- **Vite**: Modern build tool and development server
- **Docker**: Containerized deployment

## Vite Explained (For Backend Developers)

### What is Vite?
Vite is a modern frontend build tool that serves two main purposes:

1. **Development Server**: Provides a fast local development environment with features like:
   - Hot Module Replacement (HMR) - code changes appear instantly in browser
   - Built-in proxy capabilities for API calls
   - Fast startup times

2. **Build Tool**: Bundles your application for production deployment

### Key Concepts

#### Development vs Production Mode

**Development Mode** (what we use now):
```bash
npm run dev  # Starts Vite dev server on port 5173
```
- Runs a live server that rebuilds on file changes
- Includes proxy configuration to forward API calls to backend
- Provides debugging tools and better error messages

**Production Mode** (what we had before):
```bash
npm run build  # Creates static files in /dist folder
serve -s dist   # Serves static files with a simple HTTP server
```
- Creates optimized, minified files for deployment
- No proxy capabilities - all API URLs must be absolute
- Faster loading but no development features

#### The Proxy Problem We Solved

**The Issue**:
When the frontend was built as a static site, the browser tried to make API calls directly to `http://localhost:8000` from the user's machine. This failed because:
- The backend container is only accessible within the Docker network
- Static sites can't proxy requests to other services

**The Solution**:
We switched to Vite dev mode which includes a proxy configuration:

```javascript
// vite.config.js
export default defineConfig({
    server: {
        port: 5173,
        host: '0.0.0.0',
        proxy: {
            '/api': {
                target: 'http://backend:8000',  // Forward to backend container
                changeOrigin: true,
                secure: false,
            }
        }
    },
});
```

**How it works**:
1. Browser makes request to `http://localhost:5173/api/v1/auth/login`
2. Vite intercepts the `/api` request
3. Vite forwards it to `http://backend:8000/api/v1/auth/login` within Docker network
4. Backend processes the request and returns response
5. Vite forwards the response back to the browser

## File Structure

```
frontend/
├── Dockerfile              # Container configuration
├── package.json             # Dependencies and scripts
├── vite.config.js          # Vite configuration (proxy setup)
├── index.html              # Main HTML template
└── src/
    ├── main.jsx            # React app entry point
    ├── App.jsx             # Main app component
    ├── api.js              # API utility functions
    ├── hooks/
    │   ├── useAuth.js      # Authentication hook
    │   └── useChat.js      # Chat functionality hook
    └── components/
        ├── StudentView.jsx
        ├── AdvisorView.jsx
        ├── AdminView.jsx
        └── [other components]
```

## Authentication Flow

### JWT Token Handling
The frontend uses JWT tokens for authentication:

1. **Login**: User submits credentials to `/api/v1/auth/login`
2. **Token Storage**: JWT token stored in browser localStorage
3. **Token Decoding**: Simple JWT decoding to extract user info:
   ```javascript
   const payload = JSON.parse(atob(token.split('.')[1]));
   ```
4. **Role-Based UI**: Interface adapts based on user role from token

### API Calls
All API calls use the `useAuth` hook pattern:

```javascript
// useAuth.js - Authentication hook
const API_BASE = '';  // Empty = use proxy

const login = async (username, password) => {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    // Handle response...
};
```

## CORS and API Communication

### How Frontend-Backend Communication Works

The frontend and backend run in separate Docker containers and communicate via HTTP requests. This requires proper CORS (Cross-Origin Resource Sharing) configuration.

#### Development Setup (Current)
- **Frontend**: Vite dev server on `http://localhost:5173`
- **Backend**: FastAPI server on `http://localhost:8000`
- **Communication**: Vite proxy forwards `/api/*` requests to backend

#### CORS Configuration Flow
1. **Browser Request**: `http://localhost:5173/api/v1/auth/login`
2. **Vite Proxy**: Forwards to `http://backend:8000/api/v1/auth/login` (Docker network)
3. **Backend CORS**: Allows `http://localhost:5173` in `ALLOWED_ORIGINS`
4. **Response**: Backend returns data through proxy to browser

#### Why We Need CORS
Without CORS configuration, browsers block requests between different origins (different ports count as different origins). The backend must explicitly allow the frontend's origin.

**Backend CORS Settings** (`backend/brs_backend/core/config.py`):
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Production frontend
    "http://localhost:5173"   # Development frontend (Vite)
]
```

### Troubleshooting Network Issues

**"Network Error" during login**:
1. Check if backend allows frontend origin in CORS settings
2. Verify proxy configuration in `vite.config.js`
3. Ensure containers can communicate in Docker network
4. Check browser Network tab for failed requests

**Connection Status Issues**:
- "Disconnected" usually means the chat session endpoint failed
- Check if all API endpoints have proper CORS preflight support
- Verify JWT token is being sent in Authorization headers

## Docker Configuration

### Current Setup (Development Mode)
```dockerfile
FROM node:18-alpine
WORKDIR /app

# Install dependencies
COPY package.json .
COPY vite.config.js .
COPY index.html .
COPY src ./src
RUN npm install

# Expose port 5173 for Vite dev server
EXPOSE 5173

# Run Vite dev server with proxy support
CMD ["npm", "run", "dev"]
```

### Port Mapping
- Container Port: 5173 (Vite dev server)
- Host Port: 5173
- Access URL: `http://localhost:5173`

## Development Workflow

### Local Development
1. Make changes to React components in `src/`
2. Vite automatically rebuilds and refreshes browser
3. API calls are proxied to backend container
4. No need to rebuild Docker container for code changes

### Adding New Features
1. Create new components in `src/components/`
2. Add API calls using the established hook pattern
3. Update routing in `App.jsx` if needed
4. Test authentication flow with different user roles

## Troubleshooting

### Common Issues

**"Network Error" during login**:
- Check if backend container is running: `docker-compose ps`
- Verify proxy configuration in `vite.config.js`
- Ensure API_BASE is empty string (uses proxy)
- Check browser network tab for failed requests

**Container won't start**:
- Check port conflicts: `lsof -i :5173`
- Verify Docker container has correct port mapping
- Check frontend logs: `docker-compose logs frontend`

**Code changes not appearing**:
- Ensure you're running in dev mode (not production build)
- Check if files are being watched by Vite
- Try hard refresh in browser (Cmd+Shift+R)

### Debug Commands
```bash
# Check container status
docker-compose ps

# View frontend logs
docker-compose logs frontend --tail=20

# Restart frontend only
docker-compose restart frontend

# Rebuild frontend container
docker-compose build frontend --no-cache

# Test backend connectivity from frontend container
docker-compose exec frontend sh -c "wget -O- http://backend:8000/health"
```

## User Roles and Demo Accounts

The system supports different user types with demo accounts:

- **Students**: `sarah.ahmed` / `password123`
- **Advisors**: `marcus.thompson` / `password123`
- **Admins**: `emily.chen` / `password123`
- **Department Heads**: Various accounts available

Each role sees a different interface based on their JWT token claims.

## Next Steps for Production

When moving to production, consider:

1. **Build Process**: Switch back to production build for better performance
2. **Environment Variables**: Use environment-specific API URLs
3. **Security**: Implement proper token refresh mechanisms
4. **HTTPS**: Configure SSL certificates for secure communication
5. **CDN**: Serve static assets from a content delivery network

## API Integration

The frontend expects these backend endpoints:
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/chat/send` - Send chat messages
- `GET /api/v1/chat/history` - Get chat history
- Additional endpoints based on user role

All requests include the JWT token in the Authorization header for authenticated endpoints.
