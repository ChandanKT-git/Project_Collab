import React, { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, Input, Button } from '../components/ui';
import { LogIn } from 'lucide-react';
import './pages.css';

export const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // If already authenticated, redirect to dashboard
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setIsSubmitting(true);
    
    if (!username || !password) {
      setLocalError('Please enter both username and password.');
      setIsSubmitting(false);
      return;
    }

    const result = await login(username, password);
    
    if (result.success) {
      navigate('/');
    } else {
      setLocalError(result.error || 'Invalid credentials');
    }
    
    setIsSubmitting(false);
  };

  return (
    <div className="md-page-container flex-center">
      <Card variant="elevated" className="login-card">
        <div className="login-header">
          <h1 className="md-typescale-headline-medium login-title">Welcome back</h1>
          <p className="md-typescale-body-large login-subtitle">Sign in to CollabHub</p>
        </div>
        
        {localError && (
          <div className="login-error-alert md-typescale-body-medium">
            {localError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <Input 
            label="Username" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isSubmitting}
            autoComplete="username"
          />
          
          <Input 
            label="Password" 
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
            autoComplete="current-password"
          />
          
          <Button 
            type="submit" 
            variant="filled" 
            size="large" 
            disabled={isSubmitting}
            icon={<LogIn size={20} />}
            className="login-submit-btn"
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
        
        <div className="login-footer">
          <p className="md-typescale-body-medium">
            Don't have an account? <Link to="/signup">Sign up</Link>
          </p>
        </div>
      </Card>
    </div>
  );
};
