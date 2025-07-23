/**
 * UserForm Component
 * Data entry form with PII level indicators and validation
 */

import { useState } from 'react'
import { Send, RefreshCw, AlertCircle, CheckCircle, Database } from 'lucide-react'
import PIIField from './PIIField'
import { api } from '../services/api'

function UserForm({ onUserCreated }) {
  const [formData, setFormData] = useState({
    // Level 1 fields
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    
    // Level 2 fields
    address: '',
    date_of_birth: '',
    ip_address: '',
    
    // Level 3 fields
    ssn: '',
    bank_account: '',
    credit_card: ''
  })

  const [visibilityState, setVisibilityState] = useState({})
  const [validation, setValidation] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitResult, setSubmitResult] = useState(null)

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }))
    
    // Clear validation for this field
    if (validation[fieldName]) {
      setValidation(prev => ({
        ...prev,
        [fieldName]: null
      }))
    }
  }

  const handleToggleVisibility = (fieldName) => {
    setVisibilityState(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName]
    }))
  }

  // Random data generators
  const generateRandomData = () => {
    const firstNames = ['John', 'Sarah', 'Michael', 'Emma', 'David', 'Lisa', 'James', 'Maria', 'Robert', 'Jennifer']
    const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    const domains = ['example.com', 'company.com', 'tech.org', 'business.net', 'private.org']
    const streets = ['Main Street', 'Oak Avenue', 'Tech Drive', 'Privacy Lane', 'First Street', 'Second Avenue', 'Park Road', 'Center Street']
    const cities = ['Anytown', 'Springfield', 'Silicon Valley', 'Secure City', 'Downtown', 'Riverside', 'Greenfield', 'Oakville']
    const states = ['NY', 'CA', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
    
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)]
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)]
    const domain = domains[Math.floor(Math.random() * domains.length)]
    const street = streets[Math.floor(Math.random() * streets.length)]
    const city = cities[Math.floor(Math.random() * cities.length)]
    const state = states[Math.floor(Math.random() * states.length)]
    
    // Generate random numbers
    const randomPhone = `+1-555-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`
    const randomZip = String(Math.floor(Math.random() * 90000) + 10000)
    const randomYear = Math.floor(Math.random() * 40) + 1960 // 1960-1999
    const randomMonth = String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')
    const randomDay = String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')
    const randomSSN = `${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 90) + 10)}-${String(Math.floor(Math.random() * 9000) + 1000)}`
    const randomBank = String(Math.floor(Math.random() * 9000000000) + 1000000000)
    const randomCC = `${String(Math.floor(Math.random() * 9000) + 1000)}-${String(Math.floor(Math.random() * 9000) + 1000)}-${String(Math.floor(Math.random() * 9000) + 1000)}-${String(Math.floor(Math.random() * 9000) + 1000)}`
    const randomIP = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
    
    return {
      email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@${domain}`,
      first_name: firstName,
      last_name: lastName,
      phone: randomPhone,
      address: `${Math.floor(Math.random() * 9999) + 1} ${street}, ${city}, ${state} ${randomZip}`,
      date_of_birth: `${randomYear}-${randomMonth}-${randomDay}`,
      ip_address: randomIP,
      ssn: randomSSN,
      bank_account: randomBank,
      credit_card: randomCC
    }
  }

  const handlePopulateData = () => {
    const randomData = generateRandomData()
    setFormData(randomData)
    setSubmitResult(null)
    
    // Clear any existing validation errors
    setValidation({})
    
    console.log(`🎭 Generated random test data for: ${randomData.first_name} ${randomData.last_name}`)
  }

  const validateForm = () => {
    const errors = {}
    
    // Required fields validation
    if (!formData.email) {
      errors.email = { error: 'Email is required' }
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = { error: 'Please enter a valid email address' }
    }
    
    if (!formData.first_name) {
      errors.first_name = { error: 'First name is required' }
    }
    
    if (!formData.last_name) {
      errors.last_name = { error: 'Last name is required' }
    }

    // Optional field validation
    if (formData.phone && !/^[\+]?[1-9][\d]{0,15}$/.test(formData.phone.replace(/[\s\-\(\)]/g, ''))) {
      errors.phone = { error: 'Please enter a valid phone number' }
    }

    if (formData.date_of_birth && !/^\d{4}-\d{2}-\d{2}$/.test(formData.date_of_birth)) {
      errors.date_of_birth = { error: 'Date must be in YYYY-MM-DD format' }
    }

    if (formData.ssn && !/^\d{3}-?\d{2}-?\d{4}$/.test(formData.ssn.replace(/\-/g, ''))) {
      errors.ssn = { error: 'SSN must be in XXX-XX-XXXX format' }
    }

    if (formData.credit_card && !/^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$/.test(formData.credit_card)) {
      errors.credit_card = { error: 'Credit card must be 16 digits' }
    }

    setValidation(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      setSubmitResult({
        type: 'error',
        message: 'Please fix the validation errors above'
      })
      return
    }

    setIsSubmitting(true)
    setSubmitResult(null)

    try {
      // Filter out empty fields
      const submitData = Object.entries(formData)
        .filter(([_, value]) => value && value.trim() !== '')
        .reduce((acc, [key, value]) => ({
          ...acc,
          [key]: value.trim()
        }), {})

      console.log('🚀 Submitting user data:', Object.keys(submitData))
      
      const response = await api.createUser(submitData)
      
      setSubmitResult({
        type: 'success',
        message: `User created successfully! ID: ${response.data.user_id}`,
        userId: response.data.user_id
      })

      // Notify parent component
      onUserCreated(response.data.user_id)

    } catch (error) {
      console.error('❌ Failed to create user:', error)
      setSubmitResult({
        type: 'error',
        message: error.message || 'Failed to create user. Please try again.'
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReset = () => {
    setFormData({
      email: '',
      first_name: '',
      last_name: '',
      phone: '',
      address: '',
      date_of_birth: '',
      ip_address: '',
      ssn: '',
      bank_account: '',
      credit_card: ''
    })
    setValidation({})
    setVisibilityState({})
    setSubmitResult(null)
  }

  return (
    <div className="user-form">
      <div className="form-header">
        <div className="header-content">
          <div className="header-text">
            <h2>Create New User</h2>
            <p>Enter user information. Fields are automatically encrypted based on their sensitivity level.</p>
          </div>
          <div className="header-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handlePopulateData}
              disabled={isSubmitting}
            >
              <Database size={16} />
              Populate Data
            </button>
          </div>
        </div>
      </div>

      {submitResult && (
        <div className={`submit-result ${submitResult.type}`}>
          {submitResult.type === 'success' ? (
            <CheckCircle size={20} />
          ) : (
            <AlertCircle size={20} />
          )}
          <span>{submitResult.message}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="pii-form">
        <div className="form-section">
          <h3 className="section-title">
            🟢 Level 1 - Basic Information <span className="section-note">(RDS encryption only)</span>
          </h3>
          <div className="fields-grid">
            <PIIField
              name="email"
              value={formData.email}
              onChange={handleFieldChange}
              type="email"
              placeholder="Email Address"
              required
              validation={validation.email}
            />
            <PIIField
              name="first_name"
              value={formData.first_name}
              onChange={handleFieldChange}
              placeholder="First Name"
              required
              validation={validation.first_name}
            />
            <PIIField
              name="last_name"
              value={formData.last_name}
              onChange={handleFieldChange}
              placeholder="Last Name"
              required
              validation={validation.last_name}
            />
            <PIIField
              name="phone"
              value={formData.phone}
              onChange={handleFieldChange}
              type="tel"
              placeholder="Phone Number"
              validation={validation.phone}
            />
          </div>
        </div>

        <div className="form-section">
          <h3 className="section-title">
            🟠 Level 2 - Personal Details <span className="section-note">(KMS field-level encryption)</span>
          </h3>
          <div className="fields-grid">
            <PIIField
              name="address"
              value={formData.address}
              onChange={handleFieldChange}
              placeholder="Home Address"
              validation={validation.address}
            />
            <PIIField
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleFieldChange}
              type="date"
              placeholder="Date of Birth"
              validation={validation.date_of_birth}
            />
            <PIIField
              name="ip_address"
              value={formData.ip_address}
              onChange={handleFieldChange}
              placeholder="IP Address"
              validation={validation.ip_address}
            />
          </div>
        </div>

        <div className="form-section sensitive">
          <h3 className="section-title">
            🔴 Level 3 - Highly Sensitive <span className="section-note">(Double encryption)</span>
          </h3>
          <div className="fields-grid">
            <PIIField
              name="ssn"
              value={formData.ssn}
              onChange={handleFieldChange}
              placeholder="Social Security Number"
              showValue={visibilityState.ssn}
              onToggleVisibility={handleToggleVisibility}
              validation={validation.ssn}
            />
            <PIIField
              name="bank_account"
              value={formData.bank_account}
              onChange={handleFieldChange}
              placeholder="Bank Account Number"
              showValue={visibilityState.bank_account}
              onToggleVisibility={handleToggleVisibility}
              validation={validation.bank_account}
            />
            <PIIField
              name="credit_card"
              value={formData.credit_card}
              onChange={handleFieldChange}
              placeholder="Credit Card Number"
              showValue={visibilityState.credit_card}
              onToggleVisibility={handleToggleVisibility}
              validation={validation.credit_card}
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={handleReset}
            className="btn btn-secondary"
            disabled={isSubmitting}
          >
            <RefreshCw size={16} />
            Reset Form
          </button>
          
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <RefreshCw size={16} className="spinning" />
            ) : (
              <Send size={16} />
            )}
            {isSubmitting ? 'Creating User...' : 'Create User'}
          </button>
        </div>

        <div className="form-footer">
          <p className="security-notice">
            🔒 All data is encrypted before storage using AWS KMS and application-layer encryption.
            No sensitive information is stored in your browser.
          </p>
        </div>
      </form>
    </div>
  )
}

export default UserForm