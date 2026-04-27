import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, Badge, Spinner } from '../components/ui';
import apiFetch from '../api/auth';
import { CheckCircle2, Clock, Users } from 'lucide-react';
import './pages.css';

export const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const data = await apiFetch('/api/dashboard/');
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex-center" style={{ height: '50vh' }}>
        <Spinner size="large" />
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1 className="md-typescale-display-small">Overview</h1>
        <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)' }}>
          Welcome back, {user?.first_name || user?.username}! Here's what's happening.
        </p>
      </div>

      {stats && (
        <div className="dashboard-stats-grid">
          <Card variant="filled" className="stat-card">
            <div className="stat-card-header">
              <CheckCircle2 size={24} color="var(--md-primary)" />
              <h3 className="md-typescale-title-medium">Tasks</h3>
            </div>
            <div className="stat-card-value md-typescale-display-medium">
              {stats.tasks?.total || 0}
            </div>
            <div className="stat-card-footer">
              <Badge variant="assist">{stats.tasks?.completed || 0} completed</Badge>
            </div>
          </Card>

          <Card variant="filled" className="stat-card">
            <div className="stat-card-header">
              <Clock size={24} color="var(--md-tertiary)" />
              <h3 className="md-typescale-title-medium">In Progress</h3>
            </div>
            <div className="stat-card-value md-typescale-display-medium">
              {stats.tasks?.in_progress || 0}
            </div>
          </Card>

          <Card variant="filled" className="stat-card">
            <div className="stat-card-header">
              <Users size={24} color="var(--md-secondary)" />
              <h3 className="md-typescale-title-medium">Teams</h3>
            </div>
            <div className="stat-card-value md-typescale-display-medium">
              {stats.teams?.total || 0}
            </div>
          </Card>
        </div>
      )}
      
      <div className="dashboard-content-grid">
         {/* Placeholder for Recent Tasks and Notifications */}
         <Card variant="outlined" className="dashboard-section">
            <h2 className="md-typescale-title-large" style={{ marginBottom: '16px' }}>Recent Tasks</h2>
            <p className="md-typescale-body-medium">Coming soon: A list of your most recent tasks.</p>
         </Card>
      </div>
    </div>
  );
};
