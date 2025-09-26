import { useState, useEffect, useRef } from 'react';

// Use localhost:8000 since the browser runs on the host machine
const API_BASE = 'http://localhost:8000';

export function useChat(token) {
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const eventSourceRef = useRef(null);

    // Create a new chat session
    const createSession = async () => {
        if (!token) return;

        try {
            const response = await fetch(`${API_BASE}/api/v1/chat/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ persona: 'auto' }),
            });

            if (response.ok) {
                const data = await response.json();
                setSessionId(data.session_id);
                return data.session_id;
            }
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    };

    // Connect to SSE stream
    const connectToStream = (sessionId) => {
        if (!token || !sessionId) return;

        const eventSource = new EventSource(
            `${API_BASE}/api/v1/chat/sse?session_id=${sessionId}&token=${token}`
        );

        eventSource.onopen = () => {
            setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'message':
                    setMessages(prev => [...prev, {
                        id: data.message_id,
                        sender: 'assistant',
                        content: data.reply.message,
                        cards: data.reply.cards || [],
                        actions: data.reply.actions || [],
                        timestamp: new Date(),
                    }]);
                    setIsTyping(false);
                    break;
                case 'typing':
                    setIsTyping(data.actor === 'assistant');
                    break;
                case 'error':
                    console.error('Chat error:', data.error);
                    setIsTyping(false);
                    break;
            }
        };

        eventSource.onerror = () => {
            setIsConnected(false);
            eventSource.close();
        };

        eventSourceRef.current = eventSource;
    };

    // Send a message
    const sendMessage = async (text) => {
        if (!token || !sessionId) return;

        // Add user message to UI immediately
        const userMessage = {
            id: Date.now(),
            sender: 'user',
            content: text,
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);
        setIsTyping(true);

        try {
            await fetch(`${API_BASE}/api/v1/chat/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    client_idempotency_key: crypto.randomUUID(),
                }),
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            setIsTyping(false);
        }
    };

    // Execute an action
    const executeAction = async (action) => {
        if (!token || !sessionId) return;

        try {
            const response = await fetch(`${API_BASE}/api/v1/chat/action-runner`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    action,
                }),
            });

            if (response.ok) {
                const result = await response.json();
                // Add system message about action result
                setMessages(prev => [...prev, {
                    id: Date.now(),
                    sender: 'system',
                    content: result.message || 'Action completed successfully',
                    timestamp: new Date(),
                }]);
            }
        } catch (error) {
            console.error('Failed to execute action:', error);
        }
    };

    // Initialize session and connection
    useEffect(() => {
        if (token && !sessionId) {
            createSession().then(newSessionId => {
                if (newSessionId) {
                    connectToStream(newSessionId);
                }
            });
        }
    }, [token]);

    // Cleanup
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return {
        messages,
        sendMessage,
        executeAction,
        isConnected,
        isTyping,
    };
}
