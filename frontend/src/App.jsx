import React from 'react';
import { useAuth } from './hooks/useAuth.js';
import LoginForm from './components/LoginForm.jsx';
import UnifiedChatInterface from './components/UnifiedChatInterface.jsx';

export default function App() {
    const { user, token, isAuthenticated, login, logout } = useAuth();

    if (!isAuthenticated) {
        return <LoginForm onLogin={login} />;
    }

    return (
        <UnifiedChatInterface
            user={user}
            token={token}
            onLogout={logout}
        />
    );
}
