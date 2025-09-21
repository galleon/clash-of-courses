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
        <div style={{ padding: '2rem', fontFamily: 'Arial' }}>
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
                    <h2>Welcome, {currentUser.full_name}</h2>
                    <button onClick={handleLogout}>Log out</button>
                    {view}
                </div>
            )}
        </div>
    );
}
