import React, { useState } from 'react';
import WeekCalendar from './WeekCalendar.jsx';
import CourseCatalogCard from './CourseCatalogCard.jsx';

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
            return <WeekCalendar {...card.payload} />;
        case 'request_summary':
            return <RequestSummaryCard {...card.payload} />;
        case 'alternatives':
            return <AlternativesCard {...card.payload} />;
        case 'course_info':
            return <CourseInfoCard {...card.payload} />;
        case 'course_catalog':
            return <CourseCatalogCard {...card.payload} />;
        case 'prerequisite_tree':
            return <PrerequisiteTreeCard {...card.payload} />;
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

function WeekGridCard({ student_name, total_credits, courses }) {
    const timeSlots = ['8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];
    // Changed to Sunday-Thursday week with 3-letter day names (Arabic locale pattern)
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu'];
    const fullDayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];

    // State for tooltip
    const [tooltip, setTooltip] = React.useState({ show: false, content: null, x: 0, y: 0 });

    // Helper function to format time display
    const formatTimeDisplay = (timeStr) => {
        if (!timeStr) return '';
        // If it's a full datetime, extract just the time part
        let time = timeStr.includes(' ') ? timeStr.split(' ')[1] : timeStr;
        // Return just HH:MM (remove seconds)
        return time.substring(0, 5);
    };

    // Convert course time_slots to the grid format
    const gridData = {};
    fullDayNames.forEach(day => {
        gridData[day] = {};
    });

    // Process each course and place it in the grid
    if (courses) {
        courses.forEach(course => {
            if (course.time_slots) {
                course.time_slots.forEach(slot => {
                    // Convert day_of_week integer to day name
                    // Backend sends: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
                    const dayName = fullDayNames[slot.day_of_week];

                    if (slot.start_time && slot.end_time && dayName && gridData[dayName]) {
                        // Extract time from full datetime format (e.g., "2025-01-01 10:00:00" -> "10:00")
                        let startTime = slot.start_time;
                        let endTime = slot.end_time;

                        // If it's a full datetime, extract just the time part
                        if (startTime.includes(' ')) {
                            startTime = startTime.split(' ')[1]; // Get "10:00:00" part
                        }
                        if (endTime.includes(' ')) {
                            endTime = endTime.split(' ')[1]; // Get "11:15:00" part
                        }

                        // Convert time format (e.g., "10:00:00" -> "10:00")
                        const startHour = parseInt(startTime.split(':')[0]);
                        const timeKey = startHour + ':00';

                        // Debug: Processing slot information
                        // console.log(`Processing slot: day_of_week=${slot.day_of_week}, dayName=${dayName}, startTime=${startTime}, startHour=${startHour}, timeKey=${timeKey}`);

                        if (timeSlots.includes(timeKey)) {
                            gridData[dayName][timeKey] = {
                                course: `${course.course_code} - ${course.section}`,
                                title: course.title,
                                room: slot.room || 'TBA',
                                instructor: course.instructor,
                                activity: slot.activity,
                                start_time: startTime,
                                end_time: endTime,
                                credits: course.credits
                            };
                            // console.log(`Added course to grid: ${timeKey} on ${dayName}`);
                        } else {
                            // console.log(`Time slot ${timeKey} not found in available slots`);
                        }
                    }
                });
            }
        });
    }

    const handleMouseEnter = (event, courseSlot) => {
        const rect = event.target.getBoundingClientRect();
        setTooltip({
            show: true,
            content: courseSlot,
            x: rect.left + rect.width / 2,
            y: rect.top - 10
        });
    };

    const handleMouseLeave = () => {
        setTooltip({ show: false, content: null, x: 0, y: 0 });
    };

    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white',
            position: 'relative'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>📊 Weekly Schedule</h4>
            {student_name && (
                <p style={{ margin: '0 0 1rem 0', color: '#6c757d' }}>
                    Student: {student_name} | Total Credits: {total_credits}
                </p>
            )}
            <div style={{ overflowX: 'auto' }}>
                <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '0.875rem',
                    tableLayout: 'fixed' // Fixed layout for consistent column widths
                }}>
                    <thead>
                        <tr>
                            <th style={{
                                padding: '0.5rem',
                                border: '1px solid #dee2e6',
                                backgroundColor: '#f8f9fa',
                                width: '80px' // Fixed width for time column
                            }}>Time</th>
                            {dayNames.map((day, index) => (
                                <th key={day} style={{
                                    padding: '0.5rem',
                                    border: '1px solid #dee2e6',
                                    backgroundColor: '#f8f9fa',
                                    width: '120px', // Fixed width for day columns
                                    textAlign: 'center'
                                }}>
                                    {day}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {timeSlots.map(time => (
                            <tr key={time}>
                                <td style={{
                                    padding: '0.5rem',
                                    border: '1px solid #dee2e6',
                                    fontWeight: '500',
                                    textAlign: 'center'
                                }}>{time}</td>
                                {fullDayNames.map((day, index) => {
                                    const courseSlot = gridData[day][time];

                                    return (
                                        <td key={day} style={{
                                            padding: '0.25rem',
                                            border: '1px solid #dee2e6',
                                            backgroundColor: courseSlot ? '#e3f2fd' : 'white',
                                            fontSize: '0.75rem',
                                            minHeight: '60px',
                                            verticalAlign: 'top',
                                            position: 'relative',
                                            width: '120px' // Fixed width for consistency
                                        }}>
                                            {courseSlot && (
                                                <div
                                                    style={{
                                                        background: 'linear-gradient(135deg, #2196f3, #1976d2)',
                                                        color: 'white',
                                                        padding: '0.5rem',
                                                        borderRadius: '6px',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s ease',
                                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                                        height: '100%',
                                                        minHeight: '50px'
                                                    }}
                                                    onMouseEnter={(e) => handleMouseEnter(e, courseSlot)}
                                                    onMouseLeave={handleMouseLeave}
                                                    onMouseOver={(e) => {
                                                        e.target.style.transform = 'scale(1.02)';
                                                        e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
                                                    }}
                                                    onMouseOut={(e) => {
                                                        e.target.style.transform = 'scale(1)';
                                                        e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                                    }}
                                                >
                                                    <div style={{ fontWeight: '600', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                                                        {courseSlot.course}
                                                    </div>
                                                    <div style={{ fontSize: '0.7rem', opacity: 0.9 }}>
                                                        {courseSlot.activity}
                                                    </div>
                                                    <div style={{ fontSize: '0.65rem', opacity: 0.8, marginTop: '0.25rem' }}>
                                                        {formatTimeDisplay(courseSlot.start_time)} - {formatTimeDisplay(courseSlot.end_time)}
                                                    </div>
                                                </div>
                                            )}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Tooltip */}
            {tooltip.show && tooltip.content && (
                <div style={{
                    position: 'absolute',
                    top: tooltip.y,
                    left: tooltip.x,
                    transform: 'translateX(-50%) translateY(-100%)',
                    backgroundColor: '#333',
                    color: 'white',
                    padding: '0.75rem',
                    borderRadius: '8px',
                    fontSize: '0.875rem',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    zIndex: 1000,
                    maxWidth: '250px',
                    pointerEvents: 'none',
                    border: '1px solid #555'
                }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#60a5fa' }}>
                        {tooltip.content.course}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                        <strong>📚 Course:</strong> {tooltip.content.title}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                        <strong>👨‍🏫 Instructor:</strong> {tooltip.content.instructor}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                        <strong>📍 Room:</strong> {tooltip.content.room}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                        <strong>🏷️ Type:</strong> {tooltip.content.activity}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                        <strong>⏰ Time:</strong> {formatTimeDisplay(tooltip.content.start_time)} - {formatTimeDisplay(tooltip.content.end_time)}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                        <strong>🎓 Credits:</strong> {tooltip.content.credits}
                    </div>

                    {/* Tooltip arrow */}
                    <div style={{
                        position: 'absolute',
                        bottom: '-6px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        width: 0,
                        height: 0,
                        borderLeft: '6px solid transparent',
                        borderRight: '6px solid transparent',
                        borderTop: '6px solid #333'
                    }} />
                </div>
            )}
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

function AlternativesCard({
    alternatives = [],
    conflict_detected = false,
    requested_section = "",
    alternative_used = "",
    conflict_reason = "",
    resolution_message = "",
    request_details = null
}) {
    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white'
        }}>
            {conflict_detected ? (
                <div>
                    <h4 style={{ marginTop: 0, color: '#856404' }}>⚠️ Schedule Conflict Resolved</h4>

                    {/* Conflict explanation */}
                    <div style={{
                        padding: '0.75rem',
                        backgroundColor: '#fff3cd',
                        border: '1px solid #ffeaa7',
                        borderRadius: '6px',
                        marginBottom: '1rem'
                    }}>
                        <div style={{ fontSize: '0.9rem', color: '#856404' }}>
                            <strong>Requested:</strong> {requested_section}
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#6c757d', marginTop: '0.25rem' }}>
                            {conflict_reason}
                        </div>
                    </div>

                    {/* Resolution */}
                    {alternative_used && (
                        <div style={{
                            padding: '0.75rem',
                            backgroundColor: '#d4edda',
                            border: '1px solid #c3e6cb',
                            borderRadius: '6px',
                            marginBottom: '1rem'
                        }}>
                            <div style={{ fontSize: '0.9rem', color: '#155724' }}>
                                <strong>Automatic Resolution:</strong> Registered for {alternative_used} instead
                            </div>
                            {request_details && (
                                <div style={{ fontSize: '0.85rem', color: '#6c757d', marginTop: '0.25rem' }}>
                                    Request ID: {request_details.request_id}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Resolution message */}
                    {resolution_message && (
                        <div style={{
                            fontSize: '0.9rem',
                            color: '#495057',
                            marginBottom: '1rem',
                            lineHeight: '1.4'
                        }}>
                            {resolution_message}
                        </div>
                    )}
                </div>
            ) : (
                <h4 style={{ marginTop: 0, color: '#495057' }}>🔄 Alternative Options</h4>
            )}

            {/* Available alternatives */}
            {alternatives.length > 0 && (
                <div>
                    <h5 style={{ color: '#495057', marginBottom: '0.75rem' }}>
                        {conflict_detected ? 'Other Available Options:' : 'Available Alternatives:'}
                    </h5>
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
                </div>
            )}

            {!conflict_detected && alternatives.length === 0 && (
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

function PrerequisiteTreeCard({ course, prerequisites, dependents }) {
    const renderPrereqNode = (node, level = 0) => {
        const indent = level * 20;
        const isCompleted = node.status === 'completed';
        const isAvailable = node.status === 'available';

        return (
            <div key={node.course_code} style={{
                marginLeft: `${indent}px`,
                padding: '0.5rem',
                margin: '0.25rem 0',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                backgroundColor: isCompleted ? '#d4edda' : isAvailable ? '#fff3cd' : '#f8d7da',
                borderLeft: `4px solid ${isCompleted ? '#28a745' : isAvailable ? '#ffc107' : '#dc3545'}`
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.2em' }}>
                        {isCompleted ? '✅' : isAvailable ? '⏳' : '🔒'}
                    </span>
                    <div>
                        <strong>{node.course_code}</strong> - {node.course_title}
                        <br />
                        <small style={{ color: '#6c757d' }}>
                            Status: {node.status} | Credits: {node.credits}
                        </small>
                    </div>
                </div>
                {node.prerequisites && node.prerequisites.length > 0 && (
                    <div style={{ marginTop: '0.5rem' }}>
                        {node.prerequisites.map(prereq => renderPrereqNode(prereq, level + 1))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: 'white'
        }}>
            <h4 style={{ marginTop: 0, color: '#495057' }}>🌳 Course Prerequisites</h4>

            {course && (
                <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
                    <h5 style={{ margin: 0, color: '#1976d2' }}>Target Course</h5>
                    <strong>{course.code}</strong> - {course.title}
                    <br />
                    <small>Credits: {course.credits}</small>
                </div>
            )}

            {prerequisites && prerequisites.length > 0 ? (
                <div>
                    <h6 style={{ color: '#495057', marginBottom: '0.5rem' }}>Prerequisites Required:</h6>
                    {prerequisites.map(prereq => renderPrereqNode(prereq))}
                </div>
            ) : (
                <p style={{ color: '#6c757d', fontStyle: 'italic' }}>No prerequisites required</p>
            )}

            {dependents && dependents.length > 0 && (
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #dee2e6' }}>
                    <h6 style={{ color: '#495057', marginBottom: '0.5rem' }}>Unlocks these courses:</h6>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {dependents.map(dep => (
                            <span key={dep.course_code} style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#e7f3ff',
                                border: '1px solid #b3d7ff',
                                borderRadius: '12px',
                                fontSize: '0.875rem',
                                color: '#0056b3'
                            }}>
                                {dep.course_code} - {dep.course_title}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6c757d' }}>
                <strong>Legend:</strong> ✅ Completed | ⏳ Available | 🔒 Prerequisite Required
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
