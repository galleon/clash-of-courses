import React, { useEffect, useState } from 'react';
import { fetchRequests, decideRequest, fetchUsers } from '../api.js';

export default function AdvisorView({ user }) {
  const [requests, setRequests] = useState([]);
  const [heads, setHeads] = useState([]);
  const [selected, setSelected] = useState(null);
  const [decision, setDecision] = useState({ decision: 'approve', rationale: '', department_head_id: '' });

  useEffect(() => {
    const load = async () => {
      const all = await fetchRequests('pending');
      setRequests(all);
      const users = await fetchUsers();
      setHeads(users.filter((u) => u.role === 'department_head'));
    };
    load().catch(console.error);
  }, [user]);

  const handleDecision = async (e) => {
    e.preventDefault();
    if (!selected) return;
    const payload = {
      advisor_id: user.id,
      decision: decision.decision,
      rationale: decision.rationale,
    };
    if (decision.decision === 'refer') {
      payload.department_head_id = parseInt(decision.department_head_id);
    }
    await decideRequest(selected.id, payload);
    setSelected(null);
    setDecision({ decision: 'approve', rationale: '', department_head_id: '' });
    const all = await fetchRequests('pending');
    setRequests(all);
  };

  return (
    <div>
      <h3>Pending Requests</h3>
      <table border="1" cellPadding="4">
        <thead>
          <tr>
            <th>ID</th>
            <th>Student</th>
            <th>Course</th>
            <th>Type</th>
            <th>Justification</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.student_id}</td>
              <td>{r.course_id}</td>
              <td>{r.request_type}</td>
              <td style={{ maxWidth: '300px', whiteSpace: 'pre-wrap' }}>{r.justification}</td>
              <td>
                <button onClick={() => setSelected(r)}>Review</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {selected && (
        <div style={{ marginTop: '1rem', border: '1px solid #ccc', padding: '1rem' }}>
          <h4>Review Request #{selected.id}</h4>
          <p><strong>Student ID:</strong> {selected.student_id}</p>
          <p><strong>Course ID:</strong> {selected.course_id}</p>
          <p><strong>Type:</strong> {selected.request_type}</p>
          <p><strong>Justification:</strong> {selected.justification}</p>
          <form onSubmit={handleDecision} style={{ display: 'flex', flexDirection: 'column', maxWidth: '400px' }}>
            <label>
              Decision
              <select value={decision.decision} onChange={(e) => setDecision({ ...decision, decision: e.target.value })}>
                <option value="approve">Approve</option>
                <option value="reject">Reject</option>
                <option value="refer">Refer</option>
              </select>
            </label>
            {decision.decision === 'refer' && (
              <label>
                Department Head
                <select
                  value={decision.department_head_id}
                  onChange={(e) => setDecision({ ...decision, department_head_id: e.target.value })}
                  required
                >
                  <option value="" disabled>Select head</option>
                  {heads.map((h) => (
                    <option key={h.id} value={h.id}>{h.full_name}</option>
                  ))}
                </select>
              </label>
            )}
            <label>
              Rationale
              <textarea
                value={decision.rationale}
                onChange={(e) => setDecision({ ...decision, rationale: e.target.value })}
              />
            </label>
            <button type="submit">Submit Decision</button>
            <button type="button" onClick={() => setSelected(null)} style={{ marginTop: '0.5rem' }}>Cancel</button>
          </form>
        </div>
      )}
    </div>
  );
}