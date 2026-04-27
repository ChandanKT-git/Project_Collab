import apiFetch from './auth';
import { getCookie } from '../utils/csrf';

export const tasksApi = {
  getTasks: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiFetch(`/api/tasks/${query ? `?${query}` : ''}`);
  },
  
  getTask: (id) => apiFetch(`/api/tasks/${id}/`),
  
  createTask: (taskData) => apiFetch('/api/tasks/', {
    method: 'POST',
    body: JSON.stringify(taskData)
  }),
  
  updateTask: (id, taskData) => apiFetch(`/api/tasks/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(taskData)
  }),
  
  deleteTask: (id) => apiFetch(`/api/tasks/${id}/`, {
    method: 'DELETE'
  }),
  
  getStatusChoices: () => apiFetch('/api/tasks/status-choices/'),
  
  addComment: (taskId, content) => apiFetch(`/api/tasks/${taskId}/comments/`, {
    method: 'POST',
    body: JSON.stringify({ content })
  }),
  
  uploadFile: (taskId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // We cannot use the default apiFetch because it forces Content-Type: application/json
    // We need to let the browser set the boundary for multipart/form-data
    const csrfToken = getCookie('csrftoken');
    
    return fetch(`/api/tasks/${taskId}/files/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Accept': 'application/json'
      },
      body: formData
    }).then(res => {
      if (!res.ok) throw new Error('File upload failed');
      return res.json();
    });
  }
};
