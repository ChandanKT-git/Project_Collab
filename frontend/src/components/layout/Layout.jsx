import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, LayoutDashboard, CheckSquare, Users, Bell } from 'lucide-react';
import { Button } from '../ui';
import './layout.css';

export const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/tasks', label: 'Tasks', icon: <CheckSquare size={20} /> },
    { path: '/teams', label: 'Teams', icon: <Users size={20} /> },
    { path: '/notifications', label: 'Notifications', icon: <Bell size={20} /> },
  ];

  return (
    <div className="md-layout">
      {/* App Bar */}
      <header className="md-app-bar md-surface-container">
        <div className="md-app-bar__brand">
          <span className="md-app-bar__title md-typescale-title-large">CollabHub</span>
        </div>
        
        {user && (
          <div className="md-app-bar__actions flex-center gap-4">
            <span className="md-typescale-label-large">Hello, {user.username}</span>
            <Button variant="text" icon={<LogOut size={18} />} onClick={handleLogout}>
              Logout
            </Button>
          </div>
        )}
      </header>

      <div className="md-layout__main">
        {/* Navigation Rail / Sidebar */}
        {user && (
          <nav className="md-nav-rail md-surface-container-low">
            <div className="md-nav-rail__items">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path || 
                               (item.path !== '/' && location.pathname.startsWith(item.path));
                
                return (
                  <Link 
                    key={item.path} 
                    to={item.path} 
                    className={`md-nav-rail__item ${isActive ? 'md-nav-rail__item--active' : ''}`}
                  >
                    <div className="md-nav-rail__icon-container state-layer">
                      {item.icon}
                    </div>
                    <span className="md-nav-rail__label md-typescale-label-medium">
                      {item.label}
                    </span>
                  </Link>
                );
              })}
            </div>
          </nav>
        )}

        {/* Main Content Area */}
        <main className={`md-main-content ${!user ? 'md-main-content--full' : ''}`}>
          <div className="md-main-content__inner animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
