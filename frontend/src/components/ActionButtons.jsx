import React from 'react';

export default function ActionButtons({ actions, onExecuteAction }) {
    if (!actions || actions.length === 0) return null;

    return (
        <div style={{
            display: 'flex',
            gap: '0.5rem',
            flexWrap: 'wrap',
            marginTop: '1rem'
        }}>
            {actions.map((action, index) => (
                <button
                    key={index}
                    onClick={() => onExecuteAction(action)}
                    style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: getActionColor(action.type),
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        transition: 'opacity 0.2s'
                    }}
                    onMouseOver={(e) => e.target.style.opacity = '0.9'}
                    onMouseOut={(e) => e.target.style.opacity = '1'}
                >
                    {getActionIcon(action.type)} {action.label}
                </button>
            ))}
        </div>
    );
}

function getActionColor(actionType) {
    switch (actionType) {
        case 'post':
            return '#007bff';
        case 'put':
            return '#28a745';
        case 'delete':
            return '#dc3545';
        case 'patch':
            return '#ffc107';
        default:
            return '#6c757d';
    }
}

function getActionIcon(actionType) {
    switch (actionType) {
        case 'post':
            return '➕';
        case 'put':
            return '✏️';
        case 'delete':
            return '🗑️';
        case 'patch':
            return '🔧';
        default:
            return '⚡';
    }
}
