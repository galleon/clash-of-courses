const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function fetchJSON(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to fetch ${path}: ${res.status} ${errorText}`);
    }
    return res.json();
}

export async function fetchUsers() {
    return fetchJSON('/users/');
}

export async function createUser(user) {
    const res = await fetch(`${API_BASE}/users/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user),
    });
    if (!res.ok) throw new Error('Failed to create user');
    return res.json();
}

export async function fetchRequests(status) {
    const statusFilter = status ? `?status_filter=${encodeURIComponent(status)}` : '';
    return fetchJSON(`/requests/${statusFilter}`);
}

export async function submitRequest(payload) {
    const res = await fetch(`${API_BASE}/requests/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to submit request');
    return res.json();
}

export async function decideRequest(requestId, payload) {
    const res = await fetch(`${API_BASE}/requests/${requestId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to submit decision');
    return res.json();
}

export async function sendChatMessage(payload) {
    const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to send chat message');
    return res.json();
}

export async function fetchCourses() {
    return fetchJSON('/courses/');
}

export async function fetchCourseSections(courseId) {
    return fetchJSON(`/courses/${courseId}/sections`);
}

export async function fetchStudentEnrolledCourses(studentId) {
    return fetchJSON(`/students/${studentId}/enrolled_courses`);
}

export async function checkSystemHealth() {
    return fetchJSON('/health');
}
