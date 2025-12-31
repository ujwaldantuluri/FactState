# Google OAuth Authentication Setup

## Prerequisites
- A Google Cloud Console account
- A Google Cloud Project

## Setup Steps

### 1. Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (if not already enabled)

### 2. Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "FactState"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes: `email`, `profile`, `openid`
5. Add test users (your email addresses)

### 3. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized JavaScript origins:
   - `http://localhost:5173` (for development)
   - `http://localhost:3000` (if using different port)
   - Your production domain (when deployed)
5. Add authorized redirect URIs:
   - `http://localhost:5173` (for development)
   - Your production domain (when deployed)
6. Copy the Client ID

### 4. Update Your Application
1. Open `src/App.tsx`
2. Replace `YOUR_GOOGLE_CLIENT_ID` with your actual Client ID:

```typescript
const GOOGLE_CLIENT_ID = "your_actual_client_id_here";
```

### 5. Test the Integration
1. Start your development server: `npm run dev`
2. Go to the login page
3. Click "Continue with Google"
4. Complete the OAuth flow

## Features Implemented

### ✅ Authentication Features
- Google OAuth login with JWT token decoding
- Email/password login (mock implementation)
- Persistent session storage using localStorage
- Automatic session restoration on page reload
- Proper logout functionality

### ✅ Protected Routes
- All detection pages require authentication
- Dashboard and settings require authentication
- Automatic redirect to login for unauthenticated users
- Loading states during authentication checks

### ✅ User Experience
- Different UI for authenticated vs unauthenticated users
- User profile display with avatar and name
- Logout button in header and sidebar
- Smooth transitions and loading states

### ✅ Security Features
- JWT token validation
- Secure logout (clears localStorage)
- Protected route wrapper
- Authentication state management

## File Structure
```
src/
├── contexts/
│   └── AuthContext.tsx          # Authentication state management
├── components/
│   └── ProtectedRoute.tsx       # Route protection component
├── pages/
│   ├── Index.tsx               # Updated with auth-aware UI
│   └── Login.tsx               # Google OAuth integration
└── App.tsx                     # Google OAuth provider setup
```

## Usage

### For Users
1. Visit the homepage
2. Click "Sign In" or "Start Free Check"
3. Choose Google OAuth or email login
4. Access all detection features
5. Use "Sign Out" to logout

### For Developers
- All protected routes are wrapped with `<ProtectedRoute>`
- Use `useAuth()` hook to access authentication state
- User data is automatically persisted in localStorage
- Google OAuth tokens are decoded and stored securely

## Troubleshooting

### Common Issues
1. **"Invalid Client ID"**: Make sure you've updated the Client ID in `App.tsx`
2. **"Redirect URI mismatch"**: Add your development URL to authorized redirect URIs
3. **"OAuth consent screen not configured"**: Complete the OAuth consent screen setup
4. **"API not enabled"**: Enable the Google+ API in your Google Cloud Console

### Development Notes
- The email/password login is currently mocked
- Google OAuth is fully functional
- Session persistence works across browser sessions
- All authentication state is managed through React Context 