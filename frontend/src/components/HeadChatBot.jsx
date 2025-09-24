import React, { useState, useEffect, useRef } from 'react';
import { checkSystemHealth } from '../api.js';
import LoadingIndicator from './LoadingIndicator.jsx';

// Helper function to convert markdown to HTML
function formatAIResponse(content) {
    return content
        // Headers
        .replace(/### (.*$)/gm, '<h3 style="font-size: 1.1em; font-weight: bold; margin: 1em 0 0.5em 0; color: #333;">$1</h3>')
        .replace(/#### (.*$)/gm, '<h4 style="font-size: 1em; font-weight: bold; margin: 0.8em 0 0.4em 0; color: #333;">$1</h4>')
        .replace(/##### (.*$)/gm, '<h5 style="font-size: 0.9em; font-weight: bold; margin: 0.6em 0 0.3em 0; color: #333;">$1</h5>')
        // Bold text
        .replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight: bold; color: #007bff;">$1</strong>')
        // Italic text
        .replace(/\*(.*?)\*/g, '<em style="font-style: italic;">$1</em>')
        // Code blocks
        .replace(/`(.*?)`/g, '<code style="background-color: #f1f3f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 0.9em;">$1</code>')
        // Bullet points
        .replace(/^\s*[-•]\s+/gm, '• ')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Clean up multiple line breaks
        .replace(/(<br>){3,}/g, '<br><br>')
        .trim();
}

export default function HeadChatBot({ user }) {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [systemHealth, setSystemHealth] = useState(null);
    const [aiConfigured, setAiConfigured] = useState(true);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Check system health and initialize department head interface
        const checkHealthAndInitialize = async () => {
            try {
                const health = await checkSystemHealth();
                setSystemHealth(health);
                setAiConfigured(health.openai_configured);

                if (health.openai_configured) {
                    // Try to get AI-powered greeting
                    try {
                        const response = await fetch('http://localhost:8000/advisor-chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                message: "Hello, I'm ready to start my department head session",
                                advisor_id: user.id
                            }),
                        });

                        if (response.ok) {
                            const data = await response.json();
                            const greeting = {
                                type: 'bot',
                                content: formatAIResponse(data.response),
                                timestamp: new Date()
                            };
                            setMessages([greeting]);
                        } else {
                            throw new Error('Failed to initialize department head chat');
                        }
                    } catch (error) {
                        console.error('Failed to get AI greeting:', error);
                        setMessages([{
                            type: 'bot',
                            content: `Hello Dr. ${user.full_name}! 👋\n\nI'm your AI assistant for department head duties. I can help you with complex academic matters and oversight.\n\n**Available Actions:**\n• Review escalated course requests\n• Make final decisions on complex cases\n• Oversee department academic policy\n• Review student academic appeals\n• Manage departmental course offerings\n• Analyze enrollment patterns\n• Handle advisor escalations\n\nWhat can I help you with today?`,
                            timestamp: new Date()
                        }]);
                    }
                } else {
                    setMessages([
                        {
                            type: 'bot',
                            content: `Hi Dr. ${user.full_name}! I'm sorry, but the AI assistant is currently not available because the OpenAI API key is not configured. Please check the system configuration to enable AI features.\n\n⚠️ **System Status:** AI services are offline`,
                            timestamp: new Date(),
                            isError: true
                        }
                    ]);
                }
            } catch (error) {
                console.error('Health check failed:', error);
                setAiConfigured(false);
                setMessages([
                    {
                        type: 'bot',
                        content: `Hi Dr. ${user.full_name}! I'm experiencing technical difficulties connecting to the AI service. Please check system connectivity and try again.\n\n❌ **System Status:** Connection failed`,
                        timestamp: new Date(),
                        isError: true
                    }
                ]);
            }
        };

        checkHealthAndInitialize();
    }, [user.full_name]);

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        if (!aiConfigured) {
            const errorMessage = {
                type: 'bot',
                content: 'I\'m sorry, but the AI assistant is not available right now. Please check the system configuration and try again.',
                timestamp: new Date(),
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
            setInputMessage('');
            return;
        }

        const userMessage = {
            type: 'user',
            content: inputMessage,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        const originalMessage = inputMessage;
        setInputMessage('');

        try {
            const response = await fetch('http://localhost:8000/advisor-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: originalMessage,
                    advisor_id: user.id
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to get department head chat response');
            }

            const data = await response.json();

            const botMessage = {
                type: 'bot',
                content: formatAIResponse(data.response),
                timestamp: new Date(),
                action: data.action,
                request_info: data.request_info
            };

            setMessages(prev => [...prev, botMessage]);

            // Handle specific actions
            if (data.action === 'config_error') {
                setAiConfigured(false);
            }

        } catch (error) {
            console.error('Error processing message:', error);
            const errorMessage = {
                type: 'bot',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '600px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
        }}>
            {/* Header */}
            <div style={{
                padding: '1rem',
                backgroundColor: '#007bff',
                color: 'white',
                borderRadius: '8px 8px 0 0',
                fontWeight: 'bold'
            }}>
                🏛️ Department Head Assistant - Dr. {user.full_name}
            </div>

            {/* Messages Area */}
            <div style={{
                flex: 1,
                padding: '1rem',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem'
            }}>
                {messages.map((message, index) => (
                    <div key={index} style={{
                        alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: message.type === 'user' ? '75%' : '85%',
                        marginBottom: '1rem'
                    }}>
                        {message.type === 'bot' && (
                            <div style={{
                                fontSize: '0.8rem',
                                color: '#007bff',
                                marginBottom: '0.25rem',
                                fontWeight: '500'
                            }}>
                                🏛️ Department Assistant
                            </div>
                        )}
                        <div style={{
                            padding: '0.75rem 1rem',
                            borderRadius: message.type === 'user' ? '1rem 1rem 0.25rem 1rem' : '1rem 1rem 1rem 0.25rem',
                            backgroundColor: message.type === 'user' ? '#007bff' : '#f8f9fa',
                            border: message.type === 'user' ? 'none' : '1px solid #e9ecef',
                            color: message.type === 'user' ? 'white' : '#333',
                            marginBottom: '0.25rem',
                            whiteSpace: 'pre-wrap',
                            lineHeight: '1.6',
                            fontSize: '0.95rem',
                            boxShadow: message.type === 'user' ? '0 2px 4px rgba(0,123,255,0.2)' : '0 1px 3px rgba(0,0,0,0.1)'
                        }}>
                            {message.type === 'bot' ? (
                                <div dangerouslySetInnerHTML={{ __html: formatAIResponse(message.content) }} />
                            ) : (
                                message.content
                            )}
                        </div>
                        <div style={{
                            fontSize: '0.75rem',
                            color: '#999',
                            textAlign: message.type === 'user' ? 'right' : 'left',
                            paddingLeft: message.type === 'user' ? '0' : '1rem',
                            paddingRight: message.type === 'user' ? '1rem' : '0'
                        }}>
                            {message.timestamp.toLocaleTimeString()}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div style={{
                        alignSelf: 'flex-start',
                        maxWidth: '85%',
                        marginBottom: '1rem'
                    }}>
                        <div style={{
                            fontSize: '0.8rem',
                            color: '#007bff',
                            marginBottom: '0.25rem',
                            fontWeight: '500'
                        }}>
                            🏛️ Department Assistant
                        </div>
                        <div style={{
                            padding: '0.75rem 1rem',
                            borderRadius: '1rem 1rem 1rem 0.25rem',
                            backgroundColor: '#f8f9fa',
                            border: '1px solid #e9ecef',
                            color: '#666',
                            fontStyle: 'italic'
                        }}>
                            <LoadingIndicator type="dots" text="Processing..." />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div style={{
                padding: '1rem',
                borderTop: '1px solid #ddd',
                backgroundColor: 'white',
                borderRadius: '0 0 8px 8px'
            }}>
                <div style={{
                    display: 'flex',
                    gap: '0.5rem',
                    alignItems: 'flex-end'
                }}>
                    <textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask me about department requests, escalations, or say something like 'show pending requests'..."
                        style={{
                            flex: 1,
                            padding: '0.75rem',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            resize: 'none',
                            minHeight: '40px',
                            maxHeight: '120px',
                            fontFamily: 'inherit'
                        }}
                        rows={1}
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={isLoading || !inputMessage.trim()}
                        style={{
                            padding: '0.75rem 1.5rem',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: isLoading || !inputMessage.trim() ? 'not-allowed' : 'pointer',
                            fontSize: '0.9rem',
                            fontWeight: '500',
                            opacity: isLoading || !inputMessage.trim() ? 0.6 : 1,
                            transition: 'opacity 0.2s'
                        }}
                    >
                        {isLoading ? 'Sending...' : 'Send'}
                    </button>
                </div>
            </div>
        </div>
    );
}
