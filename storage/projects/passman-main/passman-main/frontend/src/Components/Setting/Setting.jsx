import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Setting.css';
import passmanlogo from '../../assets/passmanLogo.png';
import { getUserDetails, updateUserDetails, changeUserPassword } from '../api/api';

const Setting = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState({
    name: '',
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    
    // Fetch user data
    fetchUserData();
  }, [navigate]);

  useEffect(() => {
    let toastTimer;
    if(showSuccessToast){
      toastTimer = setTimeout(() => {
        setShowSuccessToast(false);
      }, 3000);
    }
    return () => {
      if(toastTimer) clearTimeout(toastTimer);
    };
  }, [showSuccessToast]);

  const fetchUserData = async () => {
    setLoading(true);
    try {
      const response = await getUserDetails();
      if (response.data) {
        setUser(prevState => ({
          ...prevState,
          name: response.data.name,
          email: response.data.email
        }));
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
      setError('Failed to load your profile information. Please try again.');
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUser(prevState => ({
      ...prevState,
      [name]: value
    }));
    if (error) setError('');
  };

  const handleEditProfile = () => {
    setIsEditing(true);
  };

  const handleUpdateProfile = async () => {
    // Validate fields
    if (!user.name.trim()) {
      setError('Username cannot be empty');
      return;
    }
    
    if (!validateEmail(user.email)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setLoading(true);
    
    try {
      // Call API to update user profile
      const updateData = {
        name: user.name,
        email: user.email
      };
      
      const response = await updateUserDetails(updateData);
      
      if (response.data) {
        
        setSuccess('Profile updated successfully!');
        setShowSuccessToast(true);
        setIsEditing(false);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Failed to update profile:', err);
      setError(err.response?.data?.message || 'Failed to update your profile. Please try again.');
      setLoading(false);
    }
  };

  const handleChangePassword = () => {
    setIsChangingPassword(true);
  };

  const handleUpdatePassword = async () => {
    // Validate password fields
    if (!user.currentPassword) {
      setError('Current password is required');
      return;
    }
    
    if (user.newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }
    
    if (user.newPassword !== user.confirmPassword) {
      setError('New passwords do not match');
      return;
    }
    
    setLoading(true);
    
    try {
      // Call API to change password
      const passwordData = {
        currentPassword: user.currentPassword,
        newPassword: user.newPassword,
        confirmPassword: user.confirmPassword
      };
      
      await changeUserPassword(passwordData);
      
      setSuccess('Password changed successfully!');
      setShowSuccessToast(true);
      setIsChangingPassword(false);
      
      // Reset password fields
      setUser(prevState => ({
        ...prevState,
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }));
      
      setLoading(false);
    } catch (err) {
      console.error('Failed to change password:', err);
      setError(err.response?.data?.message || 'Failed to change your password. Please try again.');
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setIsChangingPassword(false);
    // Reset form state
    fetchUserData();
    setError('');
  };

  const handleLogout = () => {
    // Clear all auth data
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('email');
    
    // Redirect to login page
    navigate('/login');
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const navigateToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="settings-container">
      <div className="settings">
        
      {showSuccessToast && (
        <div className="success-toast">
          <div className="toast-content">
            <span className="toast-icon">✓</span>
            <span className="toast-message">{success}</span>
          </div>
        </div>
      )}

      <header className="settings-header">
        <div className="logo-container">
          <img src={passmanlogo} width={200} alt="PassMan Logo" onClick={navigateToDashboard} style={{ cursor: 'pointer' }} />
        </div>
        <div className="settings-actions">
          <button 
            className="back-to-dashboard-btn"
            onClick={navigateToDashboard}
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="settings-content">
        <div className="settings-card">
          <div className="settings-card-header">
            <h2>Account Settings</h2>
            {!isEditing && !isChangingPassword && (
              <button 
                className="edit-profile-btn"
                onClick={handleEditProfile}
                disabled={loading}
              >
                Edit Profile
              </button>
            )}
          </div>

          {error && <div className="settings-error-message">{error}</div>}

          {loading ? (
            <div className="settings-loading">
              <div className="loading-spinner">
                <div className="spinner"></div>
                <span>Loading...</span>
              </div>
            </div>
          ) : (
            <div className="settings-form">
              <div className="settings-section profile-section">
                <h3>Profile Information</h3>
                
                <div className="form-group">
                  <label>Username</label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="name"
                      value={user.name}
                      onChange={handleChange}
                      className="settings-input"
                    />
                  ) : (
                    <div className="settings-value">{user.name}</div>
                  )}
                </div>
                
                <div className="form-group">
                  <label>Email</label>
                  {isEditing ? (
                    <input
                      type="email"
                      name="email"
                      value={user.email}
                      onChange={handleChange}
                      className="settings-input"
                    />
                  ) : (
                    <div className="settings-value">{user.email}</div>
                  )}
                </div>

                {isEditing && (
                  <div className="settings-actions-row">
                    <button 
                      className="cancel-btn"
                      onClick={handleCancel}
                      disabled={loading}
                    >
                      Cancel
                    </button>
                    <button 
                      className="save-btn"
                      onClick={handleUpdateProfile}
                      disabled={loading}
                    >
                      {loading ? (
                        <div className="button-spinner">
                          <div className="spinner-small"></div>
                          <span>Saving...</span>
                        </div>
                      ) : (
                        'Save Changes'
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* <div className="settings-section password-section">
                <h3>Password</h3>
                
                {!isChangingPassword ? (
                  <button 
                    className="change-password-btn"
                    onClick={handleChangePassword}
                    disabled={loading || isEditing}
                  >
                    Change Password
                  </button>
                ) : (
                  <>
                    <div className="form-group">
                      <label>Current Password</label>
                      <input
                        type="password"
                        name="currentPassword"
                        value={user.currentPassword}
                        onChange={handleChange}
                        className="settings-input"
                        placeholder="Enter your current password"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label>New Password</label>
                      <input
                        type="password"
                        name="newPassword"
                        value={user.newPassword}
                        onChange={handleChange}
                        className="settings-input"
                        placeholder="Enter new password"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label>Confirm New Password</label>
                      <input
                        type="password"
                        name="confirmPassword"
                        value={user.confirmPassword}
                        onChange={handleChange}
                        className="settings-input"
                        placeholder="Confirm new password"
                      />
                    </div>

                    <div className="settings-actions-row">
                      <button 
                        className="cancel-btn"
                        onClick={handleCancel}
                        disabled={loading}
                      >
                        Cancel
                      </button>
                      <button 
                        className="save-btn"
                        onClick={handleUpdatePassword}
                        disabled={loading}
                      >
                        {loading ? (
                          <div className="button-spinner">
                            <div className="spinner-small"></div>
                            <span>Updating...</span>
                          </div>
                        ) : (
                          'Update Password'
                        )}
                      </button>
                    </div>
                  </>
                )}
              </div> */}

              <div className="settings-section account-section">
                <h3>Account Actions</h3>
                <button 
                  className="logout-btn"
                  onClick={handleLogout}
                >
                  Logout
                </button>
                <button className="delete-account-btn">
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      
      </div>
    </div>
  );
};

export default Setting;