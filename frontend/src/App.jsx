import React, { useEffect, useState } from 'react';
import { fetchUsers } from './api.js';
import StudentChatBot from './components/StudentChatBot.jsx';
import AdvisorChatBot from './components/AdvisorChatBot.jsx';
import HeadChatBot from './components/HeadChatBot.jsx';
import AdminChatBot from './components/AdminChatBot.jsx';

export default function App() {
    const [users, setUsers] = useState([]);
    const [currentUser, setCurrentUser] = useState(null);

    useEffect(() => {
        fetchUsers().then(setUsers).catch(console.error);
    }, []);

    const handleLogin = (e) => {
        const id = parseInt(e.target.value);
        const user = users.find((u) => u.id === id);
        setCurrentUser(user);
    };

    const handleLogout = () => {
        setCurrentUser(null);
    };

    let view = null;
    if (currentUser) {
        switch (currentUser.role) {
            case 'student':
                view = <StudentChatBot user={currentUser} />;
                break;
            case 'advisor':
                view = <AdvisorChatBot user={currentUser} />;
                break;
            case 'department_head':
                view = <HeadChatBot user={currentUser} />;
                break;
            case 'system_admin':
                view = <AdminChatBot user={currentUser} />;
                break;
            default:
                view = <p>Unknown role.</p>;
                break;
        }
    }

    return (
        <div style={{ padding: '2rem', fontFamily: 'Arial', position: 'relative', minHeight: '100vh' }}>
            <h1>BRS Prototype Portal</h1>
            {!currentUser && (
                <div>
                    <h2>Login</h2>
                    <select onChange={handleLogin} defaultValue="">
                        <option value="" disabled>
                            Select your user
                        </option>
                        {users.map((u) => (
                            <option key={u.id} value={u.id}>
                                {u.full_name} ({u.role.replace('_', ' ')})
                            </option>
                        ))}
                    </select>
                </div>
            )}
            {currentUser && (
                <div>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '1rem'
                    }}>
                        <h2>Welcome, {currentUser.full_name}</h2>
                        <button
                            onClick={handleLogout}
                            style={{
                                position: 'absolute',
                                top: '2rem',
                                right: '2rem',
                                padding: '0.5rem 1rem',
                                backgroundColor: '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontWeight: 'bold',
                                fontSize: '0.9rem',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                            }}
                            onMouseOver={(e) => e.target.style.backgroundColor = '#c82333'}
                            onMouseOut={(e) => e.target.style.backgroundColor = '#dc3545'}
                        >
                            Log out
                        </button>
                    </div>
                    {view}
                </div>
            )}
        </div>
    );
}
