import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../Authcontext';
import "../styles/styles.css";

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [userType, setUserType] = useState('retailer');
  const [formData, setFormData] = useState({
    name: '',
    shop_mobile: '',
    mobile: '',
    shop_address: '',
    address: '',
    city: '',
    region: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Trim all string values
    const trimmedData = {};
    Object.keys(formData).forEach((key) => {
      trimmedData[key] = typeof formData[key] === 'string' ? formData[key].trim() : formData[key];
    });

    if (trimmedData.password !== trimmedData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    const registrationData =
      userType === 'retailer'
        ? {
            name: trimmedData.name,
            shop_mobile: trimmedData.shop_mobile,
            shop_address: trimmedData.shop_address,
            city: trimmedData.city,
            region: trimmedData.region,
            password: trimmedData.password
          }
        : {
            name: trimmedData.name,
            mobile: trimmedData.mobile,
            address: trimmedData.address,
            city: trimmedData.city,
            region: trimmedData.region,
            password: trimmedData.password
          };

    try {
      const result = await register(registrationData, userType);

      if (result.success) {
        setSuccess('Registration successful! Redirecting to login...');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(result.message || 'Registration failed');
      }
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h2 className="register-title">Create Account</h2>
        <p className="register-subtitle">Join our supply chain network</p>

        {/* User Type Selection */}
        <div className="mb-6 flex gap-2">
          <button
            type="button"
            className={`user-type-btn ${userType === 'retailer' ? 'active' : ''}`}
            onClick={() => setUserType('retailer')}
          >
            🏪 Retailer
          </button>
          <button
            type="button"
            className={`user-type-btn ${userType === 'warehouse' ? 'active' : ''}`}
            onClick={() => setUserType('warehouse')}
          >
            🏭 Warehouse
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-msg">{error}</div>}
          {success && <div className="success-msg">{success}</div>}

          {/* Name */}
          <input
            className="input-field"
            type="text"
            name="name"
            placeholder={userType === 'retailer' ? 'Shop Owner Name' : 'Warehouse Name'}
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />

          {/* Mobile */}
          <input
            className="input-field"
            type="tel"
            name={userType === 'retailer' ? 'shop_mobile' : 'mobile'}
            placeholder={userType === 'retailer' ? 'Shop Mobile' : 'Mobile'}
            value={userType === 'retailer' ? formData.shop_mobile : formData.mobile}
            onChange={(e) => setFormData({ ...formData, [e.target.name]: e.target.value })}
            required
          />

          {/* Address */}
          <input
            className="input-field"
            type="text"
            name={userType === 'retailer' ? 'shop_address' : 'address'}
            placeholder="Address"
            value={userType === 'retailer' ? formData.shop_address : formData.address}
            onChange={(e) => setFormData({ ...formData, [e.target.name]: e.target.value })}
            required
          />

          {/* City & Region */}
          <div className="grid grid-cols-2 gap-4">
            <input
              className="input-field"
              type="text"
              name="city"
              placeholder="City"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              required
            />
            <input
              className="input-field"
              type="text"
              name="region"
              placeholder="Region"
              value={formData.region}
              onChange={(e) => setFormData({ ...formData, region: e.target.value })}
              required
            />
          </div>

          {/* Password */}
          <input
            className="input-field"
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
            minLength={6}
          />
          <input
            className="input-field"
            type="password"
            name="confirmPassword"
            placeholder="Confirm Password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            required
            minLength={6}
          />

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="login-link">
          Already have an account? <Link to="/login">Sign in here</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
