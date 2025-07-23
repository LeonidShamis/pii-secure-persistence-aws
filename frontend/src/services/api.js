/**
 * API Service for PII Backend Integration
 * Handles all communication with FastAPI backend
 */

import axios from 'axios'

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://your-app-runner-url.awsapprunner.com'
const API_KEY = import.meta.env.VITE_API_KEY || 'your-api-key-here'

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`
  }
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🔗 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('❌ API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Unknown error'
    console.error(`❌ API Error: ${error.response?.status} - ${message}`)
    
    // Transform error for consistent handling
    const apiError = {
      status: error.response?.status || 0,
      message: message,
      data: error.response?.data
    }
    
    return Promise.reject(apiError)
  }
)

/**
 * API Methods
 */
export const api = {
  // Health check
  async healthCheck() {
    const response = await apiClient.get('/health')
    return response.data
  },

  // Create user with PII data
  async createUser(userData) {
    const response = await apiClient.post('/users', userData)
    return response.data
  },

  // Get user by ID (with decryption)
  async getUser(userId) {
    const response = await apiClient.get(`/users/${userId}`)
    return response.data
  },

  // List users (basic info only)
  async listUsers(limit = 10, offset = 0) {
    const response = await apiClient.get('/users', {
      params: { limit, offset }
    })
    return response.data
  },

  // Get audit trail for user
  async getUserAudit(userId, limit = 100) {
    const response = await apiClient.get(`/users/${userId}/audit`, {
      params: { limit }
    })
    return response.data
  },

  // Get system-wide audit trail
  async getSystemAudit(limit = 100) {
    const response = await apiClient.get('/audit', {
      params: { limit }
    })
    return response.data
  }
}

/**
 * PII Classification Helper
 * Maps field names to their security levels
 */
export const PIILevels = {
  // Level 1 - Low Sensitivity (Green)
  1: {
    fields: ['email', 'first_name', 'last_name', 'phone'],
    color: '#10b981', // Green
    label: 'Low Sensitivity',
    description: 'RDS encryption only',
    icon: '🟢'
  },
  
  // Level 2 - Medium Sensitivity (Orange)  
  2: {
    fields: ['address', 'date_of_birth', 'ip_address'],
    color: '#f59e0b', // Orange
    label: 'Medium Sensitivity', 
    description: 'KMS field-level encryption',
    icon: '🟠'
  },
  
  // Level 3 - High Sensitivity (Red)
  3: {
    fields: ['ssn', 'bank_account', 'credit_card'],
    color: '#ef4444', // Red
    label: 'High Sensitivity',
    description: 'Double encryption (App + KMS)',
    icon: '🔴'
  }
}

/**
 * Get PII level for a field name
 */
export function getPIILevel(fieldName) {
  const fieldLower = fieldName.toLowerCase()
  
  for (const [level, config] of Object.entries(PIILevels)) {
    if (config.fields.includes(fieldLower)) {
      return {
        level: parseInt(level),
        ...config
      }
    }
  }
  
  // Default to level 1
  return {
    level: 1,
    ...PIILevels[1]
  }
}

/**
 * Validate required environment variables
 */
export function validateConfig() {
  const errors = []
  
  if (!API_BASE_URL || API_BASE_URL.includes('your-app-runner-url')) {
    errors.push('VITE_API_BASE_URL is not configured')
  }
  
  if (!API_KEY || API_KEY.includes('your-api-key')) {
    errors.push('VITE_API_KEY is not configured')
  }
  
  if (errors.length > 0) {
    console.warn('⚠️ API Configuration Issues:', errors)
    return false
  }
  
  return true
}

export default api