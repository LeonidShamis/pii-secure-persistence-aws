/**
 * SecurityInfo Component
 * Explains the PII encryption system and security measures
 */

import { Shield, Lock, AlertTriangle, Key, Database, Cloud, Eye, FileText } from 'lucide-react'

function SecurityInfo() {
  return (
    <div className="security-info">
      <div className="info-header">
        <h2>
          <Shield size={24} />
          Security Information
        </h2>
        <p>Learn about the three-tier PII encryption system and security measures in place.</p>
      </div>

      {/* Overview */}
      <section className="info-section">
        <h3>
          <Lock size={20} />
          System Overview
        </h3>
        <div className="overview-content">
          <p>
            This system demonstrates secure handling of Personally Identifiable Information (PII) 
            using a three-tier encryption approach on AWS infrastructure. Each piece of data is 
            classified and encrypted according to its sensitivity level.
          </p>
          
          <div className="architecture-diagram">
            <div className="tier tier-1">
              <div className="tier-icon">🟢</div>
              <div className="tier-content">
                <h4>Level 1: Low Sensitivity</h4>
                <p>Basic contact information with RDS at-rest encryption only</p>
              </div>
            </div>
            
            <div className="tier tier-2">
              <div className="tier-icon">🟠</div>
              <div className="tier-content">
                <h4>Level 2: Medium Sensitivity</h4>
                <p>Personal details with AWS KMS field-level encryption</p>
              </div>
            </div>
            
            <div className="tier tier-3">
              <div className="tier-icon">🔴</div>
              <div className="tier-content">
                <h4>Level 3: High Sensitivity</h4>
                <p>Critical data with double encryption (Application + KMS)</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PII Levels Detail */}
      <section className="info-section">
        <h3>
          <AlertTriangle size={20} />
          PII Classification Levels
        </h3>
        
        <div className="pii-levels">
          <div className="level-card level-1">
            <div className="level-header">
              <span className="level-icon">🟢</span>
              <h4>Level 1 - Low Sensitivity</h4>
            </div>
            <div className="level-content">
              <div className="level-fields">
                <strong>Data Types:</strong>
                <ul>
                  <li>Email addresses</li>
                  <li>First and last names</li>
                  <li>Phone numbers</li>
                </ul>
              </div>
              <div className="level-encryption">
                <strong>Encryption:</strong>
                <p>RDS at-rest encryption only</p>
                <p>Data stored in clear text in database</p>
                <p>Queryable and searchable</p>
              </div>
            </div>
          </div>

          <div className="level-card level-2">
            <div className="level-header">
              <span className="level-icon">🟠</span>
              <h4>Level 2 - Medium Sensitivity</h4>
            </div>
            <div className="level-content">
              <div className="level-fields">
                <strong>Data Types:</strong>
                <ul>
                  <li>Home addresses</li>
                  <li>Dates of birth</li>
                  <li>IP addresses</li>
                </ul>
              </div>
              <div className="level-encryption">
                <strong>Encryption:</strong>
                <p>AWS KMS Customer Managed Key encryption</p>
                <p>Field-level encryption before database storage</p>
                <p>Not directly queryable</p>
              </div>
            </div>
          </div>

          <div className="level-card level-3">
            <div className="level-header">
              <span className="level-icon">🔴</span>
              <h4>Level 3 - High Sensitivity</h4>
            </div>
            <div className="level-content">
              <div className="level-fields">
                <strong>Data Types:</strong>
                <ul>
                  <li>Social Security Numbers</li>
                  <li>Bank account numbers</li>
                  <li>Credit card numbers</li>
                </ul>
              </div>
              <div className="level-encryption">
                <strong>Encryption:</strong>
                <p>Double encryption (Application + KMS)</p>
                <p>Masked by default in UI</p>
                <p>Requires explicit reveal action</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Security Measures */}
      <section className="info-section">
        <h3>
          <Key size={20} />
          Security Measures
        </h3>
        
        <div className="security-measures">
          <div className="measure">
            <div className="measure-icon">
              <Cloud size={24} />
            </div>
            <div className="measure-content">
              <h4>AWS Infrastructure</h4>
              <ul>
                <li>AWS KMS for key management with automatic rotation</li>
                <li>AWS Secrets Manager for application keys</li>
                <li>Lambda functions for encryption isolation</li>
                <li>RDS Aurora with encryption at rest</li>
              </ul>
            </div>
          </div>

          <div className="measure">
            <div className="measure-icon">
              <Lock size={24} />
            </div>
            <div className="measure-content">
              <h4>Encryption Standards</h4>
              <ul>
                <li>AES-256 encryption for all encrypted data</li>
                <li>Fernet (symmetric encryption) for application layer</li>
                <li>TLS 1.2+ for all data in transit</li>
                <li>No encryption keys in application code</li>
              </ul>
            </div>
          </div>

          <div className="measure">
            <div className="measure-icon">
              <Database size={24} />
            </div>
            <div className="measure-content">
              <h4>Data Storage</h4>
              <ul>
                <li>Private subnet deployment</li>
                <li>IAM roles with least privilege principle</li>
                <li>No hardcoded credentials</li>
                <li>Comprehensive audit logging</li>
              </ul>
            </div>
          </div>

          <div className="measure">
            <div className="measure-icon">
              <Eye size={24} />
            </div>
            <div className="measure-content">
              <h4>Frontend Security</h4>
              <ul>
                <li>No client-side encryption or key storage</li>
                <li>HTTPS enforced for all communication</li>
                <li>No sensitive data in browser storage</li>
                <li>Automatic data masking for Level 3 fields</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="info-section">
        <h3>
          <FileText size={20} />
          Compliance Features
        </h3>
        
        <div className="compliance-grid">
          <div className="compliance-item">
            <h4>GDPR Compliance</h4>
            <ul>
              <li>Right to deletion (crypto-shredding)</li>
              <li>Data minimization principles</li>
              <li>Encryption requirements met</li>
              <li>Audit trail for data access</li>
            </ul>
          </div>

          <div className="compliance-item">
            <h4>CCPA Compliance</h4>
            <ul>
              <li>Data protection controls</li>
              <li>Access logging and monitoring</li>
              <li>Secure data handling practices</li>
              <li>Deletion capabilities</li>
            </ul>
          </div>

          <div className="compliance-item">
            <h4>PCI DSS Support</h4>
            <ul>
              <li>Credit card data encryption</li>
              <li>Secure transmission protocols</li>
              <li>Access controls and monitoring</li>
              <li>Regular security assessments</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Data Flow */}
      <section className="info-section">
        <h3>
          <Database size={20} />
          Data Flow Process
        </h3>
        
        <div className="data-flow">
          <div className="flow-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>Data Entry</h4>
              <p>User enters PII data through secure web form with HTTPS encryption</p>
            </div>
          </div>
          
          <div className="flow-arrow">→</div>
          
          <div className="flow-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>Classification</h4>
              <p>FastAPI backend classifies each field by PII sensitivity level</p>
            </div>
          </div>
          
          <div className="flow-arrow">→</div>
          
          <div className="flow-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Encryption</h4>
              <p>Lambda function applies appropriate encryption based on PII level</p>
            </div>
          </div>
          
          <div className="flow-arrow">→</div>
          
          <div className="flow-step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h4>Storage</h4>
              <p>Encrypted data stored in RDS Aurora with additional at-rest encryption</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <div className="info-footer">
        <div className="footer-notice">
          <Shield size={16} />
          <p>
            This system is designed for demonstration purposes and showcases 
            security best practices for handling PII in cloud environments.
            For production use, additional security hardening would be required.
          </p>
        </div>
      </div>
    </div>
  )
}

export default SecurityInfo