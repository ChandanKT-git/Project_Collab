import React, { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, Input, Button } from '../components/ui';
import { UserPlus } from 'lucide-react';
import './pages.css';

export const Signup = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [localError, setLocalError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { signup, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // If already authenticated, redirect to dashboard
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setIsSubmitting(true);
    
    if (!formData.username || !formData.email || !formData.password || !formData.confirmPassword) {
      setLocalError('Please fill in all fields.');
      setIsSubmitting(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setLocalError('Passwords do not match.');
      setIsSubmitting(false);
      return;
    }

    const result = await signup({
      username: formData.username,
      email: formData.email,
      password: formData.password
    });
    
    if (result.success) {
      navigate('/');
    } else {
      setLocalError(result.error || 'Signup failed');
    }
    
    setIsSubmitting(false);
  };

  return (
    <div className="md-page-container flex-center">
      <Card variant="elevated" className="login-card">
        <div className="login-header">
          <h1 className="md-typescale-headline-medium login-title">Create Account</h1>
          <p className="md-typescale-body-large login-subtitle">Join CollabHub today</p>
        </div>
        
        {localError && (
          <div className="login-error-alert md-typescale-body-medium">
            {localError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <Input 
            label="Username" 
            name="username"
            value={formData.username}
            onChange={handleChange}
            disabled={isSubmitting}
            autoComplete="username"
          />
          
          <Input 
            label="Email" 
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            disabled={isSubmitting}
            autoComplete="email"
          />

          <Input 
            label="Password" 
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            disabled={isSubmitting}
            autoComplete="new-password"
          />

          <Input 
            label="Confirm Password" 
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            disabled={isSubmitting}
            autoComplete="new-password"
          />
          
          <Button 
            type="submit" 
            variant="filled" 
            size="large" 
            disabled={isSubmitting}
            icon={<UserPlus size={20} />}
            className="login-submit-btn"
          >
            {isSubmitting ? 'Creating account...' : 'Sign up'}
          </Button>
        </form>
        
        <div className="login-footer">
          <p className="md-typescale-body-medium">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </Card>
    </div>
  );
};
