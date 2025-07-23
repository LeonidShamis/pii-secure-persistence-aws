/**
 * UserList Component
 * Display list of users with click-to-view functionality
 */

import { useState, useEffect } from 'react'
import { Users, RefreshCw, Eye, AlertCircle, Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../services/api'

function UserList({ onViewUser }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [pagination, setPagination] = useState({
    limit: 10,
    offset: 0,
    total: 0
  })
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchUsers()
  }, [pagination.limit, pagination.offset])

  const fetchUsers = async () => {
    if (loading) return

    setLoading(true)
    setError(null)
    
    try {
      console.log(`📋 Fetching users: limit=${pagination.limit}, offset=${pagination.offset}`)
      const response = await api.listUsers(pagination.limit, pagination.offset)
      
      if (response.success && response.data) {
        setUsers(response.data.users || [])
        setPagination(prev => ({
          ...prev,
          total: response.data.total || 0
        }))
      } else {
        throw new Error('Invalid response format')
      }
    } catch (err) {
      console.error('❌ Error fetching users:', err)
      setError(err.message || 'Failed to load users')
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    fetchUsers()
  }

  const handleViewUser = (userId) => {
    onViewUser(userId)
  }

  const handlePageChange = (newOffset) => {
    setPagination(prev => ({
      ...prev,
      offset: newOffset
    }))
  }

  const handleLimitChange = (newLimit) => {
    setPagination(prev => ({
      ...prev,
      limit: parseInt(newLimit),
      offset: 0 // Reset to first page
    }))
  }

  const filteredUsers = users.filter(user => {
    if (!searchQuery) return true
    
    const query = searchQuery.toLowerCase()
    return (
      user.user_id?.toLowerCase().includes(query) ||
      user.email?.toLowerCase().includes(query) ||
      user.first_name?.toLowerCase().includes(query) ||
      user.last_name?.toLowerCase().includes(query)
    )
  })

  const currentPage = Math.floor(pagination.offset / pagination.limit) + 1
  const totalPages = Math.ceil(pagination.total / pagination.limit)
  const hasNextPage = pagination.offset + pagination.limit < pagination.total
  const hasPrevPage = pagination.offset > 0

  return (
    <div className="user-list">
      <div className="list-header">
        <div className="header-content">
          <h2>
            <Users size={24} />
            User Directory
          </h2>
          <p>Browse all users in the system. Click on any user to view their full encrypted details.</p>
        </div>
      </div>

      {/* Controls */}
      <div className="list-controls">
        <div className="search-section">
          <div className="search-input-group">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID, email, or name..."
              className="search-input"
            />
          </div>
        </div>

        <div className="control-actions">
          <select
            value={pagination.limit}
            onChange={(e) => handleLimitChange(e.target.value)}
            className="limit-select"
          >
            <option value="5">5 per page</option>
            <option value="10">10 per page</option>
            <option value="25">25 per page</option>
            <option value="50">50 per page</option>
          </select>

          <button
            onClick={handleRefresh}
            disabled={loading}
            className="btn btn-secondary"
          >
            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* User Table */}
      <div className="users-table-container">
        {loading && users.length === 0 ? (
          <div className="loading-state">
            <RefreshCw size={24} className="spinning" />
            <p>Loading users...</p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="empty-state">
            <Users size={48} />
            <h3>No Users Found</h3>
            <p>
              {searchQuery 
                ? `No users match "${searchQuery}". Try a different search term.`
                : 'No users have been created yet. Create your first user to get started.'
              }
            </p>
          </div>
        ) : (
          <table className="users-table">
            <thead>
              <tr>
                <th>User ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.user_id} className="user-row">
                  <td className="user-id">
                    <code>{user.user_id}</code>
                  </td>
                  <td className="user-name">
                    <div className="name-display">
                      <span className="full-name">
                        {user.first_name} {user.last_name}
                      </span>
                      <div className="pii-indicators">
                        <span className="pii-badge level-1">🟢 L1</span>
                      </div>
                    </div>
                  </td>
                  <td className="user-email">
                    <span className="email-display">{user.email}</span>
                    <span className="pii-badge level-1">🟢 L1</span>
                  </td>
                  <td className="created-date">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                  </td>
                  <td className="user-actions">
                    <button
                      onClick={() => handleViewUser(user.user_id)}
                      className="btn btn-primary btn-sm"
                      title="View full user details"
                    >
                      <Eye size={14} />
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {filteredUsers.length > 0 && (
        <div className="pagination">
          <div className="pagination-info">
            <span>
              Showing {Math.min(pagination.offset + 1, pagination.total)} to{' '}
              {Math.min(pagination.offset + pagination.limit, pagination.total)} of{' '}
              {pagination.total} users
              {searchQuery && ` (filtered from ${users.length})`}
            </span>
          </div>

          <div className="pagination-controls">
            <button
              onClick={() => handlePageChange(pagination.offset - pagination.limit)}
              disabled={!hasPrevPage || loading}
              className="btn btn-secondary btn-sm"
            >
              <ChevronLeft size={16} />
              Previous
            </button>

            <span className="page-info">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => handlePageChange(pagination.offset + pagination.limit)}
              disabled={!hasNextPage || loading}
              className="btn btn-secondary btn-sm"
            >
              Next
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      <div className="list-footer">
        <div className="footer-notice">
          <span className="security-notice">
            🔒 Only Level 1 (non-sensitive) data is displayed in the list view.
            Click "View Details" to access encrypted data with proper authentication.
          </span>
        </div>
      </div>
    </div>
  )
}

export default UserList