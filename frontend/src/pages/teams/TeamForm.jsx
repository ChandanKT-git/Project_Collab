import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Input, Button, Spinner } from '../../components/ui';
import { teamsApi } from '../../api/teams';
import { ArrowLeft, Save, Trash2 } from 'lucide-react';

export const TeamForm = () => {
  const { id } = useParams();
  const isEditMode = !!id;
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  
  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isEditMode) {
      const fetchTeam = async () => {
        try {
          const data = await teamsApi.getTeam(id);
          setFormData({
            name: data.name,
            description: data.description || ''
          });
        } catch (err) {
          setError(err.message || 'Failed to load team details');
        } finally {
          setLoading(false);
        }
      };
      
      fetchTeam();
    }
  }, [id, isEditMode]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    
    setSaving(true);
    setError(null);
    
    try {
      if (isEditMode) {
        await teamsApi.updateTeam(id, formData);
        navigate(`/teams/${id}`);
      } else {
        const newTeam = await teamsApi.createTeam(formData);
        navigate(`/teams/${newTeam.id}`);
      }
    } catch (err) {
      setError(err.message || 'Failed to save team');
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this team? This action cannot be undone.')) {
      return;
    }
    
    setDeleting(true);
    try {
      await teamsApi.deleteTeam(id);
      navigate('/teams');
    } catch (err) {
      setError(err.message || 'Failed to delete team');
      setDeleting(false);
    }
  };

  if (loading) return <div className="flex-center" style={{ height: '50vh' }}><Spinner size="large" /></div>;

  return (
    <div className="page-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Button variant="text" icon={<ArrowLeft size={18} />} onClick={() => navigate(-1)} style={{ marginBottom: '24px', marginLeft: '-12px' }}>
        Back
      </Button>
      
      <div style={{ marginBottom: '32px' }}>
        <h1 className="md-typescale-display-small">{isEditMode ? 'Edit Team' : 'Create New Team'}</h1>
        <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)', marginTop: '8px' }}>
          {isEditMode ? 'Update your team details.' : 'Start collaborating by creating a new team.'}
        </p>
      </div>

      {error && (
        <div style={{ padding: '16px', backgroundColor: 'var(--md-error-container)', color: 'var(--md-on-error-container)', borderRadius: 'var(--md-shape-small)', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      <Card variant="outlined">
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <Input 
            label="Team Name *"
            name="name"
            value={formData.name}
            onChange={handleChange}
            disabled={saving || deleting}
            placeholder="e.g. Engineering Team"
            required
          />
          
          <div className="md-input-container">
            <label className="md-input-label">Description</label>
            <div className="md-input-wrapper" style={{ height: 'auto', padding: '0' }}>
              <textarea 
                name="description"
                value={formData.description}
                onChange={handleChange}
                disabled={saving || deleting}
                className="md-input"
                style={{ height: '120px', resize: 'vertical' }}
                placeholder="What is this team for?"
              />
            </div>
          </div>
          
          <div className="flex-between" style={{ marginTop: '16px' }}>
            {isEditMode ? (
              <Button 
                type="button" 
                variant="outlined" 
                color="error" 
                onClick={handleDelete}
                disabled={saving || deleting}
                icon={<Trash2 size={18} />}
              >
                {deleting ? 'Deleting...' : 'Delete Team'}
              </Button>
            ) : <div></div>}
            
            <div className="flex-center gap-3">
              <Button type="button" variant="text" onClick={() => navigate(-1)} disabled={saving || deleting}>
                Cancel
              </Button>
              <Button type="submit" variant="filled" disabled={saving || deleting || !formData.name.trim()} icon={<Save size={18} />}>
                {saving ? 'Saving...' : 'Save Team'}
              </Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
};
