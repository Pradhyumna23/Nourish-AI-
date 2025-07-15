import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

const Navbar = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="glass-effect sticky top-0 z-50 backdrop-blur-lg border-b border-white/20 animate-fadeInUp">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 group">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-12 h-12 gradient-primary rounded-2xl flex items-center justify-center group-hover:scale-110 transition-all duration-300 shadow-lg">
                    <span className="text-white font-bold text-xl animate-float">🥗</span>
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full animate-pulse"></div>
                </div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  NourishAI
                </h1>
              </div>
            </Link>
            
            {user && (
              <div className="hidden sm:ml-8 sm:flex sm:space-x-2">
                <Link
                  to="/dashboard"
                  className="group relative px-4 py-2 rounded-xl text-sm font-semibold text-gray-700 hover:text-white transition-all duration-300 hover:scale-105"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>📊</span>
                    <span>Dashboard</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </Link>
                <Link
                  to="/recommendations"
                  className="group relative px-4 py-2 rounded-xl text-sm font-semibold text-gray-700 hover:text-white transition-all duration-300 hover:scale-105"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>🎯</span>
                    <span>Recommendations</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-teal-600 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </Link>
                <Link
                  to="/food-recommendations"
                  className="group relative px-4 py-2 rounded-xl text-sm font-semibold text-gray-700 hover:text-white transition-all duration-300 hover:scale-105"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>🍎</span>
                    <span>Smart Foods</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-500 to-red-600 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </Link>
                <Link
                  to="/food-log"
                  className="group relative px-4 py-2 rounded-xl text-sm font-semibold text-gray-700 hover:text-white transition-all duration-300 hover:scale-105"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>📝</span>
                    <span>Food Log</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </Link>
                <Link
                  to="/profile"
                  className="group relative px-4 py-2 rounded-xl text-sm font-semibold text-gray-700 hover:text-white transition-all duration-300 hover:scale-105"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>👤</span>
                    <span>Profile</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-500 to-rose-600 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </Link>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-4">
                <div className="hidden sm:flex items-center space-x-3 bg-gradient-to-r from-purple-50 to-blue-50 px-4 py-2 rounded-full border border-purple-200">
                  <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">{user.first_name?.charAt(0)}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    Welcome, {user.first_name}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="group relative px-6 py-2 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-semibold text-sm transition-all duration-300 hover:scale-105 hover:shadow-lg"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>🚪</span>
                    <span>Logout</span>
                  </span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="px-6 py-2 text-gray-700 hover:text-purple-600 text-sm font-semibold transition-all duration-300 hover:scale-105"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="group relative px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold text-sm transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-xl"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>✨</span>
                    <span>Sign Up</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-700 to-blue-700 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
