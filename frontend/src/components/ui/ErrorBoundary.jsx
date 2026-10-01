import React, { Component } from 'react'
import ErrorState from './ErrorState'

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.warn('[ErrorBoundary] Caught component render error:', {
      error: error?.message || error,
      componentStack: errorInfo?.componentStack,
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    if (this.props.onReset) {
      this.props.onReset()
    } else {
      window.location.reload()
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="w-full py-12 flex items-center justify-center p-4">
          <ErrorState
            title={this.props.title || 'Something went wrong displaying this view'}
            message={
              this.props.message ||
              "An unexpected error occurred while rendering this page. You can try refreshing or returning to the dashboard."
            }
            onRetry={this.handleReset}
            retryLabel="Reload View"
          />
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
