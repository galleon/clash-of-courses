import React from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const localizer = momentLocalizer(moment);

const WeekCalendar = ({ student_name, total_credits, pending_credits = 0, courses }) => {
    // Convert course data to calendar events
    const events = [];

    if (courses) {
        courses.forEach(course => {
            if (course.time_slots) {
                course.time_slots.forEach(slot => {
                    // Backend sends Python weekday: Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
                    // JavaScript Date.getDay(): Sunday=0, Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5, Saturday=6
                    // Convert Python weekday to JavaScript day
                    const pythonWeekday = slot.day_of_week;
                    const jsDay = pythonWeekday === 6 ? 0 : pythonWeekday + 1; // Python Sunday(6) -> JS Sunday(0), others shift +1

                    if (slot.start_time && slot.end_time) {
                        // Create a date for this week
                        const today = new Date();
                        const startOfWeek = moment().startOf('week');
                        const targetDate = startOfWeek.clone().day(jsDay);

                        // Parse time strings
                        let startTime = slot.start_time;
                        let endTime = slot.end_time;

                        // If it's a full datetime, extract just the time part
                        if (startTime.includes(' ')) {
                            startTime = startTime.split(' ')[1];
                        }
                        if (endTime.includes(' ')) {
                            endTime = endTime.split(' ')[1];
                        }

                        // Create start and end datetime objects
                        const [startHour, startMin] = startTime.split(':').map(Number);
                        const [endHour, endMin] = endTime.split(':').map(Number);

                        const startDate = targetDate.clone().hour(startHour).minute(startMin).second(0).toDate();
                        const endDate = targetDate.clone().hour(endHour).minute(endMin).second(0).toDate();

                        events.push({
                            id: `${course.course_code}-${course.section}-${pythonWeekday}`,
                            title: `${course.course_code} ${course.section}${course.status === 'pending' ? ' (Pending)' : ''}`,
                            start: startDate,
                            end: endDate,
                            resource: {
                                course: course.course_code,
                                section: course.section,
                                title: course.title,
                                instructor: course.instructor,
                                room: slot.room || 'TBA',
                                activity: slot.activity || 'Class',
                                credits: course.credits,
                                startTime: startTime,
                                endTime: endTime,
                                status: course.status || 'enrolled'  // Add status to resource
                            }
                        });
                    }
                });
            }
        });
    }

    // Custom event style - different colors for enrolled vs pending
    const eventStyleGetter = (event, start, end, isSelected) => {
        const isPending = event.resource.status === 'pending';
        const backgroundColor = isPending ? '#FFA726' : '#2196F3'; // Orange for pending, blue for enrolled
        const opacity = isPending ? 0.7 : 0.8;

        const style = {
            backgroundColor,
            borderRadius: '4px',
            opacity: opacity,
            color: 'white',
            border: isPending ? '2px dashed #FF8C00' : '0px',
            display: 'block',
            fontSize: '12px',
            padding: '2px 4px'
        };
        return { style };
    };

    // Custom formats to show day names clearly
    const formats = {
        weekdayFormat: (date, culture, localizer) => {
            // Show 3-letter day names: SUN, MON, TUE, WED, THU
            const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
            return dayNames[date.getDay()];
        },
        dayFormat: (date, culture, localizer) => {
            return localizer.format(date, 'DD', culture);
        },
        timeGutterFormat: (date, culture, localizer) => {
            return localizer.format(date, 'HH:mm', culture);
        }
    };

    // Only show Sunday through Thursday (Arabic academic week)
    const dayPropGetter = (date) => {
        const day = date.getDay();
        if (day === 5 || day === 6) { // Friday or Saturday
            return {
                style: {
                    display: 'none'
                }
            };
        }
        return {};
    };

    // Custom event component with better tooltip and status indication
    const EventComponent = ({ event }) => {
        const isPending = event.resource.status === 'pending';
        return (
            <div
                title={`${event.resource.title}${isPending ? ' (PENDING APPROVAL)' : ''}\nTime: ${event.resource.startTime}-${event.resource.endTime}\nInstructor: ${event.resource.instructor}\nRoom: ${event.resource.room}\nActivity: ${event.resource.activity}\nStatus: ${isPending ? 'Pending Approval' : 'Enrolled'}`}
                style={{ height: '100%', padding: '2px' }}
            >
                <div style={{ fontWeight: 'bold', fontSize: '11px' }}>
                    {event.resource.course} {event.resource.section}
                    {isPending && <span style={{ fontSize: '10px' }}> (P)</span>}
                </div>
                <div style={{ fontSize: '10px', opacity: 0.9 }}>
                    {event.resource.room}
                </div>
            </div>
        );
    };

    return (
        <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            margin: '1rem 0',
            width: '100%',
            maxWidth: '1200px'
        }}>
            <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>
                    📅 {student_name}'s Schedule
                </h3>
                <div style={{ fontSize: '14px', color: '#666' }}>
                    <span>Enrolled Credits: {total_credits}</span>
                    {pending_credits > 0 && (
                        <span style={{ marginLeft: '1rem', color: '#FF8C00' }}>
                            Pending Credits: {pending_credits}
                        </span>
                    )}
                </div>
                {pending_credits > 0 && (
                    <div style={{
                        fontSize: '12px',
                        color: '#FF8C00',
                        marginTop: '0.25rem',
                        fontStyle: 'italic'
                    }}>
                        📝 Orange courses with (P) are pending approval
                    </div>
                )}
            </div>            <div style={{ height: '600px', width: '100%', minWidth: '700px', maxWidth: '100%' }}>
                <Calendar
                    localizer={localizer}
                    events={events}
                    startAccessor="start"
                    endAccessor="end"
                    style={{ height: '100%', width: '100%' }}
                    view="week"
                    views={['week']}
                    toolbar={false}
                    formats={formats}
                    eventPropGetter={eventStyleGetter}
                    dayPropGetter={dayPropGetter}
                    components={{
                        event: EventComponent,
                        week: {
                            header: ({ date, localizer }) => {
                                const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
                                return (
                                    <div style={{
                                        textAlign: 'center',
                                        fontWeight: 'bold',
                                        padding: '8px',
                                        backgroundColor: '#f5f5f5',
                                        borderBottom: '1px solid #ddd'
                                    }}>
                                        {dayNames[date.getDay()]}
                                        <br />
                                        <span style={{ fontSize: '12px', fontWeight: 'normal' }}>
                                            {localizer.format(date, 'DD', 'en')}
                                        </span>
                                    </div>
                                );
                            }
                        }
                    }}
                    min={new Date(2025, 0, 1, 8, 0, 0)} // 8:00 AM
                    max={new Date(2025, 0, 1, 18, 0, 0)} // 6:00 PM
                    step={60}
                    timeslots={1}
                    popup={true}
                />
            </div>
        </div>
    );
};

export default WeekCalendar;
