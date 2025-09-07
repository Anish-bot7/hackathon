import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../Authcontext';
import "../styles/styles.css";

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [userType, setUserType] = useState('retailer');
  const [formData, setFormData] = useState({
    shop_mobile: '',
    mobile: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const credentials = userType === 'retailer' 
      ? { shop_mobile: formData.shop_mobile, password: formData.password }
      : { mobile: formData.mobile, password: formData.password };

    const result = await login(credentials, userType);
    
    if (result.success) {
      navigate(userType === 'retailer' ? '/retailer-dashboard' : '/warehouse-dashboard');
    } else {
      setError(result.message);
    }
    setLoading(false);
  };

  return (
    <div className="login-container">
  <div className="login-card">
    <div className="text-center mb-8">
      <h2 className="login-title">Welcome Back</h2>
      <p className="login-subtitle mt-2">Sign in to your account</p>
    </div>

    {/* User Type Selection */}
    <div className="mb-6 grid grid-cols-2 gap-2 p-1 bg-gray-100 rounded-lg">
      <button
        type="button"
        onClick={() => setUserType('retailer')}
        className={`user-type-btn py-2 px-4 text-sm ${userType === 'retailer' ? 'active' : 'text-gray-700 hover:text-gray-900'}`}
      >
        🏪 Retailer
      </button>
      <button
        type="button"
        onClick={() => setUserType('warehouse')}
        className={`user-type-btn py-2 px-4 text-sm ${userType === 'warehouse' ? 'active' : 'text-gray-700 hover:text-gray-900'}`}
      >
        🏭 Warehouse
      </button>
    </div>

    <form onSubmit={handleSubmit} className="space-y-6">
      {error && <div className="error-msg">{error}</div>}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {userType === 'retailer' ? 'Shop Mobile Number' : 'Mobile Number'}
        </label>
        <input
          type="tel"
          name={userType === 'retailer' ? 'shop_mobile' : 'mobile'}
          value={userType === 'retailer' ? formData.shop_mobile : formData.mobile}
          onChange={(e) => setFormData({...formData, [e.target.name]: e.target.value})}
          className="input-field w-full"
          placeholder="Enter mobile number"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          className="input-field w-full"
          placeholder="Enter password"
          required
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="submit-btn w-full py-3 px-4 disabled:opacity-50"
      >
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>

    <div className="mt-6 text-center text-sm text-gray-600">
      Don't have an account?{' '}
      <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
        Sign up here
      </Link>
    </div>
  </div>
</div>

  );
};

export default Login;