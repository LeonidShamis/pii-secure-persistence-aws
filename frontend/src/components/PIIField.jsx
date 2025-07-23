/**
 * PIIField Component
 * Reusable input field with PII level security indicators
 */

import { useState } from 'react'
import { Eye, EyeOff, Lock, Shield, AlertTriangle } from 'lucide-react'
import { getPIILevel } from '../services/api'

function PIIField({ 
  name,
  value,
  onChange,
  type = 'text',
  placeholder,
  required = false,
  disabled = false,
  showValue = false,
  onToggleVisibility,
  validation
}) {
  const [focused, setFocused] = useState(false)
  const piiInfo = getPIILevel(name)
  
  const handleChange = (e) => {
    onChange(name, e.target.value)
  }

  const getFieldIcon = () => {
    switch (piiInfo.level) {
      case 1:
        return <Shield size={16} className="field-icon level-1" />
      case 2:
        return <Lock size={16} className="field-icon level-2" />
      case 3:
        return <AlertTriangle size={16} className="field-icon level-3" />
      default:
        return <Shield size={16} className="field-icon level-1" />
    }
  }

  const shouldMaskInput = piiInfo.level === 3 && !showValue && value
  const displayValue = shouldMaskInput ? '••••••••••' : value

  return (
    <div className={`pii-field level-${piiInfo.level} ${focused ? 'focused' : ''}`}>
      <div className="field-header">
        <label className="field-label">
          {getFieldIcon()}
          <span className="label-text">
            {placeholder || name}
            {required && <span className="required">*</span>}
          </span>
          <span className={`pii-badge level-${piiInfo.level}`}>
            {piiInfo.icon} Level {piiInfo.level}
          </span>
        </label>
        
        {piiInfo.level === 3 && value && (
          <button
            type="button"
            className="visibility-toggle"
            onClick={() => onToggleVisibility?.(name)}
            title={showValue ? 'Hide sensitive data' : 'Show sensitive data'}
          >
            {showValue ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>

      <div className="field-input-container">
        <input
          type={shouldMaskInput ? 'password' : type}
          name={name}
          value={displayValue}
          onChange={handleChange}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={focused ? '' : `Enter ${placeholder || name}...`}
          required={required}
          disabled={disabled}
          className="field-input"
          autoComplete="off"
        />
        
        <div className={`security-indicator level-${piiInfo.level}`} 
             title={`${piiInfo.label}: ${piiInfo.description}`}>
        </div>
      </div>

      <div className="field-footer">
        <div className="field-info">
          <span className={`security-label level-${piiInfo.level}`}>
            {piiInfo.label}
          </span>
          <span className="security-description">
            {piiInfo.description}
          </span>
        </div>
        
        {validation && validation.error && (
          <div className="field-error">
            ⚠️ {validation.error}
          </div>
        )}
        
        {validation && validation.success && (
          <div className="field-success">
            ✅ {validation.success}
          </div>
        )}
      </div>
    </div>
  )
}

export default PIIField