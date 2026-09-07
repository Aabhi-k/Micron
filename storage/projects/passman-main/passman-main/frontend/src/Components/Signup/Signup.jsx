import { useState } from 'react';
import './Signup.css';
import { registerUser } from '../api/api';
import { deriveAESKey } from '../Encryption/CryptoUtils';
import { setAESKey } from '../Encryption/AesKeyStore';
import { useNavigate, Link } from 'react-router-dom';
import passmanLogo from '../../assets/passmanLogo.png';

const Signup = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
    if (error) setError('');
  };

  const validateForm = () => {
    setLoading(false); 
    
    if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
      setError('All fields are required');
      return false;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    localStorage.clear('token');
    localStorage.clear('userId');
    e.preventDefault();
    setError('');
    setSuccess('');
    
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    try {
      const userData = {
        name: formData.name,
        email: formData.email,
        password: formData.password
      };

      const response = await registerUser(userData);
      
      if (!response || response.status !== 200) {
        throw new Error(response?.data?.message || 'Signup failed');
      }
      
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('userId', response.data.userId);
      
      // Generate encryption key from password and salt
      const salt = response.data.encryptionSalt;
      const aesKey = await deriveAESKey(formData.password, salt);
      setAESKey(aesKey);
            
      setSuccess('Account created successfully!');
      
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
      
    } catch (err) {
      console.error('Signup error:', err);
      
      // Handle specific error cases
      if (err.response) {
        // Server responded with an error status
        const status = err.response.status;
        const message = err.response.data?.message;
        
        if (status === 409 || message?.includes('already exists')) {
          setError('This email is already registered. Please use a different email or login.');
        } else if (status === 400) {
          setError('Invalid information provided. Please check your details.');
        } else {
          setError(`Signup failed: ${message || 'Please try again later.'}`);
        }
      } else if (err.request) {
        // Request was made but no response
        setError('Network error. Please check your connection and try again.');
      } else {
        // Something else went wrong
        setError('Signup failed. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <div className="signup-form-box">
      <div className="logo-container">
          <img src={passmanLogo} alt="PassMan Logo" />
        </div>
        <h2 className="signup-subtitle">Create your account</h2>
        
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Choose a username"
              disabled={loading}
              className='form-input'
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              disabled={loading}
              className='form-input'
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a password"
              disabled={loading}
              className='form-input'
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm your password"
              disabled={loading}
              className='form-input'
            />
          </div>
          
          <button type="submit" className="signup-button" disabled={loading}>
            {loading ? (
              <div className="signup-loading-spinner">
                <div className="signup-spinner"></div>
                <span>Creating account...</span>
              </div>
            ) : (
              'Create Account'
            )}
          </button>
        </form>
        
        <div className="signup-footer">
          <p className='signup-footer-text'>
            Already have an account? <Link to="/login" className='signup-footer-link'>Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Signup;