import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Badge, Spinner, Input } from '../../components/ui';
import { tasksApi } from '../../api/tasks';
import { useAuth } from '../../contexts/AuthContext';
import { ArrowLeft, MessageSquare, Paperclip, Send, Download, FileText, CheckCircle2, Clock, CheckSquare, Circle, Edit } from 'lucide-react';

export const TaskDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [commentText, setCommentText] = useState('');
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  
  const [uploadFile, setUploadFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const fetchTask = async () => {
    try {
      const data = await tasksApi.getTask(id);
      setTask(data);
    } catch (err) {
      setError(err.message || 'Failed to load task details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTask();
  }, [id]);

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    
    setIsSubmittingComment(true);
    try {
      await tasksApi.addComment(id, commentText);
      setCommentText('');
      await fetchTask();
    } catch (err) {
      alert(err.message || 'Failed to add comment');
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    
    setIsUploading(true);
    try {
      await tasksApi.uploadFile(id, uploadFile);
      setUploadFile(null);
      // Reset input file element if needed
      document.getElementById('file-upload').value = '';
      await fetchTask();
    } catch (err) {
      alert(err.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await tasksApi.updateTask(id, { ...task, status: newStatus });
      await fetchTask();
    } catch (err) {
      alert(err.message || 'Failed to update status');
    }
  };

  if (loading) return <div className="flex-center" style={{ height: '50vh' }}><Spinner size="large" /></div>;
  if (error) return <div className="md-typescale-body-large" style={{ color: 'var(--md-error)' }}>{error}</div>;
  if (!task) return <div>Task not found</div>;

  const isAssignee = task.assignee === user?.id;

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'status-done';
      case 'in_progress': return 'status-inprogress';
      case 'review': return 'status-review';
      default: return 'status-todo';
    }
  };

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <Button variant="text" icon={<ArrowLeft size={18} />} onClick={() => navigate(-1)} style={{ marginBottom: '16px', marginLeft: '-12px' }}>
          Back
        </Button>
        <div className="flex-between">
          <div>
            <div className="flex-center" style={{ gap: '16px', justifyContent: 'flex-start' }}>
              <h1 className="md-typescale-display-small" style={{ textDecoration: task.status === 'completed' ? 'line-through' : 'none', opacity: task.status === 'completed' ? 0.7 : 1 }}>
                {task.title}
              </h1>
              <Badge variant={getStatusColor(task.status)}>
                {task.status.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
              </Badge>
            </div>
            <div className="flex-center gap-4" style={{ marginTop: '12px' }}>
              <Badge variant="assist">{task.team_name}</Badge>
              {task.assignee_name && <span className="md-typescale-body-medium">Assignee: {task.assignee_name}</span>}
              {task.due_date && <span className="md-typescale-body-medium" style={{ color: 'var(--md-error)' }}>Due: {new Date(task.due_date).toLocaleDateString()}</span>}
            </div>
          </div>
          <Button variant="outlined" icon={<Edit size={18} />} onClick={() => navigate(`/tasks/${id}/edit`)}>
            Edit Task
          </Button>
        </div>
        
        <p className="md-typescale-body-large" style={{ marginTop: '24px', whiteSpace: 'pre-wrap' }}>
          {task.description || 'No description provided.'}
        </p>

        {/* Quick Status Toggles */}
        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          {task.status !== 'todo' && <Button variant="tonal" onClick={() => handleStatusChange('todo')}>Mark Todo</Button>}
          {task.status !== 'in_progress' && <Button variant="tonal" onClick={() => handleStatusChange('in_progress')}>Mark In Progress</Button>}
          {task.status !== 'completed' && <Button variant="filled" onClick={() => handleStatusChange('completed')} icon={<CheckCircle2 size={18} />}>Complete Task</Button>}
        </div>
      </div>

      <div className="dashboard-content-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        {/* Comments Section */}
        <Card variant="outlined" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h2 className="md-typescale-title-large flex-center gap-2" style={{ marginBottom: '24px' }}>
            <MessageSquare size={20} /> Comments
          </h2>
          
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
            {task.comments && task.comments.length > 0 ? (
              task.comments.map(comment => (
                <div key={comment.id} style={{ backgroundColor: 'var(--md-surface-container-lowest)', padding: '16px', borderRadius: 'var(--md-shape-medium)' }}>
                  <div className="flex-between" style={{ marginBottom: '8px' }}>
                    <span className="md-typescale-label-large">{comment.author_name}</span>
                    <span className="md-typescale-body-small" style={{ color: 'var(--md-on-surface-variant)' }}>
                      {new Date(comment.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="md-typescale-body-medium">{comment.content}</p>
                </div>
              ))
            ) : (
              <p className="md-typescale-body-medium" style={{ color: 'var(--md-on-surface-variant)' }}>No comments yet.</p>
            )}
          </div>
          
          <form onSubmit={handleAddComment} style={{ display: 'flex', gap: '12px', marginTop: 'auto' }}>
            <div style={{ flex: 1 }}>
              <Input 
                placeholder="Add a comment..."
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                disabled={isSubmittingComment}
              />
            </div>
            <Button type="submit" variant="filled" disabled={!commentText.trim() || isSubmittingComment} icon={<Send size={18} />}>
              Send
            </Button>
          </form>
        </Card>

        {/* Files Section */}
        <Card variant="outlined" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h2 className="md-typescale-title-large flex-center gap-2" style={{ marginBottom: '24px' }}>
            <Paperclip size={20} /> Files
          </h2>
          
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
            {task.files && task.files.length > 0 ? (
              task.files.map(file => (
                <div key={file.id} className="flex-between" style={{ padding: '12px', border: '1px solid var(--md-outline-variant)', borderRadius: 'var(--md-shape-small)' }}>
                  <div className="flex-center gap-3">
                    <FileText size={24} color="var(--md-primary)" />
                    <div>
                      <div className="md-typescale-label-large">{file.file.split('/').pop()}</div>
                      <div className="md-typescale-body-small" style={{ color: 'var(--md-on-surface-variant)' }}>
                        Uploaded by {file.uploaded_by_name}
                      </div>
                    </div>
                  </div>
                  <Button variant="text" icon={<Download size={18} />} onClick={() => window.open(file.file, '_blank')}>
                    Download
                  </Button>
                </div>
              ))
            ) : (
              <p className="md-typescale-body-medium" style={{ color: 'var(--md-on-surface-variant)' }}>No files attached.</p>
            )}
          </div>
          
          <form onSubmit={handleFileUpload} style={{ marginTop: 'auto' }}>
            <div style={{ padding: '16px', backgroundColor: 'var(--md-surface-container-low)', borderRadius: 'var(--md-shape-medium)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <input 
                id="file-upload"
                type="file" 
                onChange={(e) => setUploadFile(e.target.files[0])}
                disabled={isUploading}
                style={{ fontFamily: 'var(--md-font-family)' }}
              />
              <Button type="submit" disabled={!uploadFile || isUploading} icon={<Paperclip size={18} />}>
                {isUploading ? 'Uploading...' : 'Upload File'}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
