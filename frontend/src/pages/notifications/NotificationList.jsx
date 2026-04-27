import React, { useEffect, useState } from 'react';
import { Card, Button, Spinner, Badge } from '../../components/ui';
import { notificationsApi } from '../../api/notifications';
import { Bell, Check, CheckCircle2, MessageSquare, AlertCircle } from 'lucide-react';

export const NotificationList = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [markingId, setMarkingId] = useState(null);

  const fetchNotifications = async () => {
    try {
      const data = await notificationsApi.getNotifications();
      setNotifications(data);
    } catch (err) {
      setError(err.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAsRead = async (id) => {
    setMarkingId(id);
    try {
      await notificationsApi.markAsRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error('Failed to mark as read', err);
    } finally {
      setMarkingId(null);
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingId('all');
    try {
      await notificationsApi.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Failed to mark all as read', err);
    } finally {
      setMarkingId(null);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'task_assigned':
      case 'task_status_changed':
        return <CheckCircle2 size={24} color="var(--md-primary)" />;
      case 'new_comment':
        return <MessageSquare size={24} color="var(--md-secondary)" />;
      case 'team_invite':
        return <Bell size={24} color="var(--md-tertiary)" />;
      default:
        return <AlertCircle size={24} color="var(--md-on-surface-variant)" />;
    }
  };

  const hasUnread = notifications.some(n => !n.is_read);

  if (loading) return <div className="flex-center" style={{ height: '50vh' }}><Spinner size="large" /></div>;
  if (error) return <div className="md-typescale-body-large" style={{ color: 'var(--md-error)' }}>{error}</div>;

  return (
    <div className="page-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header flex-between" style={{ marginBottom: '32px' }}>
        <div>
          <h1 className="md-typescale-display-small">Notifications</h1>
          <p className="md-typescale-body-large" style={{ color: 'var(--md-on-surface-variant)', marginTop: '4px' }}>
            Stay updated on your teams and tasks
          </p>
        </div>
        {hasUnread && (
          <Button 
            variant="tonal" 
            onClick={handleMarkAllRead} 
            disabled={markingId === 'all'}
            icon={<Check size={18} />}
          >
            Mark All as Read
          </Button>
        )}
      </div>

      {notifications.length === 0 ? (
        <Card variant="outlined" className="flex-center" style={{ padding: '48px', flexDirection: 'column', gap: '16px' }}>
          <Bell size={48} color="var(--md-on-surface-variant)" />
          <h2 className="md-typescale-headline-small">All caught up!</h2>
          <p className="md-typescale-body-medium">You don't have any notifications right now.</p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {notifications.map(notif => (
            <Card 
              key={notif.id} 
              variant={notif.is_read ? 'outlined' : 'elevated'}
              style={{ 
                padding: '16px 24px', 
                backgroundColor: notif.is_read ? 'transparent' : 'var(--md-surface-container-low)',
                opacity: notif.is_read ? 0.7 : 1
              }}
            >
              <div className="flex-between">
                <div className="flex-center gap-4">
                  {getNotificationIcon(notif.notification_type)}
                  <div>
                    <h3 className="md-typescale-title-medium" style={{ fontWeight: notif.is_read ? 400 : 600 }}>
                      {notif.title}
                    </h3>
                    <p className="md-typescale-body-medium" style={{ color: 'var(--md-on-surface-variant)', marginTop: '4px' }}>
                      {notif.message}
                    </p>
                    <span className="md-typescale-body-small" style={{ color: 'var(--md-on-surface-variant)', display: 'block', marginTop: '8px' }}>
                      {new Date(notif.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                
                {!notif.is_read && (
                  <Button 
                    variant="text" 
                    onClick={() => handleMarkAsRead(notif.id)}
                    disabled={markingId === notif.id}
                  >
                    Mark Read
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
