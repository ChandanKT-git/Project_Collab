import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Button, Badge, Spinner } from '../../components/ui';
import { teamsApi } from '../../api/teams';
import { Users, Plus, Edit } from 'lucide-react';

export const TeamList = () => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const data = await teamsApi.getTeams();
        setTeams(data);
      } catch (err) {
        setError(err.message || 'Failed to load teams');
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  if (loading) {
    return <div className="flex-center" style={{ height: '50vh' }}><Spinner size="large" /></div>;
  }

  if (error) {
    return <div className="md-typescale-body-large" style={{ color: 'var(--md-error)' }}>{error}</div>;
  }

  return (
    <div className="page-container">
      <div className="page-header flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 className="md-typescale-display-small">Teams</h1>
          <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)' }}>
            Manage your teams and collaborations
          </p>
        </div>
        <Button 
          icon={<Plus size={20} />} 
          onClick={() => navigate('/teams/new')}
        >
          Create Team
        </Button>
      </div>

      {teams.length === 0 ? (
        <Card variant="outlined" className="flex-center" style={{ padding: '48px', flexDirection: 'column', gap: '16px' }}>
          <Users size={48} color="var(--md-on-surface-variant)" />
          <h2 className="md-typescale-headline-small">No teams found</h2>
          <p className="md-typescale-body-medium">You don't belong to any teams yet.</p>
          <Button variant="tonal" onClick={() => navigate('/teams/new')}>Create your first team</Button>
        </Card>
      ) : (
        <div className="dashboard-stats-grid">
          {teams.map(team => (
            <Card key={team.id} variant="elevated" interactive onClick={() => navigate(`/teams/${team.id}`)}>
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' }}>
                <div className="flex-between">
                  <h3 className="md-typescale-title-large">{team.name}</h3>
                  <Badge variant={team.my_role === 'owner' ? 'status-inprogress' : 'assist'}>
                    {team.my_role === 'owner' ? 'Owner' : 'Member'}
                  </Badge>
                </div>
                
                <p className="md-typescale-body-medium" style={{ color: 'var(--md-on-surface-variant)', flex: 1 }}>
                  {team.description || 'No description provided.'}
                </p>
                
                <div className="flex-between" style={{ borderTop: '1px solid var(--md-outline-variant)', paddingTop: '16px', marginTop: 'auto' }}>
                  <div className="flex-center gap-2" style={{ color: 'var(--md-on-surface-variant)' }}>
                    <Users size={16} />
                    <span className="md-typescale-label-medium">{team.members_count} members</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
