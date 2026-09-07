import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { encryptData } from '../../../Components/Encryption/CryptoUtils';
import { getAESKey } from '../../../Components/Encryption/AesKeyStore';
import './InsertPassword.css';
import { savePassword } from '../../api/api';

const colorizePassword = (password) => {
  if (!password) return '';
  
  return password.split('').map((char, index) => {
    if (/[A-Za-z]/.test(char)) {
      return `<span key=${index} class="password-char letter">${char}</span>`;
    } else if (/[0-9]/.test(char)) {
      return `<span key=${index} class="password-char number">${char}</span>`;
    } else {
      return `<span key=${index} class="password-char special">${char}</span>`;
    }
  }).join('');
};

const InsertPassword = () => {
  const [formData, setFormData] = useState({
    title: '',
    username: '',
    password: '',
    url: '',
    description: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Add states for password generator
  const [showPasswordGenerator, setShowPasswordGenerator] = useState(false);
  const [passwordLength, setPasswordLength] = useState(12);
  
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const generatePassword = (length) => {
    const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:,.<>?";
    let password = "";
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * charset.length);
      password += charset[randomIndex];
    }
    return password;
  };

  const handleGeneratePassword = () => {
    setShowPasswordGenerator(!showPasswordGenerator);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.password) {
      setError('Title and password fields are required');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const aesKey = await getAESKey();
      
      if (!aesKey) {
        throw new Error('Encryption key not found. Please log in again.');
      }
      const encryptedData = await encryptData(formData, aesKey);
      const ed = {...encryptedData, userId:localStorage.getItem('userId')};
      const response = await savePassword(ed);

      if (response.status !== 201) {
        throw new Error('Failed to save password. Please try again.');
      }
      navigate('/dashboard');
      
    } catch (err) {
      console.error('Error saving password:', err);
      setError('Failed to save password. Please try again.');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="insert-password-container">
      <div className="form-container">
      <div className="insert-password-header">
        <h1>Add New Password</h1>
        <button 
          className="back-button"
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
       
        <form className="password-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title <span className="required">*</span></label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="form-input"
              placeholder="e.g. Gmail, Facebook, Bank Account"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="username">Username/Email</label>
            <input
              type="text"
              id="username"
              name="username"
              className="form-input"
              value={formData.username}
              onChange={handleChange}
              placeholder="Your login username or email"
            />
          </div>
          
          <div className="form-group password-input-group">
            <label htmlFor="password">Password <span className="required">*</span></label>
            <div className="password-field">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
                required
                className={`form-input ${showPassword ? "colorized" : ""}`}
              />
              {showPassword && (
                <div 
                  className="password-overlay" 
                  dangerouslySetInnerHTML={{ __html: colorizePassword(formData.password) }} 
                />
              )}
              <div className="password-actions">
                <button 
                  type="button" 
                  className="toggle-password-btn"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
                <button 
                  type="button" 
                  className="generate-password-btn"
                  onClick={handleGeneratePassword}
                >
                  {showPasswordGenerator ? "Hide" : "Generate"}
                </button>
              </div>
            </div>
            
            {showPasswordGenerator && (
              <div className="password-generator">
                <div className="length-slider">
                  <span>Length: {passwordLength}</span>
                  <input 
                    type="range" 
                    min="8" 
                    max="32" 
                    value={passwordLength} 
                    onChange={(e) => setPasswordLength(parseInt(e.target.value))} 
                    className="slider"
                  />
                </div>
                <button 
                  type="button"
                  className="generate-btn"
                  onClick={() => {
                    const newPassword = generatePassword(passwordLength);
                    setFormData({...formData, password: newPassword});
                  }}
                >
                  Generate New Password
                </button>
              </div>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="url">Website URL</label>
            <input
              type="text"
              id="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://example.com"
              className="form-input"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Add notes or additional details"
              rows="3"
              className="form-textarea"
            />
          </div>
          
          <div className="form-actions">
            <button 
              type="button" 
              className="cancel-btn"
              onClick={() => navigate('/dashboard')}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="save-btn"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Password'}
            </button>
          </div>
        </form>
       
      </div>
    </div>
  );
};

export default InsertPassword;