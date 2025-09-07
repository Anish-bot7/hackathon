import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../Authcontext';
import "../styles/styles.css";

const Navbar = () => {
  const { user, userType, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
<nav className="navbar">
      <Link to="/" className="navbar-logo">
        📦 SMART SUPPLY CHAIN
      </Link>

      <div className="in">
        {isAuthenticated ? (
          <>
            <span className="navbar-user-info">
              {user?.name} ({userType})
            </span>
            <Link
              to={userType === 'retailer' ? '/retailer-dashboard' : '/warehouse-dashboard'}
              className="navbar-dashboard-btn"
            >
              Dashboard
            </Link>
            <button onClick={handleLogout} className="navbar-logout-btn">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="navbar-dashboard-btn ">
              Login
            </Link>
            <Link to="/register" className="navbar-dashboard-btn ">
              Register
            </Link>
          </>
        )}
      </div>
  
</nav>

  );
};

export default Navbar;