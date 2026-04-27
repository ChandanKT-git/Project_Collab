import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Button, Badge, Spinner, Input } from '../../components/ui';
import { tasksApi } from '../../api/tasks';
import { CheckSquare, Plus, Filter, Clock, CheckCircle2, Circle } from 'lucide-react';

export const TaskList = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, completed
  
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const data = await tasksApi.getTasks();
        setTasks(data);
      } catch (err) {
        setError(err.message || 'Failed to load tasks');
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle2 size={18} color="var(--md-primary)" />;
      case 'in_progress': return <Clock size={18} color="var(--md-tertiary)" />;
      case 'review': return <CheckSquare size={18} color="var(--md-secondary)" />;
      default: return <Circle size={18} color="var(--md-on-surface-variant)" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'status-done';
      case 'in_progress': return 'status-inprogress';
      case 'review': return 'status-review';
      default: return 'status-todo';
    }
  };

  const formatStatus = (status) => {
    return status.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === 'completed') return task.status === 'completed';
    if (filter === 'pending') return task.status !== 'completed';
    return true;
  });

  if (loading) return <div className="flex-center" style={{ height: '50vh' }}><Spinner size="large" /></div>;
  if (error) return <div className="md-typescale-body-large" style={{ color: 'var(--md-error)' }}>{error}</div>;

  return (
    <div className="page-container">
      <div className="page-header flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 className="md-typescale-display-small">Tasks</h1>
          <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)' }}>
            Track and manage your assignments
          </p>
        </div>
        <Button icon={<Plus size={20} />} onClick={() => navigate('/tasks/new')}>
          New Task
        </Button>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        <Badge 
          variant={filter === 'all' ? 'filter' : 'assist'} 
          onClick={() => setFilter('all')}
        >
          All Tasks
        </Badge>
        <Badge 
          variant={filter === 'pending' ? 'filter' : 'assist'} 
          onClick={() => setFilter('pending')}
        >
          Pending
        </Badge>
        <Badge 
          variant={filter === 'completed' ? 'filter' : 'assist'} 
          onClick={() => setFilter('completed')}
        >
          Completed
        </Badge>
      </div>

      {filteredTasks.length === 0 ? (
        <Card variant="outlined" className="flex-center" style={{ padding: '48px', flexDirection: 'column', gap: '16px' }}>
          <CheckSquare size={48} color="var(--md-on-surface-variant)" />
          <h2 className="md-typescale-headline-small">No tasks found</h2>
          <p className="md-typescale-body-medium">You don't have any tasks matching this filter.</p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filteredTasks.map(task => (
            <Card key={task.id} variant="elevated" interactive onClick={() => navigate(`/tasks/${task.id}`)} style={{ padding: '16px 24px' }}>
              <div className="flex-between">
                <div className="flex-center gap-4">
                  {getStatusIcon(task.status)}
                  <div>
                    <h3 className="md-typescale-title-large" style={{ textDecoration: task.status === 'completed' ? 'line-through' : 'none', opacity: task.status === 'completed' ? 0.7 : 1 }}>
                      {task.title}
                    </h3>
                    <div className="flex-center gap-3" style={{ marginTop: '4px' }}>
                      <span className="md-typescale-body-small" style={{ color: 'var(--md-on-surface-variant)' }}>
                        Team: {task.team_name}
                      </span>
                      {task.due_date && (
                        <span className="md-typescale-body-small" style={{ color: 'var(--md-error)' }}>
                          Due: {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <Badge variant={getStatusColor(task.status)}>
                  {formatStatus(task.status)}
                </Badge>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
