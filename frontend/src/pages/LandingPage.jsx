import React from 'react'
import { Link } from 'react-router-dom'

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            🍎 <span className="text-blue-600">NourishAI</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 mb-8">
            Your AI-Powered Nutrition Companion
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="p-6 bg-blue-50 rounded-lg">
              <div className="text-3xl mb-4">🤖</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Recommendations</h3>
              <p className="text-gray-600">Get personalized nutrition advice powered by Google Gemini AI</p>
            </div>
            
            <div className="p-6 bg-green-50 rounded-lg">
              <div className="text-3xl mb-4">🍽️</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Food Search</h3>
              <p className="text-gray-600">Access 26,000+ real foods from USDA database</p>
            </div>
            
            <div className="p-6 bg-purple-50 rounded-lg">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Nutrition Tracking</h3>
              <p className="text-gray-600">Track calories, macros, and micronutrients with precision</p>
            </div>
          </div>
          
          <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
            <Link
              to="/register"
              className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition duration-200 inline-block"
            >
              Get Started Free
            </Link>
            
            <Link
              to="/login"
              className="w-full sm:w-auto bg-white hover:bg-gray-50 text-blue-600 font-semibold py-3 px-8 rounded-lg border-2 border-blue-600 transition duration-200 inline-block"
            >
              Sign In
            </Link>
          </div>
          
          <div className="mt-12 pt-8 border-t border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">✨ Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start space-x-3">
                <span className="text-green-500 font-bold">✓</span>
                <span className="text-gray-700">AI-powered food recommendations</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-500 font-bold">✓</span>
                <span className="text-gray-700">Complete meal planning</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-500 font-bold">✓</span>
                <span className="text-gray-700">Nutrient-based food suggestions</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-500 font-bold">✓</span>
                <span className="text-gray-700">Allergy and dietary restriction support</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-500 font-bold">✓</span>
                <span className="text-gray-700">Real USDA nutrition database</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-500 font-bold">✓</span>
                <span className="text-gray-700">Persistent data storage</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
