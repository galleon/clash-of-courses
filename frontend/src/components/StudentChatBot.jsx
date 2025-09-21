import React, { useState, useEffect, useRef } from 'react';
import { sendChatMessage, submitRequest, checkSystemHealth, fetchRequests } from '../api.js';

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

export default function StudentChatBot({ user }) {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [systemHealth, setSystemHealth] = useState(null);
    const [aiConfigured, setAiConfigured] = useState(true);
    const messagesEndRef = useRef(null); const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Check system health and student's request status
        const checkHealthAndRequests = async () => {
            try {
                const health = await checkSystemHealth();
                setSystemHealth(health);
                setAiConfigured(health.openai_configured);

                // Check for student's requests
                let requestStatusMessage = '';
                try {
                    const allRequests = await fetchRequests('all');
                    const studentRequests = allRequests.filter(req => req.student_id === user.id);

                    if (studentRequests.length > 0) {
                        const pending = studentRequests.filter(req => req.status === 'pending').length;
                        const approved = studentRequests.filter(req => req.status === 'approved').length;
                        const rejected = studentRequests.filter(req => req.status === 'rejected').length;

                        const statusParts = [];
                        if (pending > 0) statusParts.push(`${pending} pending`);
                        if (approved > 0) statusParts.push(`${approved} approved`);
                        if (rejected > 0) statusParts.push(`${rejected} rejected`);

                        requestStatusMessage = `\n\n📋 **Your Course Requests:**\nYou have ${statusParts.join(', ')} request${studentRequests.length > 1 ? 's' : ''}.\n\nAsk me "what's my request status?" for details.`;
                    }
                } catch (error) {
                    console.error('Failed to fetch student requests:', error);
                }

                if (health.openai_configured) {
                    setMessages([
                        {
                            type: 'bot',
                            content: `Hi ${user.full_name}! 👋 I'm your AI-powered academic assistant. I can help you manage your course enrollment.${requestStatusMessage}\n\n**Available Actions:**\n• View your current enrolled courses\n• Browse available courses and descriptions\n• Request to add courses (requires advisor approval)\n• Request to drop courses (requires advisor approval)\n• Check your course request status\n• Get course recommendations based on your major\n\nWhat would you like to do today?`,
                            timestamp: new Date()
                        }
                    ]);
                } else {
                    setMessages([
                        {
                            type: 'bot',
                            content: `Hi ${user.full_name}! I'm sorry, but the AI assistant is currently not available because the OpenAI API key is not configured. Please contact your system administrator to enable AI features, or use the traditional form interface by clicking "Traditional View" above.${requestStatusMessage}`,
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
                        content: `Hi ${user.full_name}! I'm experiencing technical difficulties connecting to the AI service. Please try using the traditional form interface or contact support.`,
                        timestamp: new Date(),
                        isError: true
                    }
                ]);
            }
        };

        checkHealthAndRequests();
    }, [user.full_name]); const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        if (!aiConfigured) {
            const errorMessage = {
                type: 'bot',
                content: 'I\'m sorry, but the AI assistant is not available right now. Please use the traditional form interface above.',
                timestamp: new Date(),
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
            setInputValue('');
            return;
        }

        const userMessage = {
            type: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await sendChatMessage({
                message: inputValue,
                student_id: user.id
            });

            const botMessage = {
                type: 'bot',
                content: formatAIResponse(response.response),
                timestamp: new Date(),
                action: response.action,
                course_info: response.course_info
            };

            setMessages(prev => [...prev, botMessage]);

            // Handle specific actions
            if (response.action === 'config_error') {
                setAiConfigured(false);
            } else if (response.action === 'course_requested') {
                // Show success message for course enrollment request
                console.log('Course enrollment requested:', response.course_info);
            } else if (response.action === 'drop_requested') {
                // Show success message for course drop request
                console.log('Course drop requested:', response.course_info);
            } else if (response.action === 'add_course' || response.action === 'drop_course') {
                // General intent detected - the AI response should guide them
            }

        } catch (error) {
            console.error('Chat error:', error);
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

    const handleQuickAction = async (action, courseCode) => {
        try {
            let requestType = '';
            let justification = '';

            if (action === 'add') {
                requestType = 'add';
                justification = `Student requested to add ${courseCode} via chatbot`;
            } else if (action === 'drop') {
                requestType = 'drop';
                justification = `Student requested to drop ${courseCode} via chatbot`;
            }

            // This would need the actual course ID - you'd need to look it up
            // For now, using placeholder
            await submitRequest({
                student_id: user.id,
                request_type: requestType,
                course_id: 1, // This should be looked up based on courseCode
                justification: justification
            });

            const successMessage = {
                type: 'bot',
                content: `I've submitted your request to ${action} ${courseCode}. Your advisor will review it soon.`,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, successMessage]);

        } catch (error) {
            console.error('Quick action error:', error);
            const errorMessage = {
                type: 'bot',
                content: 'Sorry, I couldn\'t submit that request. Please try again.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
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
                Academic Assistant - Course Management
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
                                AI Assistant
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
                            AI Assistant
                        </div>
                        <div style={{
                            padding: '0.75rem 1rem',
                            borderRadius: '1rem 1rem 1rem 0.25rem',
                            backgroundColor: '#f8f9fa',
                            border: '1px solid #e9ecef',
                            color: '#666',
                            fontStyle: 'italic',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}>
                            <span>●</span>
                            <span>●</span>
                            <span>●</span>
                            <span>Thinking...</span>
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
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask me about your courses, or say something like 'show my courses' or 'I want to add CS101'..."
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
                        disabled={isLoading || !inputValue.trim()}
                        style={{
                            padding: '0.75rem 1.5rem',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            opacity: (isLoading || !inputValue.trim()) ? 0.6 : 1
                        }}
                    >
                        Send
                    </button>
                </div>

                {/* Quick Actions */}
                <div style={{
                    marginTop: '0.5rem',
                    display: 'flex',
                    gap: '0.5rem',
                    flexWrap: 'wrap'
                }}>
                    <button
                        onClick={() => setInputValue('What courses am I taking?')}
                        style={{
                            padding: '0.25rem 0.5rem',
                            backgroundColor: '#f8f9fa',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontSize: '0.875rem',
                            cursor: 'pointer'
                        }}
                    >
                        My Courses
                    </button>
                    <button
                        onClick={() => setInputValue('What courses are available?')}
                        style={{
                            padding: '0.25rem 0.5rem',
                            backgroundColor: '#f8f9fa',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontSize: '0.875rem',
                            cursor: 'pointer'
                        }}
                    >
                        Available Courses
                    </button>
                    <button
                        onClick={() => setInputValue('I want to add a course')}
                        style={{
                            padding: '0.25rem 0.5rem',
                            backgroundColor: '#f8f9fa',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontSize: '0.875rem',
                            cursor: 'pointer'
                        }}
                    >
                        Add Course
                    </button>
                </div>
            </div>
        </div>
    );
}
