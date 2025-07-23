/**
 * UserDisplay Component
 * Display user data with appropriate masking and security indicators
 */

import { useState, useEffect } from 'react'
import { Eye, EyeOff, RefreshCw, User, AlertCircle, Search, Download } from 'lucide-react'
import PIIField from './PIIField'
import { api, getPIILevel } from '../services/api'

function UserDisplay({ userId, onViewUser }) {
  const [userData, setUserData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [visibilityState, setVisibilityState] = useState({})
  const [searchUserId, setSearchUserId] = useState(userId || '')
  const [auditData, setAuditData] = useState(null)
  const [showAudit, setShowAudit] = useState(false)

  useEffect(() => {
    if (userId) {
      fetchUser(userId)
    }
  }, [userId])

  const fetchUser = async (id) => {
    if (!id) return

    setLoading(true)
    setError(null)
    
    try {
      console.log(`🔍 Fetching user: ${id}`)
      const response = await api.getUser(id)
      
      if (response.success && response.data) {
        setUserData({
          user_id: id,
          ...response.data
        })
      } else {
        throw new Error('Invalid response format')
      }
    } catch (err) {
      console.error('❌ Error fetching user:', err)
      setError(err.message || 'Failed to load user data')
      setUserData(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchAuditTrail = async (id) => {
    try {
      console.log(`📋 Fetching audit trail for user: ${id}`)
      const response = await api.getUserAudit(id)
      setAuditData(response.data)
      setShowAudit(true)
    } catch (err) {
      console.error('❌ Error fetching audit trail:', err)
      setError('Failed to load audit trail')
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchUserId.trim()) {
      onViewUser(searchUserId.trim())
    }
  }

  const handleToggleVisibility = (fieldName) => {
    setVisibilityState(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName]
    }))
  }

  const handleRefresh = () => {
    if (userId) {
      fetchUser(userId)
    }
  }

  const renderField = (fieldName, value, label) => {
    if (!value) return null

    const piiInfo = getPIILevel(fieldName)
    const shouldMask = piiInfo.level === 3 && !visibilityState[fieldName]
    const displayValue = shouldMask ? '••••••••••' : value

    return (
      <div key={fieldName} className={`display-field level-${piiInfo.level}`}>
        <div className="field-header">
          <label className="field-label">
            <span className={`pii-indicator level-${piiInfo.level}`}>
              {piiInfo.icon}
            </span>
            <span className="label-text">{label || fieldName}</span>
            <span className={`pii-badge level-${piiInfo.level}`}>
              Level {piiInfo.level}
            </span>
          </label>
          
          {piiInfo.level === 3 && (
            <button
              type="button"
              className="visibility-toggle"
              onClick={() => handleToggleVisibility(fieldName)}
              title={visibilityState[fieldName] ? 'Hide sensitive data' : 'Reveal sensitive data'}
            >
              {visibilityState[fieldName] ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          )}
        </div>

        <div className="field-value">
          <span className={shouldMask ? 'masked' : 'revealed'}>
            {displayValue}
          </span>
        </div>

        <div className="field-footer">
          <span className={`security-label level-${piiInfo.level}`}>
            {piiInfo.description}
          </span>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="user-display loading">
        <div className="loading-content">
          <RefreshCw size={24} className="spinning" />
          <p>Loading user data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="user-display">
      <div className="display-header">
        <h2>
          <User size={24} />
          View User Data
        </h2>
        <p>Encrypted data is decrypted server-side and displayed with appropriate security masking.</p>
      </div>

      {/* User Search */}
      <form onSubmit={handleSearch} className="user-search">
        <div className="search-input-group">
          <input
            type="text"
            value={searchUserId}
            onChange={(e) => setSearchUserId(e.target.value)}
            placeholder="Enter User ID to view..."
            className="search-input"
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            <Search size={16} />
            Load User
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {userData && (
        <div className="user-data">
          <div className="data-header">
            <div className="user-info">
              <h3>User ID: {userData.user_id}</h3>
              {userData.created_at && (
                <p className="creation-date">
                  Created: {new Date(userData.created_at).toLocaleDateString()}
                </p>
              )}
            </div>
            <div className="data-actions">
              <button
                onClick={handleRefresh}
                className="btn btn-secondary"
                disabled={loading}
              >
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                onClick={() => fetchAuditTrail(userData.user_id)}
                className="btn btn-secondary"
              >
                <Download size={16} />
                View Audit
              </button>
            </div>
          </div>

          <div className="data-sections">
            {/* Level 1 Fields */}
            <div className="data-section level-1">
              <h4 className="section-title">
                🟢 Level 1 - Basic Information
                <span className="section-note">(RDS encryption only)</span>
              </h4>
              <div className="fields-grid">
                {renderField('email', userData.email, 'Email Address')}
                {renderField('first_name', userData.first_name, 'First Name')}
                {renderField('last_name', userData.last_name, 'Last Name')} 
                {renderField('phone', userData.phone, 'Phone Number')}
              </div>
            </div>

            {/* Level 2 Fields */}
            <div className="data-section level-2">
              <h4 className="section-title">
                🟠 Level 2 - Personal Details
                <span className="section-note">(KMS field-level encryption)</span>
              </h4>
              <div className="fields-grid">
                {renderField('address', userData.address, 'Home Address')}
                {renderField('date_of_birth', userData.date_of_birth, 'Date of Birth')}
                {renderField('ip_address', userData.ip_address, 'IP Address')}
              </div>
            </div>

            {/* Level 3 Fields */}
            <div className="data-section level-3 sensitive">
              <h4 className="section-title">
                🔴 Level 3 - Highly Sensitive
                <span className="section-note">(Double encryption)</span>
              </h4>
              <div className="fields-grid">
                {renderField('ssn', userData.ssn, 'Social Security Number')}
                {renderField('bank_account', userData.bank_account, 'Bank Account')}
                {renderField('credit_card', userData.credit_card, 'Credit Card')}
              </div>
            </div>
          </div>

          <div className="data-footer">
            <p className="security-notice">
              🔒 Level 3 data is masked by default. Click the eye icon to reveal.
              All decryption is performed server-side with full audit logging.
            </p>
          </div>
        </div>
      )}

      {/* Audit Trail Modal */}
      {showAudit && auditData && (
        <div className="audit-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Audit Trail - User {userData?.user_id}</h3>
              <button
                onClick={() => setShowAudit(false)}
                className="modal-close"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              {auditData.audit_logs && auditData.audit_logs.length > 0 ? (
                <div className="audit-list">
                  {auditData.audit_logs.map((log, index) => (
                    <div key={index} className="audit-entry">
                      <div className="audit-info">
                        <span className="audit-operation">{log.operation}</span>
                        <span className="audit-field">{log.field_name}</span>
                        <span className={`audit-level level-${log.pii_level}`}>
                          Level {log.pii_level}
                        </span>
                      </div>
                      <div className="audit-meta">
                        <span className="audit-time">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                        <span className={`audit-status ${log.success ? 'success' : 'error'}`}>
                          {log.success ? '✅' : '❌'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No audit logs found for this user.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserDisplay