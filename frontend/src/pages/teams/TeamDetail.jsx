import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Badge, Spinner, Input } from '../../components/ui';
import { teamsApi } from '../../api/teams';
import { useAuth } from '../../contexts/AuthContext';
import { Users, Settings, UserMinus, Plus, ArrowLeft } from 'lucide-react';

export const TeamDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [newMemberUsername, setNewMemberUsername] = useState('');
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [addMemberError, setAddMemberError] = useState('');

  const fetchTeam = async () => {
    try {
      const data = await teamsApi.getTeam(id);
      setTeam(data);
    } catch (err) {
      setError(err.message || 'Failed to load team details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeam();
  }, [id]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!newMemberUsername) return;
    
    setIsAddingMember(true);
    setAddMemberError('');
    
    try {
      await teamsApi.addMember(id, newMemberUsername);
      setNewMemberUsername('');
      await fetchTeam(); // Refresh team data
    } catch (err) {
      setAddMemberError(err.message || 'Failed to add member');
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    
    try {
      await teamsApi.removeMember(id, memberId);
      await fetchTeam(); // Refresh
    } catch (err) {
      alert(err.message || 'Failed to remove member');
    }
  };

  if (loading) return <div className="flex-center" style={{ height: '50vh' }}><Spinner size="large" /></div>;
  if (error) return <div className="md-typescale-body-large" style={{ color: 'var(--md-error)' }}>{error}</div>;
  if (!team) return <div>Team not found</div>;

  const isOwner = team.my_role === 'owner';

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header section */}
      <div>
        <Button variant="text" icon={<ArrowLeft size={18} />} onClick={() => navigate('/teams')} style={{ marginBottom: '16px', marginLeft: '-12px' }}>
          Back to Teams
        </Button>
        <div className="flex-between">
          <div>
            <div className="flex-center" style={{ gap: '16px', justifyContent: 'flex-start' }}>
              <h1 className="md-typescale-display-small">{team.name}</h1>
              <Badge variant={isOwner ? 'status-inprogress' : 'assist'}>{isOwner ? 'Owner' : 'Member'}</Badge>
            </div>
            <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)', marginTop: '8px' }}>
              {team.description || 'No description provided.'}
            </p>
          </div>
          {isOwner && (
            <Button variant="outlined" icon={<Settings size={18} />} onClick={() => navigate(`/teams/${id}/edit`)}>
              Settings
            </Button>
          )}
        </div>
      </div>

      <div className="dashboard-content-grid">
        {/* Members List */}
        <Card variant="outlined" style={{ padding: '0', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '24px', borderBottom: '1px solid var(--md-outline-variant)' }} className="flex-between">
            <h2 className="md-typescale-title-large flex-center gap-2">
              <Users size={24} /> Members ({team.members.length})
            </h2>
          </div>
          
          <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {team.members.map(member => (
              <div key={member.id} className="flex-between" style={{ padding: '12px', backgroundColor: 'var(--md-surface-container-lowest)', borderRadius: 'var(--md-shape-small)' }}>
                <div className="flex-center gap-3">
                  <div className="flex-center" style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'var(--md-primary-container)', color: 'var(--md-on-primary-container)', fontWeight: 'bold' }}>
                    {member.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="md-typescale-title-medium">{member.username} {member.id === user?.id ? '(You)' : ''}</div>
                    <div className="md-typescale-body-small" style={{ color: 'var(--md-on-surface-variant)' }}>{member.role}</div>
                  </div>
                </div>
                
                {isOwner && member.role !== 'owner' && (
                  <Button variant="text" color="error" icon={<UserMinus size={18} />} onClick={() => handleRemoveMember(member.id)}>
                    Remove
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Add Member Form / Side Panel */}
        {isOwner && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <Card variant="filled">
              <h3 className="md-typescale-title-large" style={{ marginBottom: '16px' }}>Add Member</h3>
              {addMemberError && (
                <div style={{ color: 'var(--md-error)', marginBottom: '16px', fontSize: '14px' }}>{addMemberError}</div>
              )}
              <form onSubmit={handleAddMember} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <Input 
                  label="Username"
                  placeholder="Enter username"
                  value={newMemberUsername}
                  onChange={(e) => setNewMemberUsername(e.target.value)}
                  disabled={isAddingMember}
                />
                <Button type="submit" disabled={!newMemberUsername || isAddingMember} icon={<Plus size={18} />}>
                  {isAddingMember ? 'Adding...' : 'Add to Team'}
                </Button>
              </form>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
