import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotFound } from './pages/NotFound';
import { Layout } from './components/layout';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { TeamList, TeamDetail, TeamForm } from './pages/teams';
import { TaskList, TaskDetail, TaskForm } from './pages/tasks';
import { NotificationList } from './pages/notifications';
import { Spinner } from './components/ui';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div className="flex-center" style={{height: '100vh'}}><Spinner size="large" /></div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// App Content with Routing
const AppContent = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      
      {/* Protected Routes wrapped in Layout */}
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        
        {/* Teams Routes */}
        <Route path="teams">
          <Route index element={<TeamList />} />
          <Route path="new" element={<TeamForm />} />
          <Route path=":id" element={<TeamDetail />} />
          <Route path=":id/edit" element={<TeamForm />} />
        </Route>
        
        {/* Tasks Routes */}
        <Route path="tasks">
          <Route index element={<TaskList />} />
          <Route path="new" element={<TaskForm />} />
          <Route path=":id" element={<TaskDetail />} />
          <Route path=":id/edit" element={<TaskForm />} />
        </Route>
        
        {/* Notifications Route */}
        <Route path="notifications" element={<NotificationList />} />
      </Route>
      
      {/* Catch all */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;
