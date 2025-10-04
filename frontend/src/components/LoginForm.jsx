import React, { useState } from 'react';

export default function LoginForm({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        const result = await onLogin(username, password);

        if (!result.success) {
            setError(result.error);
        }

        setIsLoading(false);
    };

    const demoUsers = [
        { username: 'sarah.ahmed', password: 'password123', role: 'Student' },
        { username: 'mohammed.hassan', password: 'password123', role: 'Student' },
        { username: 'fatima.alzahra', password: 'password123', role: 'Student' },
        { username: 'ahmad.mahmoud', password: 'instructor123', role: 'Instructor' },
        { username: 'layla.khalil', password: 'instructor123', role: 'Instructor' },
        { username: 'admin', password: 'admin123', role: 'System Admin' },
    ];

    return (
        <div style={{
            display: 'flex',
            minHeight: '100vh',
            fontFamily: 'Arial, sans-serif'
        }}>
            {/* Left side - Login Form */}
            <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f8f9fa',
                padding: '2rem'
            }}>
                <div style={{
                    backgroundColor: 'white',
                    padding: '3rem',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    width: '100%',
                    maxWidth: '400px'
                }}>
                    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                        <h1 style={{ color: '#2c3e50', marginBottom: '0.5rem' }}>BRS Portal</h1>
                        <p style={{ color: '#6c757d', margin: 0 }}>Business Registration System</p>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                color: '#495057',
                                fontWeight: '500'
                            }}>
                                Username
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    border: '1px solid #ced4da',
                                    borderRadius: '4px',
                                    fontSize: '1rem',
                                    boxSizing: 'border-box'
                                }}
                                placeholder="Enter your username"
                            />
                        </div>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                color: '#495057',
                                fontWeight: '500'
                            }}>
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    border: '1px solid #ced4da',
                                    borderRadius: '4px',
                                    fontSize: '1rem',
                                    boxSizing: 'border-box'
                                }}
                                placeholder="Enter your password"
                            />
                        </div>

                        {error && (
                            <div style={{
                                backgroundColor: '#f8d7da',
                                color: '#721c24',
                                padding: '0.75rem',
                                borderRadius: '4px',
                                marginBottom: '1rem',
                                fontSize: '0.875rem'
                            }}>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                backgroundColor: isLoading ? '#6c757d' : '#007bff',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '1rem',
                                fontWeight: '500',
                                cursor: isLoading ? 'not-allowed' : 'pointer',
                                transition: 'background-color 0.2s'
                            }}
                        >
                            {isLoading ? 'Signing In...' : 'Sign In'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Right side - Demo Users */}
            <div style={{
                flex: 1,
                backgroundColor: '#2c3e50',
                color: 'white',
                padding: '3rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
            }}>
                <div>
                    <h2 style={{ marginBottom: '2rem', fontSize: '1.75rem' }}>Demo Users</h2>
                    <p style={{ marginBottom: '2rem', color: '#bdc3c7', lineHeight: '1.6' }}>
                        Use any of these demo accounts to explore the system with different role permissions:
                    </p>

                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {demoUsers.map((user, index) => (
                            <div
                                key={index}
                                style={{
                                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                    padding: '1rem',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    transition: 'background-color 0.2s'
                                }}
                                onClick={() => {
                                    setUsername(user.username);
                                    setPassword(user.password);
                                }}
                                onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.15)'}
                                onMouseOut={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
                            >
                                <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                                    {user.username}
                                </div>
                                <div style={{ fontSize: '0.875rem', color: '#bdc3c7' }}>
                                    {user.role} • {user.password}
                                </div>
                            </div>
                        ))}
                    </div>

                    <p style={{
                        marginTop: '2rem',
                        fontSize: '0.875rem',
                        color: '#bdc3c7',
                        fontStyle: 'italic'
                    }}>
                        Click on any user above to auto-fill the login form
                    </p>
                </div>
            </div>
        </div>
    );
}
