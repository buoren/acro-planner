# Acro Planner Mobile App (React Native)

A cross-platform mobile application built with React Native and Expo that serves as a non-admin client for the Acro Planner platform.

## Features

- Cross-platform support (iOS, Android, Web)
- User authentication (login/register)
- Real-time API health monitoring
- Convention browsing
- Workshop scheduling
- Material-inspired UI design
- Secure token storage with Expo SecureStore
- TypeScript for type safety

## Tech Stack

- **React Native** with Expo SDK 54
- **TypeScript** for type safety
- **React Navigation** for routing
- **Axios** for API calls
- **Expo SecureStore** for secure authentication token storage
- **React Context API** for state management

## Project Structure

```
acro-planner-mobile/
├── src/
│   ├── config/           # Environment configuration
│   ├── contexts/         # React contexts (Auth)
│   ├── navigation/       # Navigation structure and types
│   ├── screens/         
│   │   ├── auth/        # Login and Register screens
│   │   └── main/        # Main app screens
│   └── services/        # API service layer
├── .env                 # Environment variables
├── App.tsx              # Root component
└── package.json         # Dependencies
```

## Getting Started

### Prerequisites

- Node.js 20.19+ (recommended)
- npm or yarn
- Expo CLI
- iOS Simulator (for Mac) or Android Emulator

### Installation

```bash
# Install dependencies
npm install

# Install iOS dependencies (Mac only)
npx pod-install
```

### Running the App

```bash
# Start for web
npm run web

# Start for iOS (Mac only)
npm run ios

# Start for Android
npm run android

# Start Expo development server
npx expo start
```

The app will connect to the production backend at:
`https://acro-planner-backend-733697808355.us-central1.run.app`

### Environment Configuration

The app uses different environment configurations for development and production:

- Development: Points to production API (can be changed in `src/config/env.ts`)
- Production: Points to production API

## API Integration

The app connects to the existing FastAPI backend service and includes:

- Health check monitoring
- User authentication (login/register)
- Convention listing
- Workshop browsing
- Event slot management

All API calls are centralized in `src/services/api.ts` with:
- Automatic token attachment
- Error handling
- Request/response interceptors
- Secure token storage

## Authentication Flow

1. User enters credentials on login screen
2. API validates and returns JWT token
3. Token stored securely using Expo SecureStore
4. Token automatically attached to subsequent requests
5. 401 responses trigger automatic logout

## Available Screens

- **Login Screen**: User authentication
- **Register Screen**: New user registration
- **Home Screen**: Dashboard with health status and quick actions
- **Conventions**: Browse available conventions (placeholder)
- **Workshops**: View and register for workshops (placeholder)
- **Schedule**: Personal schedule view (placeholder)
- **Profile**: User profile management (placeholder)

## Development Notes

### Testing with Production Backend

The app is configured to connect directly to the production backend. Ensure:
1. CORS is properly configured on the backend
2. API endpoints are accessible
3. Authentication tokens are valid

### Building for Production

```bash
# Build for iOS
expo build:ios

# Build for Android
expo build:android

# Build for web
expo build:web
```

## Deployment

### Web Deployment
The web version can be deployed to any static hosting service:

```bash
# Build for web
npx expo export:web

# Deploy to hosting service
# (Files will be in web-build directory)
```

### Mobile Deployment
- iOS: Submit to App Store via Xcode or EAS Build
- Android: Submit to Play Store via EAS Build

## Troubleshooting

### Port conflicts
If port 8081 is in use, specify a different port:
```bash
npx expo start --port 19006
```

### Package version mismatches
If you see warnings about package versions:
```bash
npx expo doctor
npx expo install --fix
```

### API Connection Issues
- Verify backend is running and accessible
- Check CORS configuration
- Ensure correct API URL in environment config

## Future Enhancements

- Push notifications
- Offline support with data caching
- Advanced workshop filtering
- Social features
- Real-time updates via WebSocket
- Biometric authentication
- Dark mode support