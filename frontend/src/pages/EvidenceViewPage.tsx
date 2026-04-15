import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { evidenceApi } from '../api/client';
import type { Evidence, Artifact } from '../types';

export default function EvidenceViewPage() {
  const { caseId, evidenceId } = useParams<{ caseId: string; evidenceId: string }>();
  const [ev, setEv] = useState<Evidence | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);

  useEffect(() => {
    if (!caseId || !evidenceId) return;
    evidenceApi.get(caseId, evidenceId).then(r => setEv(r.data));
    evidenceApi.getArtifacts(caseId, evidenceId).then(r => setArtifacts(r.data));
  }, [caseId, evidenceId]);

  if (!ev) return <p>Loading…</p>;

  const downloadUrl = evidenceApi.downloadUrl(caseId!, evidenceId!);

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <Link to={`/cases/${caseId}`}>← Back to case</Link>
      </div>
      <h2>{ev.original_filename}</h2>
      <table style={{ borderCollapse: 'collapse', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
        <tbody>
          {[
            ['Status', ev.status],
            ['MIME type', ev.mime_type],
            ['Size', `${(ev.file_size / 1024).toFixed(1)} KB`],
            ['SHA-256', ev.sha256_hash],
            ['Uploaded', new Date(ev.uploaded_at).toLocaleString()],
            ['Parsed', ev.parsed_at ? new Date(ev.parsed_at).toLocaleString() : '—'],
          ].map(([k, v]) => (
            <tr key={k}>
              <td style={{ paddingRight: '1.5rem', fontWeight: 600, color: '#555' }}>{k}</td>
              <td style={{ fontFamily: k === 'SHA-256' ? 'monospace' : 'inherit', wordBreak: 'break-all' }}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <a href={downloadUrl} download style={{ padding: '0.4rem 0.8rem', background: '#1a1a2e', color: '#fff', borderRadius: 4, textDecoration: 'none' }}>
        Download original
      </a>

      {artifacts.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Parsed artifacts</h3>
          {artifacts.map(a => (
            <div key={a.id} style={{ marginBottom: '1.5rem', border: '1px solid #ddd', borderRadius: 4, padding: '1rem' }}>
              <strong>{a.artifact_type}</strong>
              {a.content && (
                <pre style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap', fontSize: '0.85rem', maxHeight: 300, overflow: 'auto' }}>
                  {a.content}
                </pre>
              )}
              {Object.keys(a.metadata_).length > 0 && (
                <pre style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#666' }}>
                  {JSON.stringify(a.metadata_, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
