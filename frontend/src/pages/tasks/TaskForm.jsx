import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Input, Button, Spinner } from '../../components/ui';
import { tasksApi } from '../../api/tasks';
import { teamsApi } from '../../api/teams';
import { ArrowLeft, Save, Trash2 } from 'lucide-react';

export const TaskForm = () => {
  const { id } = useParams();
  const isEditMode = !!id;
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    team: '',
    assignee: '',
    due_date: ''
  });
  
  const [teams, setTeams] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initForm = async () => {
      try {
        const userTeams = await teamsApi.getUserTeams();
        setTeams(userTeams);
        
        if (isEditMode) {
          const taskData = await tasksApi.getTask(id);
          setFormData({
            title: taskData.title,
            description: taskData.description || '',
            team: taskData.team || '',
            assignee: taskData.assignee || '',
            due_date: taskData.due_date ? taskData.due_date.split('T')[0] : ''
          });
          
          if (taskData.team) {
            const members = await teamsApi.getTeamMembers(taskData.team);
            setTeamMembers(members);
          }
        }
      } catch (err) {
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    
    initForm();
  }, [id, isEditMode]);

  const fetchTeamMembers = async (teamId) => {
    if (!teamId) {
      setTeamMembers([]);
      setFormData(prev => ({ ...prev, assignee: '' }));
      return;
    }
    
    try {
      const members = await teamsApi.getTeamMembers(teamId);
      setTeamMembers(members);
      // Reset assignee if they are not in the new team
      if (formData.assignee && !members.some(m => m.id === formData.assignee)) {
        setFormData(prev => ({ ...prev, assignee: '' }));
      }
    } catch (err) {
      console.error("Failed to fetch team members", err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (name === 'team') {
      fetchTeamMembers(value);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.team) {
      setError('Title and Team are required');
      return;
    }
    
    setSaving(true);
    setError(null);
    
    try {
      const payload = {
        ...formData,
        assignee: formData.assignee || null,
        due_date: formData.due_date || null
      };
      
      if (isEditMode) {
        await tasksApi.updateTask(id, payload);
        navigate(`/tasks/${id}`);
      } else {
        const newTask = await tasksApi.createTask(payload);
        navigate(`/tasks/${newTask.id}`);
      }
    } catch (err) {
      setError(err.message || 'Failed to save task');
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
      return;
    }
    
    setDeleting(true);
    try {
      await tasksApi.deleteTask(id);
      navigate('/tasks');
    } catch (err) {
      setError(err.message || 'Failed to delete task');
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
        <h1 className="md-typescale-display-small">{isEditMode ? 'Edit Task' : 'Create New Task'}</h1>
        <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)', marginTop: '8px' }}>
          {isEditMode ? 'Update task details.' : 'Create a new task and assign it to a team member.'}
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
            label="Task Title *"
            name="title"
            value={formData.title}
            onChange={handleChange}
            disabled={saving || deleting}
            placeholder="e.g. Design Landing Page"
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
                placeholder="What needs to be done?"
              />
            </div>
          </div>
          
          <div className="dashboard-content-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: 0 }}>
            <div className="md-input-container">
              <label className="md-input-label">Team *</label>
              <div className="md-input-wrapper">
                <select 
                  name="team" 
                  value={formData.team} 
                  onChange={handleChange} 
                  disabled={saving || deleting}
                  className="md-input"
                  required
                >
                  <option value="">Select a team</option>
                  {teams.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="md-input-container">
              <label className="md-input-label">Assignee</label>
              <div className="md-input-wrapper">
                <select 
                  name="assignee" 
                  value={formData.assignee} 
                  onChange={handleChange} 
                  disabled={saving || deleting || !formData.team}
                  className="md-input"
                >
                  <option value="">Unassigned</option>
                  {teamMembers.map(m => (
                    <option key={m.id} value={m.user}>{m.user_username}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          
          <Input 
            type="date"
            label="Due Date"
            name="due_date"
            value={formData.due_date}
            onChange={handleChange}
            disabled={saving || deleting}
          />
          
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
                {deleting ? 'Deleting...' : 'Delete Task'}
              </Button>
            ) : <div></div>}
            
            <div className="flex-center gap-3">
              <Button type="button" variant="text" onClick={() => navigate(-1)} disabled={saving || deleting}>
                Cancel
              </Button>
              <Button type="submit" variant="filled" disabled={saving || deleting || !formData.title.trim() || !formData.team} icon={<Save size={18} />}>
                {saving ? 'Saving...' : 'Save Task'}
              </Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
};
