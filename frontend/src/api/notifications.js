import apiFetch from './auth';

export const notificationsApi = {
  getNotifications: () => apiFetch('/api/notifications/'),
  
  getUnreadCount: () => apiFetch('/api/notifications/unread-count/'),
  
  markAsRead: (id) => apiFetch(`/api/notifications/${id}/read/`, {
    method: 'POST'
  }),
  
  markAllAsRead: () => apiFetch('/api/notifications/mark-all-read/', {
    method: 'POST'
  })
};
