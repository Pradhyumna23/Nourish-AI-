import React, { useState, useEffect } from 'react'
import { nutritionAPI } from '../services/api'
import Card from './ui/Card'
import LoadingSpinner from './ui/LoadingSpinner'

const NutritionSummary = ({ date = new Date().toISOString().split('T')[0] }) => {
  const [recommendations, setRecommendations] = useState(null)
  const [weeklySummary, setWeeklySummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('recommendations')

  useEffect(() => {
    fetchNutritionData()
  }, [date])

  const fetchNutritionData = async () => {
    try {
      setLoading(true)
      const [recResponse, weeklyResponse] = await Promise.all([
        nutritionAPI.getRecommendations(date),
        nutritionAPI.getWeeklySummary(1)
      ])
      setRecommendations(recResponse.data)
      setWeeklySummary(weeklyResponse.data)
    } catch (error) {
      console.error('Failed to fetch nutrition data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'border-red-500 bg-red-50'
      case 'medium': return 'border-yellow-500 bg-yellow-50'
      case 'low': return 'border-green-500 bg-green-50'
      default: return 'border-gray-300 bg-gray-50'
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'meal_suggestion': return '🍽️'
      case 'nutrient_focus': return '💊'
      case 'hydration': return '💧'
      case 'goal_specific': return '🎯'
      case 'activity_suggestion': return '🏃'
      case 'health_alert': return '🏥'
      case 'safety_alert': return '⚠️'
      default: return '📋'
    }
  }

  const getSafetyBadgeColor = (warnings) => {
    if (!warnings || warnings.length === 0) return 'bg-green-100 text-green-800'
    return 'bg-red-100 text-red-800'
  }

  if (loading) {
    return (
      <Card className="p-6">
        <LoadingSpinner />
        <p className="text-center mt-4">Loading nutrition insights...</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-8">
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm text-center sm:text-left ${
              activeTab === 'recommendations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="hidden sm:inline">Today's Recommendations</span>
            <span className="sm:hidden">Recommendations</span>
          </button>
          <button
            onClick={() => setActiveTab('weekly')}
            className={`py-2 px-1 border-b-2 font-medium text-sm text-center sm:text-left ${
              activeTab === 'weekly'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Weekly Summary
          </button>
        </nav>
      </div>

      {/* Recommendations Tab */}
      {activeTab === 'recommendations' && recommendations && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Personalized Nutrition Recommendations
            </h3>
            <span className="text-sm text-gray-500">
              {recommendations.summary?.total_recommendations} recommendations
            </span>
          </div>

          <div className="grid gap-3 sm:gap-4">
            {recommendations.recommendations?.map((rec, index) => (
              <Card key={index} className={`p-3 sm:p-4 border-l-4 ${getPriorityColor(rec.priority)}`}>
                <div className="flex items-start space-x-3">
                  <span className="text-xl sm:text-2xl flex-shrink-0">{getTypeIcon(rec.type)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <h4 className="font-semibold text-gray-900 truncate">{rec.title}</h4>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full self-start sm:self-auto ${
                        rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                        rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {rec.priority} priority
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1 text-sm sm:text-base">{rec.description}</p>
                    
                    {/* Safety Note */}
                    {rec.safety_note && (
                      <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-sm">
                        <div className="flex items-center space-x-2">
                          <span className="text-blue-600">🛡️</span>
                          <span className="text-blue-800 font-medium">Safety Note:</span>
                        </div>
                        <p className="text-blue-700 mt-1">{rec.safety_note}</p>
                      </div>
                    )}

                    {/* Suggested Foods */}
                    {rec.suggested_foods && rec.suggested_foods.length > 0 && (
                      <div className="mt-3">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Suggested Foods:</h5>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                          {rec.suggested_foods.map((food, foodIndex) => (
                            <div key={foodIndex} className="bg-white p-2 rounded border text-sm relative">
                              <div className="font-medium truncate">{food.name}</div>
                              <div className="text-gray-500 text-xs truncate">
                                {food.calories && `${food.calories} cal`}
                                {food.protein_g && ` • ${food.protein_g}g protein`}
                                {food.fiber_g && ` • ${food.fiber_g}g fiber`}
                              </div>

                              {/* Safety indicators */}
                              <div className="flex flex-wrap gap-1 mt-1">
                                {food.tags && food.tags.includes('vegan') && (
                                  <span className="px-1 py-0.5 text-xs bg-green-100 text-green-700 rounded">🌱 Vegan</span>
                                )}
                                {food.tags && food.tags.includes('vegetarian') && !food.tags.includes('vegan') && (
                                  <span className="px-1 py-0.5 text-xs bg-green-100 text-green-700 rounded">🥬 Vegetarian</span>
                                )}
                                {food.tags && food.tags.includes('gluten_free') && (
                                  <span className="px-1 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">🌾 Gluten-Free</span>
                                )}
                                {food.warnings && food.warnings.length > 0 && (
                                  <span className="px-1 py-0.5 text-xs bg-red-100 text-red-700 rounded">⚠️ Warning</span>
                                )}
                              </div>

                              {/* Warning details */}
                              {food.warnings && food.warnings.length > 0 && (
                                <div className="mt-1 text-xs text-red-600">
                                  {food.warnings.map((warning, wIndex) => (
                                    <div key={wIndex}>{warning}</div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Suggested Activities */}
                    {rec.suggested_activities && rec.suggested_activities.length > 0 && (
                      <div className="mt-3">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Suggested Activities:</h5>
                        <div className="space-y-1">
                          {rec.suggested_activities.map((activity, actIndex) => (
                            <div key={actIndex} className="bg-white p-2 rounded border text-sm">
                              <span className="font-medium">{activity.name}</span>
                              <span className="text-gray-500 ml-2">
                                {activity.duration} • {activity.calories_burned} cal burned
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Timing Info */}
                    {rec.suggested_timing && (
                      <div className="mt-2 text-sm text-blue-600">
                        ⏰ {rec.suggested_timing}
                      </div>
                    )}

                    {/* Amount Info */}
                    {rec.suggested_amount && (
                      <div className="mt-2 text-sm text-blue-600">
                        💧 {rec.suggested_amount}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Summary Stats */}
          {recommendations.summary && (
            <Card className="p-4 bg-blue-50">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {recommendations.summary.calories_remaining}
                  </div>
                  <div className="text-sm text-gray-600">Calories Remaining</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {recommendations.summary.protein_remaining}g
                  </div>
                  <div className="text-sm text-gray-600">Protein Needed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {recommendations.summary.high_priority}
                  </div>
                  <div className="text-sm text-gray-600">High Priority</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {recommendations.summary.total_recommendations}
                  </div>
                  <div className="text-sm text-gray-600">Total Tips</div>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Weekly Summary Tab */}
      {activeTab === 'weekly' && weeklySummary && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Weekly Nutrition Summary</h3>
            <span className="text-sm text-gray-500">
              {weeklySummary.days_logged} days logged
            </span>
          </div>

          {/* Averages vs Targets */}
          <Card className="p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Average Daily Intake vs Targets</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {['calories', 'protein_g', 'carbs_g', 'fat_g'].map((nutrient) => {
                const average = weeklySummary.averages[nutrient]
                const target = weeklySummary.targets[nutrient]
                const percentage = target > 0 ? (average / target) * 100 : 0
                
                return (
                  <div key={nutrient} className="text-center">
                    <div className="text-lg font-bold text-gray-900">
                      {average.toFixed(1)}{nutrient === 'calories' ? '' : 'g'}
                    </div>
                    <div className="text-sm text-gray-500">
                      / {target.toFixed(1)}{nutrient === 'calories' ? '' : 'g'}
                    </div>
                    <div className={`text-sm font-medium ${
                      percentage >= 80 && percentage <= 120 ? 'text-green-600' :
                      percentage >= 60 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {percentage.toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-400 capitalize">
                      {nutrient.replace('_g', '').replace('_', ' ')}
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>

          {/* Adherence Scores */}
          <Card className="p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Adherence Scores</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {weeklySummary.adherence.calorie_adherence.toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">Calorie Target</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {weeklySummary.adherence.protein_adherence.toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">Protein Target</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {weeklySummary.adherence.consistency_score.toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">Consistency</div>
              </div>
            </div>
          </Card>

          {/* Weekly Insights */}
          {weeklySummary.insights && weeklySummary.insights.length > 0 && (
            <Card className="p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Weekly Insights</h4>
              <div className="space-y-3">
                {weeklySummary.insights.map((insight, index) => (
                  <div key={index} className={`p-3 rounded-lg border-l-4 ${
                    insight.type === 'concern' ? 'border-red-500 bg-red-50' :
                    insight.type === 'warning' ? 'border-yellow-500 bg-yellow-50' :
                    insight.type === 'suggestion' ? 'border-blue-500 bg-blue-50' :
                    'border-green-500 bg-green-50'
                  }`}>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium capitalize">{insight.type}</span>
                      <span className="text-xs text-gray-500">• {insight.category}</span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{insight.message}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default NutritionSummary
