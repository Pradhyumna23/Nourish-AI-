import React, { useState, useEffect } from 'react'
import api from '../services/api'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import LoadingSpinner from '../components/ui/LoadingSpinner'

// Enhanced icons using emoji with better styling
const LoaderIcon = () => <span className="animate-spin text-lg">⏳</span>
const UtensilsIcon = () => <span className="text-xl">🍽️</span>
const StarIcon = () => <span className="text-lg">⭐</span>
const SparklesIcon = () => <span className="text-lg">✨</span>
const ChefIcon = () => <span className="text-lg">👨‍🍳</span>
const NutritionIcon = () => <span className="text-lg">🥗</span>

const FoodRecommendations = () => {
  const [foodRecommendations, setFoodRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [targetNutrients, setTargetNutrients] = useState('protein,iron')
  const [limit, setLimit] = useState(5)

  const fetchFoodRecommendations = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/foods/recommendations?target_nutrients=${targetNutrients}&limit=${limit}`)
      setFoodRecommendations(response.data.recommendations || [])
    } catch (error) {
      console.error('Error fetching food recommendations:', error)
      setFoodRecommendations([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFoodRecommendations()
  }, [])

  const quickNutrientOptions = [
    { label: 'Protein Power', value: 'protein', icon: '💪', color: 'bg-red-500' },
    { label: 'Iron Boost', value: 'iron', icon: '🔋', color: 'bg-orange-500' },
    { label: 'Calcium Strong', value: 'calcium', icon: '🦴', color: 'bg-blue-500' },
    { label: 'Fiber Rich', value: 'fiber', icon: '🌾', color: 'bg-green-500' },
    { label: 'Vitamin C', value: 'vitamin_c', icon: '🍊', color: 'bg-yellow-500' },
    { label: 'Healthy Fats', value: 'omega3', icon: '🐟', color: 'bg-purple-500' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-700 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
          <div className="text-center max-w-4xl mx-auto">
            <div className="flex justify-center mb-4">
              <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
                <span className="text-4xl sm:text-5xl">🍎</span>
              </div>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6">
              Smart Food Recommendations
            </h1>
            <p className="text-lg sm:text-xl text-purple-100 max-w-2xl mx-auto leading-relaxed">
              Get AI-powered, personalized food suggestions based on your nutritional needs and dietary preferences
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="space-y-8">
          {/* Quick Nutrient Selection */}
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-6 sm:p-8">
              <h2 className="text-xl sm:text-2xl font-bold mb-2 flex items-center gap-3">
                <SparklesIcon />
                Quick Nutrient Selection
              </h2>
              <p className="text-indigo-100">Choose what your body needs most today</p>
            </div>

            <div className="p-6 sm:p-8">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
                {quickNutrientOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTargetNutrients(option.value)}
                    className={`${option.color} text-white p-3 sm:p-4 rounded-xl hover:scale-105 transform transition-all duration-200 shadow-lg hover:shadow-xl`}
                  >
                    <div className="text-2xl sm:text-3xl mb-2">{option.icon}</div>
                    <div className="text-xs sm:text-sm font-semibold text-center leading-tight">
                      {option.label}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Custom Form */}
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-6 sm:p-8">
              <h2 className="text-xl sm:text-2xl font-bold mb-2 flex items-center gap-3">
                <UtensilsIcon />
                Customize Your Recommendations
              </h2>
              <p className="text-green-100">Fine-tune your nutrition search</p>
            </div>

            <div className="p-6 sm:p-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      <NutritionIcon /> Target Nutrients
                    </label>
                    <Input
                      type="text"
                      value={targetNutrients}
                      onChange={(e) => setTargetNutrients(e.target.value)}
                      placeholder="protein,iron,calcium,fiber"
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      Separate multiple nutrients with commas
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      📊 Number of Recommendations
                    </label>
                    <Input
                      type="number"
                      value={limit}
                      onChange={(e) => setLimit(parseInt(e.target.value))}
                      min="1"
                      max="10"
                      className="w-full"
                    />
                  </div>
                </div>

                <div className="flex items-end">
                  <Button
                    onClick={fetchFoodRecommendations}
                    disabled={loading}
                    variant="gradient"
                    className="w-full h-14 text-lg font-semibold"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center gap-3">
                        <LoadingSpinner size="sm" />
                        <span>Generating Recommendations...</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-3">
                        <StarIcon />
                        <span>Get Smart Recommendations</span>
                      </div>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Results Section */}
          {loading && (
            <Card className="text-center py-12">
              <LoadingSpinner size="lg" text="Generating personalized recommendations..." />
            </Card>
          )}

          {foodRecommendations.length > 0 && !loading && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                  <ChefIcon /> Your Personalized Recommendations
                </h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Discover these nutritious foods tailored to your specific needs
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                {foodRecommendations.map((food, index) => (
                  <Card key={index} className="group hover:scale-105 transform transition-all duration-300 hover:shadow-2xl overflow-hidden">
                    {/* Food Header */}
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 sm:p-6">
                      <h3 className="text-lg sm:text-xl font-bold mb-2 leading-tight">
                        {food.food_name}
                      </h3>
                      <div className="flex items-center gap-2 text-purple-100">
                        <span className="text-sm">🍽️</span>
                        <span className="text-sm font-medium">
                          {food.serving_size} {food.serving_unit}
                        </span>
                        <span className="text-sm">•</span>
                        <span className="text-sm font-medium">
                          {food.calories_per_serving} cal
                        </span>
                      </div>
                    </div>

                    {/* Food Content */}
                    <div className="p-4 sm:p-6 space-y-4">
                      {/* Reason */}
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <p className="text-sm text-blue-800 leading-relaxed">
                          💡 {food.reason}
                        </p>
                      </div>

                      {/* Key Nutrients */}
                      {food.key_nutrients && (
                        <div>
                          <h4 className="font-semibold text-sm mb-3 text-gray-800 flex items-center gap-2">
                            🥗 Key Nutrients
                          </h4>
                          <div className="grid grid-cols-1 gap-2">
                            {Object.entries(food.key_nutrients).map(([nutrient, value]) => (
                              <div key={nutrient} className="flex justify-between items-center bg-gray-50 px-3 py-2 rounded-lg">
                                <span className="text-xs font-medium text-gray-700 capitalize">
                                  {nutrient.replace('_', ' ')}
                                </span>
                                <span className="text-xs font-bold text-gray-900 bg-white px-2 py-1 rounded">
                                  {value}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Addresses Nutrients */}
                      {food.addresses_nutrients && (
                        <div>
                          <h4 className="font-semibold text-sm mb-3 text-gray-800 flex items-center gap-2">
                            🎯 Targets
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {food.addresses_nutrients.map((nutrient, idx) => (
                              <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                                {nutrient}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Preparation Tips */}
                      {food.preparation_suggestions && (
                        <div>
                          <h4 className="font-semibold text-sm mb-3 text-gray-800 flex items-center gap-2">
                            👨‍🍳 Prep Tips
                          </h4>
                          <ul className="space-y-2">
                            {food.preparation_suggestions.slice(0, 2).map((tip, idx) => (
                              <li key={idx} className="text-xs text-gray-600 flex items-start gap-2">
                                <span className="text-orange-500 mt-0.5">•</span>
                                <span className="leading-relaxed">{tip}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Meal Timing */}
                      {food.meal_timing && (
                        <div className="pt-2 border-t border-gray-100">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">⏰ Best for:</span>
                            <div className="flex flex-wrap gap-1">
                              {food.meal_timing.map((timing, idx) => (
                                <span key={idx} className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full capitalize">
                                  {timing}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {foodRecommendations.length === 0 && !loading && (
            <Card className="text-center py-12 sm:py-16">
              <div className="max-w-md mx-auto">
                <div className="text-6xl sm:text-7xl mb-4">🍽️</div>
                <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">
                  Ready for Smart Recommendations?
                </h3>
                <p className="text-gray-600 mb-6 leading-relaxed">
                  Select your target nutrients above and click "Get Smart Recommendations" to discover personalized food suggestions!
                </p>
                <Button
                  onClick={fetchFoodRecommendations}
                  variant="gradient"
                  className="px-8 py-3"
                >
                  <StarIcon /> Get Started
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default FoodRecommendations