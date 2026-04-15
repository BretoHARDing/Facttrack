import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { casesApi, evidenceApi } from '../api/client';
import type { Case, Evidence, PaginatedResponse } from '../types';

export default function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [total, setTotal] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!caseId) return;
    casesApi.get(caseId).then(r => setCaseData(r.data));
    evidenceApi.list(caseId).then(r => {
      const data = r.data as PaginatedResponse<Evidence>;
      setEvidence(data.items);
      setTotal(data.total);
    });
  }, [caseId]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file || !caseId) return;
    setUploading(true);
    setUploadError('');
    try {
      const { data } = await evidenceApi.upload(caseId, file);
      setEvidence(prev => [data, ...prev]);
      setTotal(t => t + 1);
      if (fileRef.current) fileRef.current.value = '';
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setUploadError(msg ?? 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  if (!caseData) return <p>Loading…</p>;

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/cases">← Cases</Link>
      </div>
      <h2>{caseData.name}</h2>
      {caseData.description && <p>{caseData.description}</p>}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <Link to={`/cases/${caseId}/audit`}>View audit log</Link>
      </div>

      <h3>Evidence ({total})</h3>
      <form onSubmit={handleUpload} style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input type="file" ref={fileRef} required />
        <button type="submit" disabled={uploading}>{uploading ? 'Uploading…' : 'Upload'}</button>
      </form>
      {uploadError && <p style={{ color: 'red' }}>{uploadError}</p>}

      {evidence.length === 0 && <p>No evidence uploaded yet.</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {evidence.map(ev => (
          <li key={ev.id} style={{ borderBottom: '1px solid #eee', padding: '0.75rem 0' }}>
            <Link to={`/cases/${caseId}/evidence/${ev.id}`} style={{ fontWeight: 600 }}>
              {ev.original_filename}
            </Link>
            <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: '#888' }}>{ev.status}</span>
            <br />
            <small style={{ color: '#aaa', fontFamily: 'monospace' }}>SHA-256: {ev.sha256_hash.slice(0, 16)}…</small>
            <small style={{ marginLeft: '1rem', color: '#aaa' }}>{(ev.file_size / 1024).toFixed(1)} KB</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
