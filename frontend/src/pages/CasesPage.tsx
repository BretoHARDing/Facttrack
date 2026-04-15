import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { casesApi } from '../api/client';
import type { Case } from '../types';

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    casesApi.list().then(r => setCases(r.data)).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    const { data } = await casesApi.create(newName.trim());
    setCases(prev => [data, ...prev]);
    setNewName('');
    setCreating(false);
  };

  if (loading) return <p>Loading cases…</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0 }}>Cases</h2>
        <button onClick={() => setCreating(!creating)}>+ New case</button>
      </div>

      {creating && (
        <form onSubmit={handleCreate} style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="Case name"
            required
            style={{ flex: 1 }}
          />
          <button type="submit">Create</button>
          <button type="button" onClick={() => setCreating(false)}>Cancel</button>
        </form>
      )}

      {cases.length === 0 && <p>No cases yet. Create one to get started.</p>}

      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {cases.map(c => (
          <li key={c.id} style={{ borderBottom: '1px solid #eee', padding: '0.75rem 0' }}>
            <Link to={`/cases/${c.id}`} style={{ fontWeight: 600 }}>{c.name}</Link>
            <span style={{ marginLeft: '1rem', fontSize: '0.8rem', color: '#888' }}>{c.status}</span>
            <br />
            <small style={{ color: '#aaa' }}>Created {new Date(c.created_at).toLocaleDateString()}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
