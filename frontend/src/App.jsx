import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'

// Pages
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import Recommendations from './pages/Recommendations'
import FoodRecommendations from './pages/FoodRecommendations'
import FoodLog from './pages/FoodLog'

// Components
import Layout from './components/Layout'
import ChatbotButton from './components/ChatbotButton'

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" />
}

// Public Route Component (redirect to dashboard if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return !isAuthenticated ? children : <Navigate to="/dashboard" />
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Public Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Layout>
                  <Profile />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/food-log"
            element={
              <ProtectedRoute>
                <Layout>
                  <FoodLog />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <Layout>
                  <Recommendations />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/food-recommendations"
            element={
              <ProtectedRoute>
                <Layout>
                  <FoodRecommendations />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Landing page */}
          <Route path="/" element={<LandingPage />} />

          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
        <Toaster position="top-right" />

        {/* Global Chatbot - only show when authenticated */}
        <ChatbotButton />
      </div>
    </Router>
  )
}

export default App
