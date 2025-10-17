# Acro Planner Clients

This directory contains all frontend applications for the Acro Planner project.

## Flutter App (`acro_planner_app`)

Cross-platform mobile app built with Flutter that connects to the FastAPI backend.

### Features

- **API Integration**: Configured HTTP client with environment-based URLs
- **State Management**: Provider pattern for scalable state management
- **Modern UI**: Material Design 3 with light/dark theme support
- **Health Check**: Real-time connection status to backend API
- **Environment Configuration**: Development and production configurations

### Setup

1. **Install Flutter**: Follow [Flutter installation guide](https://docs.flutter.dev/get-started/install)

2. **Install dependencies**:
   ```bash
   cd acro_planner_app
   flutter pub get
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

4. **Run the app**:
   ```bash
   # For iOS simulator
   flutter run -d ios
   
   # For Android emulator  
   flutter run -d android
   
   # For web
   flutter run -d web
   ```

### Project Structure

```
acro_planner_app/
├── lib/
│   ├── main.dart              # App entry point
│   └── services/
│       └── api_service.dart   # HTTP client service
├── assets/                    # Images, fonts, etc.
├── .env                       # Environment variables
├── .env.example              # Environment template
└── pubspec.yaml              # Dependencies
```

### Dependencies

- **http**: HTTP client for API communication
- **provider**: State management solution
- **flutter_dotenv**: Environment variable management

### API Integration

The app automatically connects to your FastAPI backend:

- **Development**: `http://localhost:8000`
- **Production**: Configure in `.env` file

### Development Notes

- The app includes a health check that tests connectivity to the backend
- Environment variables are loaded from `.env` file
- Provider pattern is set up for easy state management expansion
- Material Design 3 theming with automatic dark mode support

### Next Steps

- Add authentication screens
- Implement session planning features
- Add progress tracking
- Create user profiles
- Add offline support