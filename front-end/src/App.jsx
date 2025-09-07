import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import RetailerDashboard from './pages/RetailerDashboard';
import WarehouseDashboard from './pages/WarehouseDashboard';
import './App.css';

function ProtectedRoute({ children, requiredType }) {
  const { user, userType, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (requiredType && userType !== requiredType) return <Navigate to="/login" />;
  
  return children;
}

function AppRoutes() {
  const { user, userType } = useAuth();
  
  return (
    <div className="App">
      <Navbar />
      <Routes>
        <Route path="/" element={
          user ? (
            <Navigate to={userType === 'retailer' ? '/retailer-dashboard' : '/warehouse-dashboard'} />
          ) : (
            <Navigate to="/login" />
          )
        } />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/retailer-dashboard" element={
          <ProtectedRoute requiredType="retailer">
            <RetailerDashboard />
          </ProtectedRoute>
        } />
        <Route path="/warehouse-dashboard" element={
          <ProtectedRoute requiredType="warehouse">
            <WarehouseDashboard />
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;