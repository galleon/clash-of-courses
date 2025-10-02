import { useState, useEffect, useRef } from 'react';
import { logger } from '../utils/logger.js';

// Use proxy path - Vite will forward /api to backend:8000
const API_BASE = '';  // Empty base URL to use proxy

export function useChat(token) {
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const eventSourceRef = useRef(null);
    const sessionCreatedRef = useRef(false);

    // Create a new chat session
    const createSession = async () => {
        if (!token) {
            logger.warn('No token available for session creation');
            return;
        }

        logger.info('Creating chat session...');
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
                logger.success('Session created:', data.session_id);
                setSessionId(data.session_id);
                return data.session_id;
            } else {
                const errorData = await response.text();
                console.error('❌ Session creation failed:', response.status, errorData);
            }
        } catch (error) {
            console.error('❌ Session creation error:', error);
        }
    };

    // Connect to SSE stream
    const connectToStream = (sessionId) => {
        if (!token || !sessionId) {
            logger.warn('Missing token or sessionId for SSE connection');
            return;
        }

        // Close existing connection if any
        if (eventSourceRef.current) {
            console.log('🔄 Closing existing SSE connection');
            eventSourceRef.current.close();
        }

        console.log('🔄 Connecting to SSE stream...', sessionId);
        const url = `${API_BASE}/api/v1/chat/sse?session_id=${sessionId}&token=${token}`;
        console.log('🔗 SSE URL:', url);

        const eventSource = new EventSource(url);

        // Add a timeout to detect connection issues
        const connectionTimeout = setTimeout(() => {
            if (eventSource.readyState === EventSource.CONNECTING) {
                console.error('⏰ SSE connection timeout - still connecting after 10 seconds');
                console.error('🔍 This might indicate CORS, network, or authentication issues');
            }
        }, 10000);

        eventSource.onopen = (event) => {
            console.log('✅ SSE connection opened', event);
            clearTimeout(connectionTimeout);
            setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
            console.log('📨 SSE message received:', event.data);
            try {
                const data = JSON.parse(event.data);

                switch (data.type) {
                    case 'connected':
                        console.log('✅ SSE connected successfully');
                        setIsConnected(true);
                        break;
                    case 'message':
                        console.log('💬 New chat message:', data);
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
            } catch (parseError) {
                console.error('❌ Failed to parse SSE message:', parseError, event.data);
            }
        };

        eventSource.onerror = (error) => {
            console.error('❌ SSE connection error:', error);
            console.error('❌ EventSource readyState:', eventSource.readyState);
            console.error('❌ EventSource url:', eventSource.url);

            // ReadyState values: 0=CONNECTING, 1=OPEN, 2=CLOSED
            switch (eventSource.readyState) {
                case EventSource.CONNECTING:
                    console.log('📡 EventSource is still connecting...');
                    break;
                case EventSource.OPEN:
                    console.log('✅ EventSource is open but had an error');
                    break;
                case EventSource.CLOSED:
                    console.log('❌ EventSource connection closed');
                    setIsConnected(false);
                    break;
            }

            // Don't automatically close on error, let it retry
        };

        eventSourceRef.current = eventSource;
    };

    // Send a message
    const sendMessage = async (text) => {
        if (!token || !sessionId) {
            console.log('❌ Cannot send message: missing token or sessionId');
            return;
        }

        console.log('📤 Sending message:', text);

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
            const response = await fetch(`${API_BASE}/api/v1/chat/messages`, {
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

            if (response.ok) {
                console.log('✅ Message sent successfully');
                const responseData = await response.json();
                console.log('📨 Received chat response:', responseData);
                console.log('💬 Assistant message:', responseData.reply.message);
                console.log('🎴 Cards:', responseData.reply.cards);
                console.log('⚡ Actions:', responseData.reply.actions);

                // Add assistant response to UI immediately
                const assistantMessage = {
                    id: responseData.message_id,
                    sender: 'assistant',
                    content: responseData.reply.message,
                    cards: responseData.reply.cards || [],
                    actions: responseData.reply.actions || [],
                    timestamp: new Date(),
                };
                setMessages(prev => [...prev, assistantMessage]);
                setIsTyping(false);
            } else {
                const errorData = await response.text();
                console.error('❌ Message send failed:', response.status, errorData);
                setIsTyping(false);
            }
        } catch (error) {
            console.error('❌ Message send error:', error);
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
        if (token && !sessionCreatedRef.current) {
            console.log('🚀 Initializing chat session...');
            sessionCreatedRef.current = true;
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
