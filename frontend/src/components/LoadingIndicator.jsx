import React from 'react';

const LoadingIndicator = ({ type = 'dots', text = 'Thinking...' }) => {
    if (type === 'spinner') {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
            }}>
                <div style={{
                    width: '16px',
                    height: '16px',
                    border: '2px solid #e3e3e3',
                    borderTop: '2px solid #007bff',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                }} />
                <span>{text}</span>
                <style>{`
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `}</style>
            </div>
        );
    }

    // Default animated dots
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
        }}>
            <div style={{
                display: 'flex',
                gap: '0.25rem'
            }}>
                <span style={{
                    display: 'inline-block',
                    width: '6px',
                    height: '6px',
                    backgroundColor: '#007bff',
                    borderRadius: '50%',
                    animation: 'bounce 1.4s ease-in-out infinite both',
                    animationDelay: '0s'
                }} />
                <span style={{
                    display: 'inline-block',
                    width: '6px',
                    height: '6px',
                    backgroundColor: '#007bff',
                    borderRadius: '50%',
                    animation: 'bounce 1.4s ease-in-out infinite both',
                    animationDelay: '0.16s'
                }} />
                <span style={{
                    display: 'inline-block',
                    width: '6px',
                    height: '6px',
                    backgroundColor: '#007bff',
                    borderRadius: '50%',
                    animation: 'bounce 1.4s ease-in-out infinite both',
                    animationDelay: '0.32s'
                }} />
            </div>
            <span>{text}</span>
            <style>{`
                @keyframes bounce {
                    0%, 80%, 100% {
                        transform: scale(0);
                        opacity: 0.5;
                    }
                    40% {
                        transform: scale(1);
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
};

export default LoadingIndicator;
