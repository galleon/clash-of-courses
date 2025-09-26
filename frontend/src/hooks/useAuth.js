import { useState, useEffect } from 'react';

// Use relative path - Vite proxy will forward to backend
const API_BASE = '';

export function useAuth() {
    const [token, setToken] = useState(() => localStorage.getItem('auth_token'));
    const [user, setUser] = useState(null);

    // Decode JWT to get user info (simple implementation)
    const decodeToken = (token) => {
        if (!token) return null;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload;
        } catch (e) {
            console.error('Failed to decode token:', e);
            return null;
        }
    };

    useEffect(() => {
        if (token) {
            const decodedUser = decodeToken(token);
            setUser(decodedUser);
        } else {
            setUser(null);
        }
    }, [token]);

    const login = async (username, password) => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                setToken(data.access_token);
                localStorage.setItem('auth_token', data.access_token);
                return { success: true };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('auth_token');
    };

    return {
        token,
        user,
        isAuthenticated: !!token,
        login,
        logout,
    };
}
