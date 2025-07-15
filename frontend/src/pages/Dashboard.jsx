import React, { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { useFoodStore } from '../store/foodStore'
import { Link } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import NutritionSummary from '../components/NutritionSummary'
import HealthProfile from '../components/HealthProfile'
import Chatbot from '../components/Chatbot'

const Dashboard = () => {
  const { user } = useAuthStore()
  const { dailyNutrition, isDailyLoading, getDailyNutrition } = useFoodStore()
  const [todayDate] = useState(new Date().toISOString().split('T')[0])
  const [activeTab, setActiveTab] = useState('overview')
  const [isChatOpen, setIsChatOpen] = useState(false)

  useEffect(() => {
    if (user) {
      getDailyNutrition(todayDate)
    }
  }, [user, getDailyNutrition, todayDate])

  const calculateProgress = (actual, target) => {
    if (!target || target === 0) return 0
    return Math.min((actual / target) * 100, 100)
  }

  const getProgressColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-500'
    if (percentage >= 60) return 'bg-yellow-500'
    if (percentage >= 40) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8 sm:mb-12 text-center animate-fadeInUp">
          <div className="relative inline-block">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4 px-4">
              Welcome back, {user?.first_name}! 👋
            </h1>
            <div className="absolute -top-2 -right-2 w-4 h-4 sm:w-6 sm:h-6 bg-yellow-400 rounded-full animate-pulse"></div>
          </div>
          <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed px-4">
            Here's your personalized nutrition overview for today. Let's make it amazing! ✨
          </p>
          <div className="mt-6 flex flex-col sm:flex-row justify-center items-center gap-3 sm:gap-4 px-4">
            <div className="bg-white/60 backdrop-blur-sm px-3 sm:px-4 py-2 rounded-full border border-white/20 w-full sm:w-auto text-center">
              <span className="text-xs sm:text-sm font-medium text-gray-700">📅 {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
            </div>
            <div className="bg-white/60 backdrop-blur-sm px-3 sm:px-4 py-2 rounded-full border border-white/20 w-full sm:w-auto text-center">
              <span className="text-xs sm:text-sm font-medium text-gray-700">🎯 Daily Goals Active</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8 sm:mb-12 animate-slideInRight px-4">
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-2 border border-white/20 shadow-lg max-w-lg mx-auto">
            <nav className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
              <button
                onClick={() => setActiveTab('overview')}
                className={`flex-1 py-3 px-4 sm:px-6 rounded-xl font-semibold text-sm transition-all duration-300 ${
                  activeTab === 'overview'
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>📊</span>
                  <span className="hidden xs:inline">Overview</span>
                  <span className="xs:hidden">Stats</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('health-profile')}
                className={`flex-1 py-3 px-4 sm:px-6 rounded-xl font-semibold text-sm transition-all duration-300 ${
                  activeTab === 'health-profile'
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>🏥</span>
                  <span className="hidden xs:inline">Health Profile</span>
                  <span className="xs:hidden">Health</span>
                </span>
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="animate-fadeInUp">
            {/* Today's Progress */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8 mb-8 sm:mb-12 px-4">
              <div className="xl:col-span-2">
                <div className="card-enhanced bg-gradient-to-br from-white to-blue-50 border-0 shadow-2xl">
                  <div className="p-4 sm:p-6 lg:p-8">
                    <div className="flex items-center justify-between mb-8">
                      <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                        Today's Nutrition Progress
                      </h2>
                      <div className="bg-gradient-to-r from-green-400 to-blue-500 text-white px-4 py-2 rounded-full text-sm font-semibold animate-pulse">
                        Live Tracking
                      </div>
                    </div>

                    {isDailyLoading ? (
                      <LoadingSpinner center text="Loading nutrition data..." />
                    ) : dailyNutrition ? (
                      <div className="space-y-6">
                        {/* Daily Overview Cards */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
                          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-3 sm:p-4 rounded-lg border border-blue-200">
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-blue-600 uppercase tracking-wide">Calories</p>
                                <p className="text-xl sm:text-2xl font-bold text-blue-900 truncate">
                                  {Math.round(dailyNutrition.total_calories || 0)}
                                </p>
                                <p className="text-xs text-blue-700 truncate">
                                  of {dailyNutrition.target_calories || 2000} goal
                                </p>
                              </div>
                              <div className="text-blue-500 ml-2">
                                <span className="text-xl sm:text-2xl">🔥</span>
                              </div>
                            </div>
                          </div>

                          <div className="bg-gradient-to-r from-green-50 to-green-100 p-3 sm:p-4 rounded-lg border border-green-200">
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-green-600 uppercase tracking-wide">Protein</p>
                                <p className="text-xl sm:text-2xl font-bold text-green-900 truncate">
                                  {Math.round(dailyNutrition.total_protein_g || 0)}g
                                </p>
                                <p className="text-xs text-green-700 truncate">
                                  of {dailyNutrition.target_protein_g || 150}g goal
                                </p>
                              </div>
                              <div className="text-green-500 ml-2">
                                <span className="text-xl sm:text-2xl">💪</span>
                              </div>
                            </div>
                          </div>

                          <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-3 sm:p-4 rounded-lg border border-orange-200">
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-orange-600 uppercase tracking-wide">Carbs</p>
                                <p className="text-xl sm:text-2xl font-bold text-orange-900 truncate">
                                  {Math.round(dailyNutrition.total_carbs_g || 0)}g
                                </p>
                                <p className="text-xs text-orange-700 truncate">
                                  of {dailyNutrition.target_carbs_g || 250}g goal
                                </p>
                              </div>
                              <div className="text-orange-500 ml-2">
                                <span className="text-xl sm:text-2xl">🌾</span>
                              </div>
                            </div>
                          </div>

                          <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-3 sm:p-4 rounded-lg border border-purple-200">
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-purple-600 uppercase tracking-wide">Fat</p>
                                <p className="text-xl sm:text-2xl font-bold text-purple-900 truncate">
                                  {Math.round(dailyNutrition.total_fat_g || 0)}g
                                </p>
                                <p className="text-xs text-purple-700 truncate">
                                  of {dailyNutrition.target_fat_g || 65}g goal
                                </p>
                              </div>
                              <div className="text-purple-500 ml-2">
                                <span className="text-xl sm:text-2xl">🥑</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Progress Bars */}
                        <div className="space-y-4">
                          <div className="bg-gray-50 p-3 sm:p-4 rounded-lg">
                            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-3 gap-1">
                              <span className="text-sm font-semibold text-gray-800">🔥 Calories</span>
                              <span className="text-sm font-bold text-gray-900">
                                {Math.round(dailyNutrition.total_calories || 0)} / {dailyNutrition.target_calories || 2000}
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 sm:h-3">
                              <div
                                className={`h-2 sm:h-3 rounded-full transition-all duration-500 ${getProgressColor(
                                  calculateProgress(dailyNutrition.total_calories, dailyNutrition.target_calories || 2000)
                                )}`}
                                style={{
                                  width: `${Math.min(calculateProgress(dailyNutrition.total_calories, dailyNutrition.target_calories || 2000), 100)}%`
                                }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-gray-500">No nutrition data available for today</p>
                        <Link to="/food-log">
                          <Button className="mt-4">Start Logging Food</Button>
                        </Link>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="animate-slideInRight">
                <div className="card-enhanced bg-gradient-to-br from-white to-purple-50 border-0 shadow-2xl">
                  <div className="p-4 sm:p-6 lg:p-8">
                    <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-6 sm:mb-8 flex items-center">
                      <span className="mr-2 sm:mr-3">⚡</span>
                      Quick Actions
                    </h2>
                    <div className="space-y-3 sm:space-y-4">
                      <Link to="/food-log" className="block group">
                        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 sm:p-4 rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-xl">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                              <span className="text-xl sm:text-2xl">📝</span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <h3 className="font-semibold text-base sm:text-lg truncate">Log Food</h3>
                              <p className="text-blue-100 text-xs sm:text-sm truncate">Track your meals</p>
                            </div>
                          </div>
                        </div>
                      </Link>

                      <Link to="/recommendations" className="block group">
                        <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-3 sm:p-4 rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-xl">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                              <span className="text-xl sm:text-2xl">🎯</span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <h3 className="font-semibold text-base sm:text-lg truncate">Get Recommendations</h3>
                              <p className="text-green-100 text-xs sm:text-sm truncate">AI-powered advice</p>
                            </div>
                          </div>
                        </div>
                      </Link>

                      <Link to="/food-recommendations" className="block group">
                        <div className="bg-gradient-to-r from-orange-500 to-red-600 text-white p-3 sm:p-4 rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-xl">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                              <span className="text-xl sm:text-2xl">🍎</span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <h3 className="font-semibold text-base sm:text-lg truncate">Smart Foods</h3>
                              <p className="text-orange-100 text-xs sm:text-sm truncate">Discover new foods</p>
                            </div>
                          </div>
                        </div>
                      </Link>

                      <div
                        onClick={() => setIsChatOpen(true)}
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-3 sm:p-4 rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-xl cursor-pointer group"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                            <span className="text-xl sm:text-2xl">🤖</span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 className="font-semibold text-base sm:text-lg truncate">Ask NourishAI</h3>
                            <p className="text-indigo-100 text-xs sm:text-sm truncate">Chat with AI assistant</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Nutrition Summary */}
            <div className="mt-6 sm:mt-8 px-4">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Nutrition Insights</h2>
              <NutritionSummary date={todayDate} />
            </div>
          </div>
        )}

        {/* Health Profile Tab */}
        {activeTab === 'health-profile' && (
          <HealthProfile />
        )}
      </div>

      {/* Chatbot Modal */}
      <Chatbot
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  )
}

export default Dashboard
