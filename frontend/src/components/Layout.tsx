import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', minHeight: '100vh' }}>
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 1.5rem', height: '3rem',
        background: '#1a1a2e', color: '#fff'
      }}>
        <Link to="/cases" style={{ color: '#fff', textDecoration: 'none', fontWeight: 700, letterSpacing: '0.05em' }}>
          FACTTRACK
        </Link>
        <span style={{ fontSize: '0.875rem' }}>
          {user?.email}&nbsp;
          <button onClick={handleLogout} style={{ marginLeft: '1rem', cursor: 'pointer' }}>
            Logout
          </button>
        </span>
      </nav>
      <main style={{ padding: '1.5rem' }}>
        <Outlet />
      </main>
    </div>
  );
}
