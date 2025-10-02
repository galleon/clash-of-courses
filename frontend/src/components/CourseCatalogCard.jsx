import React from 'react';

const CourseCatalogCard = ({ courses, total_count }) => {
    return (
        <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            margin: '1rem 0'
        }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#333' }}>
                📚 Available Courses {total_count ? `(${total_count} courses)` : ''}
            </h3>

            {courses && courses.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {courses.map((course, index) => (
                        <div key={index} style={{
                            border: '1px solid #e0e0e0',
                            borderRadius: '6px',
                            padding: '1rem',
                            backgroundColor: '#fafafa'
                        }}>
                            <div style={{ marginBottom: '0.5rem' }}>
                                <h4 style={{ margin: '0 0 0.25rem 0', color: '#1976d2' }}>
                                    {course.code} - {course.title}
                                </h4>
                                <p style={{ margin: '0', fontSize: '14px', color: '#666' }}>
                                    {course.credits} credit{course.credits !== 1 ? 's' : ''} • {course.description}
                                </p>
                            </div>

                            {course.sections && course.sections.length > 0 && (
                                <div style={{ marginTop: '0.75rem' }}>
                                    <h5 style={{ margin: '0 0 0.5rem 0', color: '#333', fontSize: '14px' }}>
                                        Available Sections:
                                    </h5>
                                    <div style={{ display: 'grid', gap: '0.5rem' }}>
                                        {course.sections.map((section, secIndex) => (
                                            <div key={secIndex} style={{
                                                backgroundColor: 'white',
                                                border: '1px solid #ddd',
                                                borderRadius: '4px',
                                                padding: '0.75rem',
                                                fontSize: '13px'
                                            }}>
                                                <div style={{
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center',
                                                    marginBottom: '0.5rem'
                                                }}>
                                                    <span style={{ fontWeight: 'bold', color: '#1976d2' }}>
                                                        Section {section.section_code}
                                                    </span>
                                                    <span style={{
                                                        color: section.available > 0 ? '#4caf50' : '#f44336',
                                                        fontWeight: 'bold'
                                                    }}>
                                                        {section.available}/{section.capacity} seats
                                                    </span>
                                                </div>

                                                <div style={{ color: '#666', marginBottom: '0.25rem' }}>
                                                    <strong>Instructor:</strong> {section.instructor || 'TBD'}
                                                </div>

                                                {section.meetings && section.meetings.length > 0 && (
                                                    <div style={{ color: '#666' }}>
                                                        <strong>Schedule:</strong>
                                                        <div style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
                                                            {section.meetings.map((meeting, meetIndex) => (
                                                                <div key={meetIndex} style={{ marginBottom: '0.125rem' }}>
                                                                    <span style={{ fontWeight: 'bold', color: '#1976d2' }}>
                                                                        {meeting.day_name || `Day ${meeting.day_of_week}`}
                                                                    </span>
                                                                    {meeting.start_time && meeting.end_time && (
                                                                        <span>: {meeting.start_time} - {meeting.end_time}</span>
                                                                    )}
                                                                    {meeting.room && (
                                                                        <span style={{ color: '#888', marginLeft: '0.5rem' }}>
                                                                            📍 {meeting.room}
                                                                        </span>
                                                                    )}
                                                                    {meeting.activity && meeting.activity !== 'LEC' && (
                                                                        <span style={{ color: '#888', marginLeft: '0.5rem' }}>
                                                                            ({meeting.activity})
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <p style={{ margin: '0', color: '#666' }}>No courses available.</p>
            )}
        </div>
    );
};

export default CourseCatalogCard;
