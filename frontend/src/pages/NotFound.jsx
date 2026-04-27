import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui';
import { Home } from 'lucide-react';

export const NotFound = () => {
  const navigate = useNavigate();
  
  return (
    <div className="flex-center" style={{ minHeight: '100vh', flexDirection: 'column', gap: '24px', textAlign: 'center', padding: '24px' }}>
      <h1 className="md-typescale-display-large" style={{ color: 'var(--md-primary)', fontSize: '120px', margin: 0 }}>404</h1>
      <h2 className="md-typescale-display-small">Page Not Found</h2>
      <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)', maxWidth: '400px' }}>
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button 
        variant="filled" 
        size="large" 
        icon={<Home size={20} />} 
        onClick={() => navigate('/')}
        style={{ marginTop: '16px' }}
      >
        Back to Dashboard
      </Button>
    </div>
  );
};
