import React, { useState, useEffect, useRef } from 'react';

const API_BASE_URL = 'http://localhost:8000';

// JWT Authentication hook
function useAuth() {
    const [token, setToken] = useState(localStorage.getItem('brs_token'));
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);

    const login = async (username, password) => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) throw new Error('Login failed');

            const data = await response.json();
            setToken(data.token);
            setUser({
                user_id: data.user_id,
                role: data.role,
                full_name: data.full_name
            });
            localStorage.setItem('brs_token', data.token);
            return true;
        } catch (error) {
            console.error('Login error:', error);
            return false;
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('brs_token');
    };

    // Validate token on mount
    useEffect(() => {
        if (token) {
            fetch(`${API_BASE_URL}/v1/auth/validate`, {
                headers: { Authorization: `Bearer ${token}` }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.valid) {
                        setUser({
                            user_id: data.user_id,
                            role: data.role,
                            full_name: data.full_name
                        });
                    } else {
                        logout();
                    }
                })
                .catch(() => logout());
        }
    }, [token]);

    return { token, user, login, logout, loading };
}

// Chat hook with SSE streaming
function useChat(sessionId, token) {
    const [events, setEvents] = useState([]);
    const esRef = useRef(null);

    const send = async (text) => {
        if (!sessionId || !token) return;

        try {
            const response = await fetch(`${API_BASE_URL}/v1/chat/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    client_idempotency_key: crypto.randomUUID()
                })
            });

            const data = await response.json();
            setEvents(prev => [...prev, { type: 'user', data: text }, { type: 'assistant', data }]);
        } catch (error) {
            console.error('Send message error:', error);
        }
    };

    const connect = () => {
        if (!sessionId || !token) return;

        esRef.current = new EventSource(
            `${API_BASE_URL}/v1/chat/sse?session_id=${sessionId}`,
            { withCredentials: true }
        );

        esRef.current.onmessage = (e) => {
            const event = JSON.parse(e.data);
            setEvents(prev => [...prev, event]);
        };

        esRef.current.onerror = () => {
            esRef.current?.close();
        };
    };

    useEffect(() => {
        if (sessionId && token) {
            connect();
            return () => esRef.current?.close();
        }
    }, [sessionId, token]);

    return { events, send };
}

// Card components for rich chat responses
function WeekGrid({ payload }) {
    return (
        <div className="bg-white border rounded-lg p-4 my-2">
            <h3 className="font-bold mb-2">Your Schedule</h3>
            <div className="space-y-2">
                {payload.courses?.map((course, i) => (
                    <div key={i} className="flex justify-between border-l-4 border-blue-500 pl-3">
                        <div>
                            <span className="font-semibold">{course.course_code}</span>
                            <span className="text-gray-600 ml-2">{course.title}</span>
                        </div>
                        <div className="text-right text-sm text-gray-500">
                            <div>{course.time}</div>
                            <div>{course.instructor}</div>
                        </div>
                    </div>
                ))}
            </div>
            <div className="mt-3 text-sm text-gray-600">
                Total Credits: {payload.total_credits}
            </div>
        </div>
    );
}

function Alternatives({ payload }) {
    return (
        <div className="bg-white border rounded-lg p-4 my-2">
            <h3 className="font-bold mb-2">Available Sections for {payload.course_code}</h3>
            <div className="space-y-2">
                {payload.sections?.map((section, i) => (
                    <div key={i} className={`p-3 border rounded ${section.conflicts?.length > 0 ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
                        <div className="flex justify-between items-center">
                            <div>
                                <span className="font-semibold">Section {section.section_code}</span>
                                <span className="ml-2 text-gray-600">{section.time}</span>
                            </div>
                            <div className="text-right text-sm">
                                <div>{section.instructor}</div>
                                <div className="text-gray-500">{section.enrolled}/{section.capacity} enrolled</div>
                            </div>
                        </div>
                        {section.conflicts?.length > 0 && (
                            <div className="mt-2 text-sm text-red-600">
                                ⚠️ {section.conflicts.join(', ')}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

function RequestSummary({ payload }) {
    return (
        <div className="bg-white border rounded-lg p-4 my-2">
            <h3 className="font-bold mb-2">Your Requests</h3>

            {payload.pending?.length > 0 && (
                <div className="mb-3">
                    <h4 className="font-semibold text-yellow-600 mb-1">Pending</h4>
                    {payload.pending.map((req, i) => (
                        <div key={i} className="p-2 bg-yellow-50 border-l-4 border-yellow-400 mb-1">
                            <div className="text-sm">
                                {req.type} {req.course} {req.section} - {req.status}
                            </div>
                            <div className="text-xs text-gray-500">Submitted: {req.submitted}</div>
                        </div>
                    ))}
                </div>
            )}

            {payload.completed?.length > 0 && (
                <div>
                    <h4 className="font-semibold text-green-600 mb-1">Completed</h4>
                    {payload.completed.map((req, i) => (
                        <div key={i} className="p-2 bg-green-50 border-l-4 border-green-400 mb-1">
                            <div className="text-sm">
                                {req.type} {req.course} - {req.status}
                            </div>
                            <div className="text-xs text-gray-500">Completed: {req.completed}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// Main CardRenderer component
function CardRenderer({ cards }) {
    return (
        <>
            {cards?.map((card, i) => {
                switch (card.type) {
                    case 'week_grid':
                        return <WeekGrid key={i} payload={card.payload} />;
                    case 'alternatives':
                        return <Alternatives key={i} payload={card.payload} />;
                    case 'request_summary':
                        return <RequestSummary key={i} payload={card.payload} />;
                    default:
                        // Hide unknown card types instead of showing JSON
                        return null;
                }
            })}
        </>
    );
}

// Login component
function LoginForm({ onLogin, loading }) {
    const [credentials, setCredentials] = useState({ username: '', password: '' });

    const handleSubmit = (e) => {
        e.preventDefault();
        onLogin(credentials.username, credentials.password);
    };

    const quickLogin = (username) => {
        setCredentials({ username, password: 'password123' });
        onLogin(username, 'password123');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full space-y-8">
                <div>
                    <h2 className="text-3xl font-bold text-center">BRS Login</h2>
                    <p className="text-center text-gray-600 mt-2">Business Registration System</p>
                </div>

                <form className="space-y-6" onSubmit={handleSubmit}>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Username</label>
                        <input
                            type="text"
                            value={credentials.username}
                            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Enter username"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Password</label>
                        <input
                            type="password"
                            value={credentials.password}
                            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Enter password"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                        {loading ? 'Signing in...' : 'Sign in'}
                    </button>
                </form>

                <div className="mt-4">
                    <p className="text-sm text-gray-600 mb-2">Quick login as:</p>
                    <div className="space-y-1">
                        <button onClick={() => quickLogin('sarah.ahmed')} className="w-full text-left px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 rounded">
                            Sarah Ahmed (Student)
                        </button>
                        <button onClick={() => quickLogin('dr.williams')} className="w-full text-left px-3 py-2 text-sm bg-green-50 hover:bg-green-100 rounded">
                            Dr. Williams (Advisor)
                        </button>
                        <button onClick={() => quickLogin('prof.johnson')} className="w-full text-left px-3 py-2 text-sm bg-purple-50 hover:bg-purple-100 rounded">
                            Prof. Johnson (Department Head)
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Main BRS Chat App
function BRSChatApp() {
    const { token, user, login, logout, loading } = useAuth();
    const [sessionId, setSessionId] = useState(null);
    const [message, setMessage] = useState('');
    const { events, send } = useChat(sessionId, token);

    // Create chat session when logged in
    useEffect(() => {
        if (token && !sessionId) {
            fetch(`${API_BASE_URL}/v1/chat/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ persona: 'auto' })
            })
                .then(res => res.json())
                .then(data => setSessionId(data.session_id))
                .catch(console.error);
        }
    }, [token, sessionId]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (message.trim()) {
            send(message);
            setMessage('');
        }
    };

    const executeAction = async (action) => {
        try {
            const response = await fetch(action.endpoint, {
                method: action.type.toUpperCase(),
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: action.body ? JSON.stringify(action.body) : undefined
            });

            const result = await response.json();
            console.log('Action result:', result);

            // Optionally show success message
            alert(`Action "${action.label}" executed successfully!`);
        } catch (error) {
            console.error('Action execution error:', error);
            alert('Action failed. Please try again.');
        }
    };

    if (!token) {
        return <LoginForm onLogin={login} loading={loading} />;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold">BRS Chat</h1>
                        <p className="text-gray-600">Welcome, {user?.full_name} ({user?.role})</p>
                    </div>
                    <button
                        onClick={logout}
                        className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                    >
                        Logout
                    </button>
                </div>
            </div>

            {/* Chat Interface */}
            <div className="max-w-4xl mx-auto px-4 py-6">
                <div className="bg-white rounded-lg shadow-lg h-96 flex flex-col">

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {events.filter(e => e.type === 'user' || e.type === 'assistant').map((event, i) => (
                            <div key={i} className={`flex ${event.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${event.type === 'user'
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-200 text-gray-800'
                                    }`}>
                                    {event.type === 'user' ? (
                                        <p>{event.data}</p>
                                    ) : (
                                        <>
                                            <p>{event.data.reply?.message || event.data.message}</p>

                                            {/* Render cards */}
                                            {event.data.reply?.cards && (
                                                <div className="mt-2">
                                                    <CardRenderer cards={event.data.reply.cards} />
                                                </div>
                                            )}

                                            {/* Render actions */}
                                            {event.data.reply?.actions && event.data.reply.actions.length > 0 && (
                                                <div className="mt-2 space-y-1">
                                                    {event.data.reply.actions.map((action, ai) => (
                                                        <button
                                                            key={ai}
                                                            onClick={() => executeAction(action)}
                                                            className="w-full text-left px-3 py-2 text-sm bg-blue-100 hover:bg-blue-200 rounded text-blue-800"
                                                        >
                                                            {action.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Input */}
                    <form onSubmit={handleSendMessage} className="border-t p-4 flex space-x-2">
                        <input
                            type="text"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            type="submit"
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            Send
                        </button>
                    </form>

                </div>

                {/* Quick Actions */}
                <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-2">
                    <button
                        onClick={() => send("Show my schedule")}
                        className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                    >
                        📅 Show Schedule
                    </button>
                    <button
                        onClick={() => send("I want to add CS201")}
                        className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                    >
                        ➕ Add Course
                    </button>
                    <button
                        onClick={() => send("Check my request status")}
                        className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                    >
                        📋 Request Status
                    </button>
                </div>
            </div>
        </div>
    );
}

export default BRSChatApp;
