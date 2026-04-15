import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { auditApi } from '../api/client';
import type { AuditLogEntry, AuditVerifyResult } from '../types';

export default function AuditLogPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyResult, setVerifyResult] = useState<AuditVerifyResult | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    if (!caseId) return;
    auditApi.listForCase(caseId).then(r => setEntries(r.data)).finally(() => setLoading(false));
  }, [caseId]);

  const handleVerify = async () => {
    if (!caseId) return;
    setVerifying(true);
    try {
      const { data } = await auditApi.verifyCase(caseId);
      setVerifyResult(data);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <Link to={`/cases/${caseId}`}>← Back to case</Link>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0 }}>Audit Log</h2>
        <button onClick={handleVerify} disabled={verifying}>
          {verifying ? 'Verifying…' : 'Verify chain'}
        </button>
      </div>

      {verifyResult && (
        <div style={{
          marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: 4,
          background: verifyResult.valid ? '#d4edda' : '#f8d7da',
          color: verifyResult.valid ? '#155724' : '#721c24'
        }}>
          {verifyResult.valid
            ? `✓ Chain valid — ${verifyResult.total_entries} entries verified`
            : `✗ Chain invalid: ${verifyResult.error}`}
        </div>
      )}

      {loading && <p>Loading…</p>}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
            <th style={{ padding: '0.5rem' }}>Timestamp</th>
            <th style={{ padding: '0.5rem' }}>Event</th>
            <th style={{ padding: '0.5rem' }}>Actor</th>
            <th style={{ padding: '0.5rem' }}>Entry hash</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(e => (
            <tr key={e.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '0.5rem', whiteSpace: 'nowrap' }}>
                {new Date(e.created_at).toLocaleString()}
              </td>
              <td style={{ padding: '0.5rem' }}>{e.event_type}</td>
              <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                {e.actor_id ? e.actor_id.slice(0, 8) + '…' : '(system)'}
              </td>
              <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                {e.entry_hash.slice(0, 16)}…
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {entries.length === 0 && !loading && <p>No audit entries yet.</p>}
    </div>
  );
}
