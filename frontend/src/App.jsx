/**
 * PII Encryption System Frontend
 * Main application component with security-focused UI
 */

import { useState } from 'react'
import UserForm from './components/UserForm'
import UserDisplay from './components/UserDisplay'
import SecurityInfo from './components/SecurityInfo'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('form')
  const [selectedUserId, setSelectedUserId] = useState(null)

  const handleUserCreated = (userId) => {
    setSelectedUserId(userId)
    setCurrentView('display')
  }

  const handleViewUser = (userId) => {
    setSelectedUserId(userId)
    setCurrentView('display')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            🔒 PII Encryption System
          </h1>
          <p className="app-subtitle">
            Demonstrating Three-Tier Encryption for Personally Identifiable Information
          </p>
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={`nav-button ${currentView === 'form' ? 'active' : ''}`}
          onClick={() => setCurrentView('form')}
        >
          📝 Create User
        </button>
        <button 
          className={`nav-button ${currentView === 'display' ? 'active' : ''}`}
          onClick={() => setCurrentView('display')}
          disabled={!selectedUserId}
        >
          👁️ View User
        </button>
        <button 
          className={`nav-button ${currentView === 'info' ? 'active' : ''}`}
          onClick={() => setCurrentView('info')}
        >
          ℹ️ Security Info
        </button>
      </nav>

      <main className="app-main">
        {currentView === 'form' && (
          <UserForm onUserCreated={handleUserCreated} />
        )}
        
        {currentView === 'display' && (
          <UserDisplay 
            userId={selectedUserId} 
            onViewUser={handleViewUser}
          />
        )}
        
        {currentView === 'info' && (
          <SecurityInfo />
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <p>
            🛡️ This system demonstrates secure handling of PII using AWS services.
            All encryption is performed server-side with no sensitive data stored locally.
          </p>
          <div className="security-indicators-legend">
            <span className="legend-item">
              <span className="indicator level-1">●</span> Level 1: Low Sensitivity (RDS encryption)
            </span>
            <span className="legend-item">
              <span className="indicator level-2">●</span> Level 2: Medium Sensitivity (KMS encryption)
            </span>
            <span className="legend-item">
              <span className="indicator level-3">●</span> Level 3: High Sensitivity (Double encryption)
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
