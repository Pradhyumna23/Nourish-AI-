import React, { useEffect, useState } from 'react'
import { useRecommendationStore } from '../store/recommendationStore'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import LoadingSpinner from '../components/ui/LoadingSpinner'

const Recommendations = () => {
  const {
    recommendations,
    isLoading,
    isGenerating,
    selectedRecommendation,
    generateRecommendations,
    getRecommendations,
    getRecommendationDetails,
    submitFeedback,
    clearSelectedRecommendation
  } = useRecommendationStore()
  const [feedbackData, setFeedbackData] = useState({
    is_accepted: null,
    rating: null,
    feedback: ''
  })
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)

  useEffect(() => {
    getRecommendations()
  }, [getRecommendations])

  const handleGenerateRecommendations = async () => {
    try {
      await generateRecommendations()
    } catch (error) {
      console.error('Failed to generate recommendations:', error)
    }
  }



  const handleSubmitFeedback = async (e) => {
    e.preventDefault()
    if (!selectedRecommendation) return

    try {
      await submitFeedback(selectedRecommendation.id, feedbackData)
      setShowFeedbackModal(false)
      setFeedbackData({
        is_accepted: null,
        rating: null,
        feedback: ''
      })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 1: return 'bg-danger-100 text-danger-800'
      case 2: return 'bg-warning-100 text-warning-800'
      case 3: return 'bg-primary-100 text-primary-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityText = (priority) => {
    switch (priority) {
      case 1: return 'Critical'
      case 2: return 'High'
      case 3: return 'Medium'
      default: return 'Low'
    }
  }

  const getConfidenceColor = (confidence) => {
    if (confidence === 'high') return 'text-success-600'
    if (confidence === 'medium') return 'text-warning-600'
    return 'text-danger-600'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
          <div className="text-center max-w-4xl mx-auto">
            <div className="flex justify-center mb-4">
              <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
                <span className="text-4xl sm:text-5xl">🤖</span>
              </div>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6">
              AI Nutrition Recommendations
            </h1>
            <p className="text-lg sm:text-xl text-purple-100 max-w-2xl mx-auto leading-relaxed mb-6 sm:mb-8">
              Get personalized nutrition recommendations powered by AI and nutritional science
            </p>
            <Button
              onClick={handleGenerateRecommendations}
              loading={isGenerating}
              disabled={isGenerating}
              variant="secondary"
              className="bg-white text-purple-600 hover:bg-gray-100 px-6 sm:px-8 py-3 text-lg font-semibold"
            >
              {isGenerating ? (
                <div className="flex items-center gap-2">
                  <LoadingSpinner size="sm" />
                  <span>Generating...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span>✨</span>
                  <span>Generate New Recommendations</span>
                </div>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">

        {isLoading ? (
          <Card className="text-center py-12">
            <LoadingSpinner size="lg" text="Loading your personalized recommendations..." />
          </Card>
        ) : recommendations.length > 0 ? (
          <div className="space-y-6">
            {recommendations.map((rec) => (
              <Card key={rec.id} className="group hover:shadow-xl transition-all duration-300 hover:scale-[1.02] overflow-hidden">
                {/* Card Header */}
                <div className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white p-4 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <h3 className="text-lg sm:text-xl font-bold">{rec.title}</h3>
                        <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getPriorityColor(rec.priority)} bg-white/20 text-white border border-white/30`}>
                          {getPriorityText(rec.priority)} Priority
                        </span>
                        {!rec.is_viewed && (
                          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-yellow-400 text-yellow-900">
                            ✨ New
                          </span>
                        )}
                      </div>
                      <p className="text-purple-100 leading-relaxed">{rec.description}</p>
                    </div>
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-4 sm:p-6">
                  {/* Recommendation Stats */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 p-3 rounded-lg text-center">
                      <div className="text-xs font-medium text-blue-600 mb-1">Confidence</div>
                      <div className={`text-sm font-bold ${getConfidenceColor(rec.confidence_level)}`}>
                        {rec.confidence_level.toUpperCase()}
                      </div>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg text-center">
                      <div className="text-xs font-medium text-green-600 mb-1">Impact</div>
                      <div className="text-sm font-bold text-green-800">{rec.expected_impact}</div>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center">
                      <div className="text-xs font-medium text-orange-600 mb-1">Difficulty</div>
                      <div className="text-sm font-bold text-orange-800">{rec.implementation_difficulty}</div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg text-center">
                      <div className="text-xs font-medium text-purple-600 mb-1">Created</div>
                      <div className="text-sm font-bold text-purple-800">
                        {new Date(rec.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-col sm:flex-row gap-3">
                    {rec.is_viewed && rec.is_accepted === null && (
                      <Button
                        onClick={() => {
                          getRecommendationDetails(rec.id).then(() => {
                            setShowFeedbackModal(true)
                          })
                        }}
                        variant="gradient"
                        className="flex-1 sm:flex-none"
                      >
                        <span className="mr-2">💬</span>
                        Provide Feedback
                      </Button>
                    )}
                  </div>
                </div>

              {/* Quick preview of recommendation content */}
              {rec.recommendation_type === 'NUTRIENT_ADJUSTMENT' && rec.nutrient_adjustments && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Nutrient Adjustments:</h4>
                  <div className="space-y-2">
                    {rec.nutrient_adjustments.slice(0, 3).map((adj, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <span className="text-gray-700">
                          {adj.nutrient_name.replace('_', ' ')}: {adj.adjustment_direction} by {adj.adjustment_amount}{adj.unit}
                        </span>
                        <span className="text-gray-500">{adj.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {rec.recommendation_type === 'FOOD_SUGGESTION' && rec.food_suggestions && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Food Suggestions:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {rec.food_suggestions.slice(0, 4).map((food, index) => (
                      <div key={index} className="text-sm">
                        <span className="font-medium text-gray-700">{food.food_name}</span>
                        <span className="text-gray-500 ml-2">
                          ({food.serving_size} {food.serving_unit}, {food.calories} cal)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {rec.user_rating && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-500">Your rating:</span>
                    <div className="flex space-x-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <svg
                          key={star}
                          className={`w-4 h-4 ${
                            star <= rec.user_rating ? 'text-yellow-400' : 'text-gray-300'
                          }`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                    <span className={`text-sm px-2 py-1 rounded ${
                      rec.is_accepted ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'
                    }`}>
                      {rec.is_accepted ? 'Accepted' : 'Declined'}
                    </span>
                  </div>
                </div>
              )}
            </Card>
          ))}
          </div>
        ) : (
          <Card className="text-center py-12 sm:py-16">
            <div className="max-w-md mx-auto">
              <div className="text-6xl sm:text-7xl mb-6">🤖</div>
              <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">
                Ready for AI Recommendations?
              </h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Generate your first AI-powered nutrition recommendations based on your profile, goals, and current nutrition status.
              </p>
              <Button
                onClick={handleGenerateRecommendations}
                loading={isGenerating}
                disabled={isGenerating}
                variant="gradient"
                className="px-8 py-3 text-lg font-semibold"
              >
                {isGenerating ? (
                  <div className="flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    <span>Generating...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span>✨</span>
                    <span>Generate AI Recommendations</span>
                  </div>
                )}
              </Button>
            </div>
          </Card>
        )}
      </div>



      {/* Feedback Modal */}
      <Modal
        isOpen={showFeedbackModal}
        onClose={() => {
          setShowFeedbackModal(false)
          setFeedbackData({
            is_accepted: null,
            rating: null,
            feedback: ''
          })
        }}
      >
        <Modal.Header>
          <Modal.Title>Provide Feedback</Modal.Title>
        </Modal.Header>
        <Modal.Content>
          <form onSubmit={handleSubmitFeedback} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Do you accept this recommendation?
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="is_accepted"
                    value="true"
                    checked={feedbackData.is_accepted === true}
                    onChange={() => setFeedbackData(prev => ({ ...prev, is_accepted: true }))}
                    className="mr-2"
                  />
                  Yes, I accept
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="is_accepted"
                    value="false"
                    checked={feedbackData.is_accepted === false}
                    onChange={() => setFeedbackData(prev => ({ ...prev, is_accepted: false }))}
                    className="mr-2"
                  />
                  No, I decline
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rate this recommendation (1-5 stars)
              </label>
              <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setFeedbackData(prev => ({ ...prev, rating: star }))}
                    className={`w-8 h-8 ${
                      star <= (feedbackData.rating || 0) ? 'text-yellow-400' : 'text-gray-300'
                    }`}
                  >
                    <svg fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional feedback (optional)
              </label>
              <textarea
                value={feedbackData.feedback}
                onChange={(e) => setFeedbackData(prev => ({ ...prev, feedback: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Share your thoughts about this recommendation..."
              />
            </div>
          </form>
        </Modal.Content>
        <Modal.Footer>
          <Button
            variant="outline"
            onClick={() => {
              setShowFeedbackModal(false)
              setFeedbackData({
                is_accepted: null,
                rating: null,
                feedback: ''
              })
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmitFeedback}
            disabled={feedbackData.is_accepted === null || !feedbackData.rating}
          >
            Submit Feedback
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  )
}

export default Recommendations
