import React from 'react';

export default function CardRenderer({ cards }) {
    if (!cards || cards.length === 0) return null;

    return (
        <div style={{ marginTop: '1rem' }}>
            {cards.map((card, index) => (
                <div key={index} style={{ marginBottom: '1rem' }}>
                    <CardComponent card={card} />
                </div>
            ))}
        </div>
    );
}

function CardComponent({ card }) {
    switch (card.type) {
        case 'schedule_diff':
            return <ScheduleDiffCard {...card.payload} />;
        case 'week_grid':
            return <WeekGridCard {...card.payload} />;
        case 'request_summary':
            return <RequestSummaryCard {...card.payload} />;
        case 'alternatives':
            return <AlternativesCard {...card.payload} />;
        case 'course_info':
            return <CourseInfoCard {...card.payload} />;
        default:
            return <GenericCard card={card} />;
    }
}

function ScheduleDiffCard({ changes, current_schedule, new_schedule }) {
    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: '#f8f9fa'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>📅 Schedule Changes</h4>
            {changes && changes.length > 0 ? (
                <div>
                    {changes.map((change, i) => (
                        <div key={i} style={{
                            padding: '0.5rem',
                            margin: '0.5rem 0',
                            borderLeft: `4px solid ${change.type === 'add' ? '#28a745' : '#dc3545'}`,
                            backgroundColor: 'white',
                            borderRadius: '4px'
                        }}>
                            <strong>{change.type === 'add' ? '+ Adding:' : '- Removing:'}</strong> {change.course} ({change.section})
                            <br />
                            <small style={{ color: '#6c757d' }}>{change.schedule}</small>
                        </div>
                    ))}
                </div>
            ) : (
                <p style={{ color: '#6c757d' }}>No schedule changes</p>
            )}
        </div>
    );
}

function WeekGridCard({ days, conflicts }) {
    const timeSlots = ['8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>📊 Weekly Schedule</h4>
            <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                        <tr>
                            <th style={{ padding: '0.5rem', border: '1px solid #dee2e6', backgroundColor: '#f8f9fa' }}>Time</th>
                            {dayNames.map(day => (
                                <th key={day} style={{ padding: '0.5rem', border: '1px solid #dee2e6', backgroundColor: '#f8f9fa' }}>
                                    {day}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {timeSlots.map(time => (
                            <tr key={time}>
                                <td style={{ padding: '0.5rem', border: '1px solid #dee2e6', fontWeight: '500' }}>{time}</td>
                                {dayNames.map(day => {
                                    const dayData = days && days.find(d => d.day === day);
                                    const timeSlot = dayData && dayData.slots && dayData.slots.find(s => s.time === time);
                                    const hasConflict = conflicts && conflicts.some(c => c.day === day && c.time === time);

                                    return (
                                        <td key={day} style={{
                                            padding: '0.25rem',
                                            border: '1px solid #dee2e6',
                                            backgroundColor: hasConflict ? '#ffebee' : timeSlot ? '#e3f2fd' : 'white',
                                            fontSize: '0.75rem'
                                        }}>
                                            {timeSlot && (
                                                <div>
                                                    <div style={{ fontWeight: '500' }}>{timeSlot.course}</div>
                                                    <div style={{ color: '#6c757d' }}>{timeSlot.room}</div>
                                                </div>
                                            )}
                                            {hasConflict && <span style={{ color: '#d32f2f' }}>⚠️</span>}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function RequestSummaryCard({ request_id, status, course, section, type, created_at }) {
    const statusColors = {
        'submitted': '#ffc107',
        'advisor_review': '#17a2b8',
        'dept_review': '#6f42c1',
        'approved': '#28a745',
        'rejected': '#dc3545',
        'cancelled': '#6c757d'
    };

    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>📋 Request Summary</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                    <strong>Request ID:</strong> {request_id}
                </div>
                <div>
                    <strong>Type:</strong> {type}
                </div>
                <div>
                    <strong>Course:</strong> {course}
                </div>
                <div>
                    <strong>Section:</strong> {section}
                </div>
                <div>
                    <strong>Status:</strong>
                    <span style={{
                        marginLeft: '0.5rem',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        backgroundColor: statusColors[status] || '#6c757d',
                        color: 'white'
                    }}>
                        {status}
                    </span>
                </div>
                <div>
                    <strong>Created:</strong> {new Date(created_at).toLocaleDateString()}
                </div>
            </div>
        </div>
    );
}

function AlternativesCard({ alternatives = [] }) {
    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>🔄 Alternative Options</h4>
            {alternatives.length > 0 ? (
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                    {alternatives.map((alt, i) => (
                        <div key={i} style={{
                            padding: '0.75rem',
                            border: '1px solid #e9ecef',
                            borderRadius: '6px',
                            backgroundColor: '#f8f9fa'
                        }}>
                            <div style={{ fontWeight: '500' }}>{alt.course} - {alt.section}</div>
                            <div style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.25rem' }}>
                                {alt.schedule} • {alt.instructor}
                            </div>
                            <div style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>
                                Available: {alt.available_seats}/{alt.capacity}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <p style={{ color: '#6c757d' }}>No alternatives available</p>
            )}
        </div>
    );
}

function CourseInfoCard({ code, title, credits, description, prerequisites }) {
    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>📚 Course Information</h4>
            <div>
                <h5 style={{ margin: '0 0 0.5rem 0', color: '#2c3e50' }}>{code}: {title}</h5>
                <p style={{ margin: '0 0 1rem 0', fontSize: '0.875rem' }}>Credits: {credits}</p>
                {description && (
                    <p style={{ margin: '0 0 1rem 0', color: '#495057', lineHeight: '1.5' }}>{description}</p>
                )}
                {prerequisites && prerequisites.length > 0 && (
                    <div>
                        <strong>Prerequisites:</strong>
                        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                            {prerequisites.map((prereq, i) => (
                                <li key={i} style={{ fontSize: '0.875rem' }}>{prereq}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}

function GenericCard({ card }) {
    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: '#f8f9fa'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>📄 {card.type}</h4>
            <pre style={{
                fontSize: '0.875rem',
                color: '#495057',
                overflow: 'auto',
                maxHeight: '200px'
            }}>
                {JSON.stringify(card.payload, null, 2)}
            </pre>
        </div>
    );
}
