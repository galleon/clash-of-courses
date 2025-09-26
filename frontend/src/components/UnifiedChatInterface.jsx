import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat.js';
import CardRenderer from './CardRenderer.jsx';
import ActionButtons from './ActionButtons.jsx';

export default function UnifiedChatInterface({ user, token, onLogout }) {
    const { messages, sendMessage, executeAction, isConnected, isTyping } = useChat(token);
    const [inputValue, setInputValue] = useState('');
    const [isInputFocused, setIsInputFocused] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        await sendMessage(inputValue);
        setInputValue('');
        inputRef.current?.focus();
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(e);
        }
    };

    const getRoleColor = (role) => {
        const colors = {
            'student': '#007bff',
            'advisor': '#28a745',
            'department_head': '#6f42c1',
            'system_admin': '#dc3545'
        };
        return colors[role] || '#6c757d';
    };

    const getRoleIcon = (role) => {
        const icons = {
            'student': '🎓',
            'advisor': '👨‍🏫',
            'department_head': '👔',
            'system_admin': '⚙️'
        };
        return icons[role] || '👤';
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100vh',
            fontFamily: 'Arial, sans-serif',
            backgroundColor: '#f8f9fa'
        }}>
            {/* Header */}
            <header style={{
                backgroundColor: 'white',
                borderBottom: '1px solid #dee2e6',
                padding: '1rem 2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <h1 style={{ margin: 0, color: '#2c3e50', fontSize: '1.5rem' }}>
                        BRS Chat Portal
                    </h1>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem 1rem',
                        backgroundColor: getRoleColor(user?.role),
                        color: 'white',
                        borderRadius: '20px',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                    }}>
                        <span>{getRoleIcon(user?.role)}</span>
                        <span>{user?.full_name}</span>
                        <span>•</span>
                        <span>{user?.role?.replace('_', ' ')}</span>
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                        color: isConnected ? '#28a745' : '#dc3545'
                    }}>
                        <div style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            backgroundColor: isConnected ? '#28a745' : '#dc3545'
                        }} />
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </div>

                    <button
                        onClick={onLogout}
                        style={{
                            padding: '0.5rem 1rem',
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontWeight: '500',
                            fontSize: '0.875rem'
                        }}
                    >
                        Sign Out
                    </button>
                </div>
            </header>

            {/* Chat Messages */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1rem 2rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem'
            }}>
                {messages.length === 0 && (
                    <div style={{
                        textAlign: 'center',
                        padding: '3rem 1rem',
                        color: '#6c757d'
                    }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
                        <h3 style={{ margin: '0 0 1rem 0' }}>Welcome to BRS Chat!</h3>
                        <p>
                            I'm your academic assistant. I can help you with course registration,
                            schedule planning, and academic advising. Just ask me anything!
                        </p>
                        <div style={{
                            display: 'flex',
                            gap: '0.5rem',
                            justifyContent: 'center',
                            marginTop: '2rem',
                            flexWrap: 'wrap'
                        }}>
                            {[
                                "Show me my current schedule",
                                "I want to add CS101",
                                "What are my course options?",
                                "Help me plan next semester"
                            ].map((suggestion, i) => (
                                <button
                                    key={i}
                                    onClick={() => {
                                        setInputValue(suggestion);
                                        inputRef.current?.focus();
                                    }}
                                    style={{
                                        padding: '0.5rem 1rem',
                                        backgroundColor: 'white',
                                        border: '1px solid #dee2e6',
                                        borderRadius: '20px',
                                        cursor: 'pointer',
                                        fontSize: '0.875rem',
                                        color: '#495057'
                                    }}
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((message) => (
                    <div
                        key={message.id}
                        style={{
                            display: 'flex',
                            justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                            marginBottom: '1rem'
                        }}
                    >
                        <div style={{
                            maxWidth: '70%',
                            minWidth: message.sender === 'assistant' ? '300px' : 'auto'
                        }}>
                            <div style={{
                                padding: '1rem',
                                borderRadius: '12px',
                                backgroundColor: message.sender === 'user' ? '#007bff' : 'white',
                                color: message.sender === 'user' ? 'white' : '#495057',
                                border: message.sender === 'user' ? 'none' : '1px solid #dee2e6',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                            }}>
                                {message.sender !== 'user' && (
                                    <div style={{
                                        fontSize: '0.75rem',
                                        color: '#6c757d',
                                        marginBottom: '0.5rem',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem'
                                    }}>
                                        <span>🤖</span>
                                        <span>Assistant</span>
                                        <span>•</span>
                                        <span>{message.timestamp?.toLocaleTimeString()}</span>
                                    </div>
                                )}

                                <div style={{ lineHeight: '1.5' }}>
                                    {message.content}
                                </div>

                                {/* Render cards */}
                                {message.cards && <CardRenderer cards={message.cards} />}

                                {/* Render action buttons */}
                                {message.actions && (
                                    <ActionButtons
                                        actions={message.actions}
                                        onExecuteAction={executeAction}
                                    />
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {/* Typing indicator */}
                {isTyping && (
                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <div style={{
                            padding: '1rem',
                            borderRadius: '12px',
                            backgroundColor: 'white',
                            border: '1px solid #dee2e6',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            color: '#6c757d'
                        }}>
                            <div style={{
                                display: 'flex',
                                gap: '2px'
                            }}>
                                <div style={{
                                    width: '6px',
                                    height: '6px',
                                    borderRadius: '50%',
                                    backgroundColor: '#6c757d',
                                    animation: 'typing 1.4s infinite ease-in-out',
                                    animationDelay: '0ms'
                                }} />
                                <div style={{
                                    width: '6px',
                                    height: '6px',
                                    borderRadius: '50%',
                                    backgroundColor: '#6c757d',
                                    animation: 'typing 1.4s infinite ease-in-out',
                                    animationDelay: '200ms'
                                }} />
                                <div style={{
                                    width: '6px',
                                    height: '6px',
                                    borderRadius: '50%',
                                    backgroundColor: '#6c757d',
                                    animation: 'typing 1.4s infinite ease-in-out',
                                    animationDelay: '400ms'
                                }} />
                            </div>
                            <span>Assistant is typing...</span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div style={{
                borderTop: '1px solid #dee2e6',
                backgroundColor: 'white',
                padding: '1rem 2rem'
            }}>
                <form onSubmit={handleSend} style={{ display: 'flex', gap: '1rem' }}>
                    <textarea
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onFocus={() => setIsInputFocused(true)}
                        onBlur={() => setIsInputFocused(false)}
                        placeholder="Type your message here... (Shift+Enter for new line)"
                        style={{
                            flex: 1,
                            minHeight: '2.5rem',
                            maxHeight: '8rem',
                            padding: '0.75rem',
                            border: `2px solid ${isInputFocused ? '#007bff' : '#dee2e6'}`,
                            borderRadius: '8px',
                            fontSize: '1rem',
                            resize: 'vertical',
                            fontFamily: 'inherit',
                            transition: 'border-color 0.2s',
                            outline: 'none'
                        }}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || !isConnected}
                        style={{
                            padding: '0.75rem 1.5rem',
                            backgroundColor: !inputValue.trim() || !isConnected ? '#6c757d' : '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: !inputValue.trim() || !isConnected ? 'not-allowed' : 'pointer',
                            fontWeight: '500',
                            fontSize: '1rem',
                            transition: 'background-color 0.2s'
                        }}
                    >
                        Send
                    </button>
                </form>
            </div>

            <style>{`
        @keyframes typing {
          0%, 60%, 100% {
            transform: translateY(0);
          }
          30% {
            transform: translateY(-10px);
          }
        }
      `}</style>
        </div>
    );
}
