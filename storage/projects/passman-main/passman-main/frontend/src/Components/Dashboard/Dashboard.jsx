import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";
import { getAllPasswords, updatePassword, deletePassword } from "../api/api";
import { decryptData, encryptData } from "../Encryption/CryptoUtils";
import { getAESKey } from "./../Encryption/AesKeyStore";

import passmanlogo from "../../assets/passmanLogo.png";

import searchIcon from "../../assets/icons/search.svg";
import signoutIcon from "../../assets/icons/signout.svg";
import settingsIcon from "../../assets/icons/gear-solid.svg";

const colorizePassword = (password) => {
  if (!password) return "";

  return password
    .split("")
    .map((char, index) => {
      if (/[A-Za-z]/.test(char)) {
        return `<span key=${index} class="password-char letter">${char}</span>`;
      } else if (/[0-9]/.test(char)) {
        return `<span key=${index} class="password-char number">${char}</span>`;
      } else {
        return `<span key=${index} class="password-char special">${char}</span>`;
      }
    })
    .join("");
};

const Dashboard = () => {
  const [selectedPassword, setSelectedPassword] = useState(null);
  const [view, setView] = useState(false);
  const [passwords, setPasswords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const [success, setSuccess] = useState("");
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [refreshPasswords, setRefreshPasswords] = useState(true);
  const [editFormData, setEditFormData] = useState({
    title: "",
    username: "",
    password: "",
    url: "",
    description: "",
  });

  const [searchTerm, setSearchTerm] = useState("");

  const [showPasswordGenerator, setShowPasswordGenerator] = useState(false);
  const [passwordLength, setPasswordLength] = useState(12);

  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    let toastTimer;
    if (showSuccessToast) {
      toastTimer = setTimeout(() => {
        setShowSuccessToast(false);
      }, 3000);
    }
    return () => {
      if (toastTimer) clearTimeout(toastTimer);
    };
  }, [showSuccessToast]);
  const fetchPasswords = async () => {
    try {
      const response = await getAllPasswords(localStorage.getItem("userId"));
      const key = await getAESKey();
      if (response.status === 200) {
        if (!response.data || response.data.length === 0) {
          setPasswords([]);
        } else {
          const decryptedPasswords = await Promise.all(
            response.data.map(async (encryptedPassword) => {
              try {
                return await decryptData(encryptedPassword, key);
              } catch (decryptError) {
                console.error("Failed to decrypt password:", decryptError);
                return {
                  title: "Decryption failed",
                  username: "Error",
                  error: true,
                };
              }
            })
          );

          setPasswords(decryptedPasswords);
        }
      } else {
        setError("Failed to load your passwords. Please try again.");
      }
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch passwords:", err);
      setError("Failed to load your passwords. Please try again.");
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }

    if (refreshPasswords) {
      fetchPasswords();
      setRefreshPasswords(false);
    }
  }, [navigate, refreshPasswords]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [menuRef]);

  const handleAddPassword = () => {
    navigate("/insert-password");
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const filteredPasswords = () => {
    if (!searchTerm.trim()) {
      return passwords;
    }
    const term = searchTerm.toLowerCase().trim();
    return passwords.filter(
      (password) =>
        password.title.toLowerCase().includes(term) ||
        (password.username && password.username.toLowerCase().includes(term)) ||
        (password.url && password.url.toLowerCase().includes(term)) ||
        (password.description &&
          password.description.toLowerCase().includes(term))
    );
  };

  const handlePasswordClick = (password) => {
    setSelectedPassword(password);
    setView(true);
  };
  const CloseModel = () => {
    setView(false);
    setSelectedPassword(null);
    setIsEditing(false);

    setRefreshPasswords(true);
  };
  const generatePassword = (length) => {
    const charset =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:,.<>?";
    let password = "";
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * charset.length);
      password += charset[randomIndex];
    }
    return password;
  };

  const EditPassword = () => {
    setEditFormData({
      title: selectedPassword.title,
      username: selectedPassword.username || "",
      password: selectedPassword.password || "",
      url: selectedPassword.url || "",
      description: selectedPassword.description || "",
    });

    setIsEditing(true);
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSave = async () => {
    const key = await getAESKey();
    const encryptedD = await encryptData(editFormData, key);
    const passwordDto = {
      ...encryptedD,
      userId: localStorage.getItem("userId"),
      id: selectedPassword.id,
    };

    try {
      const response = await updatePassword(passwordDto);
      if (response.status === 200) {
        setSelectedPassword({
          ...selectedPassword,
          ...editFormData,
        });

        setSuccess("Password Updated successfully!");
        setShowSuccessToast(true);
        setIsEditing(false);

        const updatedPasswords = passwords.map((password) =>
          password.id === selectedPassword.id
            ? { ...password, ...editFormData }
            : password
        );
        setPasswords(updatedPasswords);
      }
    } catch (e) {
      console.log("error: ", e);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      const response = await deletePassword(selectedPassword.id);

      if (response.status === 200) {
        // First close the modal
        setView(false);
        setSelectedPassword(null);
        setIsEditing(false);

        // Then show success message
        setSuccess("Password deleted successfully");
        setShowSuccessToast(true);

        // Update the password list
        setRefreshPasswords(true);
      } else {
        setError("Failed to delete password. Please try again.");
      }
    } catch (err) {
      console.error("Error deleting password:", err);
      setError("Failed to delete password. Please try again.");
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleMenuToggle = () => {
    setShowMenu(!showMenu);
  };

  const handleSignOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");

    navigate("/login");
  };

  const navigateToSettings = () => {
    navigate("/settings");
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard">
        {showSuccessToast && (
          <div className="success-toast">
            <div className="toast-content">
              <span className="toast-icon">✓</span>
              <span className="toast-message">{success}</span>
            </div>
          </div>
        )}

        <header className="dashboard-header">
          <div className="logo-container">
            <img src={passmanlogo} width={200} alt="PassMan Logo" />
          </div>
          <div className="dashboard-actions">
            <button className="add-password-btn" onClick={handleAddPassword}>
              Add Password
            </button>
            <div className="user-menu-container" ref={menuRef}>
              <button
                className="user-menu-btn"
                onClick={handleMenuToggle}
                aria-label="User menu"
              >
                <i className="hamburger-icon"></i>
              </button>
              {showMenu && (
                <div className="user-dropdown-menu">
                  <button className="menu-item" onClick={navigateToSettings}>
                    <img
                      src={settingsIcon}
                      alt="Settings"
                      className="menu-icon"
                    />
                    Settings
                  </button>
                  <button className="menu-item" onClick={handleSignOut}>
                    <img
                      src={signoutIcon}
                      alt="Sign out"
                      className="menu-icon"
                    />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="search-container">
          <img src={searchIcon} alt="Search" className="search-icon" />
          <input
            type="text"
            placeholder="Search passwords..."
            value={searchTerm}
            onChange={handleSearch}
            className="search-input"
          />
          {searchTerm && (
            <button
              className="clear-search-btn"
              onClick={() => setSearchTerm("")}
              title="Clear search"
            >
              ×
            </button>
          )}
        </div>

        <main className="dashboard-content">
          {loading ? (
            <div className="loading-spinner">Loading your passwords...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : passwords.length === 0 ? (
            <div className="empty-state">
              <h2>No passwords saved yet</h2>
              <p>Click "Add Password" to store your first password securely.</p>
              <button
                className="add-password-btn-large"
                onClick={handleAddPassword}
              >
                Add Your First Password
              </button>
            </div>
          ) : (
            <div className="password-list-container">
              <ul className="password-list">
                {filteredPasswords().map((password, index) => (
                  <li
                    key={password.id || index}
                    className={`password-list-item ${
                      password.error ? "password-item-error" : ""
                    }`}
                    onClick={() => handlePasswordClick(password)}
                  >
                    <div className="password-item-content">
                      <div className="password-title">{password.title}</div>
                      <div className="password-username">
                        {password.username || "No username"}
                      </div>
                    </div>
                    <div className="password-item-actions">
                      <button
                        className="copy-password-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigator.clipboard.writeText(password.password);
                        }}
                        title="Copy password"
                      >
                        Copy
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </main>
        {view && selectedPassword && (
          <div className="password-modal-overlay" onClick={CloseModel}>
            <div
              className="password-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2>{isEditing ? "Edit Password" : selectedPassword.title}</h2>
                <button className="modal-close-btn" onClick={CloseModel}>
                  ×
                </button>
              </div>

              <div className="modal-body">
                {isEditing ? (
                  // EDIT MODE
                  <form className="edit-password-form">
                    <div className="modal-field">
                      <label htmlFor="edit-title">Title:</label>
                      <input
                        type="text"
                        id="edit-title"
                        name="title"
                        value={editFormData.title}
                        onChange={handleEditChange}
                        className="edit-input"
                      />
                    </div>

                    <div className="modal-field">
                      <label htmlFor="edit-username">Username:</label>
                      <input
                        type="text"
                        id="edit-username"
                        name="username"
                        value={editFormData.username}
                        onChange={handleEditChange}
                        className="edit-input"
                      />
                    </div>

                    <div className="modal-field">
                      <label htmlFor="edit-password">Password:</label>
                      <div className="password-input-group">
                        <input
                          type="text"
                          id="edit-password"
                          name="password"
                          value={editFormData.password}
                          onChange={handleEditChange}
                          className="edit-input"
                        />
                        <button
                          type="button"
                          className="generate-password-btn"
                          onClick={() =>
                            setShowPasswordGenerator(!showPasswordGenerator)
                          }
                          title={
                            showPasswordGenerator
                              ? "Hide generator"
                              : "Generate password"
                          }
                        >
                          {showPasswordGenerator ? "Hide" : "Generate"}
                        </button>
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
                              onChange={(e) =>
                                setPasswordLength(parseInt(e.target.value))
                              }
                              className="slider"
                            />
                          </div>
                          <button
                            type="button"
                            className="generate-btn"
                            onClick={() => {
                              const newPassword =
                                generatePassword(passwordLength);
                              setEditFormData({
                                ...editFormData,
                                password: newPassword,
                              });
                            }}
                          >
                            Generate New Password
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="modal-field">
                      <label htmlFor="edit-url">Website URL:</label>
                      <input
                        type="text"
                        id="edit-url"
                        name="url"
                        value={editFormData.url}
                        onChange={handleEditChange}
                        className="edit-input"
                      />
                    </div>

                    <div className="modal-field">
                      <label htmlFor="edit-description">Description:</label>
                      <textarea
                        id="edit-description"
                        name="description"
                        value={editFormData.description}
                        onChange={handleEditChange}
                        className="edit-textarea"
                        rows="3"
                      />
                    </div>
                  </form>
                ) : (
                  // VIEW MODE (your existing code)
                  <>
                    {selectedPassword.url && (
                      <div className="modal-field">
                        <label>Website:</label>
                        <div className="field-value">
                          <a
                            href={selectedPassword.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {selectedPassword.url}
                          </a>
                        </div>
                      </div>
                    )}

                    <div className="modal-field">
                      <label>Username:</label>
                      <div className="field-value field-with-copy">
                        <span>
                          {selectedPassword.username || "No username"}
                        </span>
                        <button
                          className="copy-btn"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              selectedPassword.username || ""
                            );
                          }}
                        >
                          Copy
                        </button>
                      </div>
                    </div>

                    <div className="modal-field">
                      <label>Password:</label>
                      <div className="field-value field-with-copy">
                        <span
                          className="password-dots"
                          dangerouslySetInnerHTML={{ __html: "••••••••••" }}
                        ></span>
                        <button
                          className="copy-btn"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              selectedPassword.password || ""
                            );
                          }}
                        >
                          Copy
                        </button>
                        <button
                          className="show-btn"
                          onClick={(e) => {
                            const element = e.target.parentNode.querySelector(
                              ".password-dots, .password-display"
                            );
                            if (e.target.textContent === "Show") {
                              // Replace with colorized password
                              element.innerHTML = colorizePassword(
                                selectedPassword.password || ""
                              );
                              element.className = "password-display"; // Change class for styling
                              e.target.textContent = "Hide";
                            } else {
                              // Hide password
                              element.innerHTML = "••••••••••";
                              element.className = "password-dots"; // Restore original class
                              e.target.textContent = "Show";
                            }
                          }}
                        >
                          Show
                        </button>
                      </div>
                    </div>

                    {selectedPassword.description && (
                      <div className="modal-field">
                        <label>Description:</label>
                        <div className="field-value description">
                          {selectedPassword.description}
                        </div>
                      </div>
                    )}

                    <div className="modal-field metadata">
                      <label>Added:</label>
                      <div className="field-value">
                        {new Date(
                          selectedPassword.createdAt
                        ).toLocaleDateString()}
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="modal-footer">
                {isEditing ? (
                  <>
                    <button className="cancel-btn" onClick={handleCancelEdit}>
                      Cancel
                    </button>
                    <button className="save-btn" onClick={handleSave}>
                      Save Changes
                    </button>
                  </>
                ) : showDeleteConfirm ? (
                  <>
                    <div className="delete-confirmation">
                      <p>Are you sure you want to delete this password?</p>
                      <div className="delete-actions">
                        <button
                          className="cancel-btn"
                          onClick={handleCancelDelete}
                          disabled={isDeleting}
                        >
                          Cancel
                        </button>
                        <button
                          className="delete-btn"
                          onClick={handleDelete}
                          disabled={isDeleting}
                        >
                          {isDeleting ? (
                            <div className="delete-loading-spinner">
                              <div className="delete-spinner"></div>
                              <span className="delete-loading-text">
                                Deleting...
                              </span>
                            </div>
                          ) : (
                            "Confirm Delete"
                          )}
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <button className="edit-btn" onClick={EditPassword}>
                      Edit
                    </button>
                    <button className="delete-btn" onClick={handleDeleteClick}>
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
