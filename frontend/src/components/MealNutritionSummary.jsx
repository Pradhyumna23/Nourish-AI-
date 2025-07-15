import React, { useState, useEffect } from 'react'
import { foodAPI } from '../services/api'
import Card from './ui/Card'
import LoadingSpinner from './ui/LoadingSpinner'

const MealNutritionSummary = ({ date = new Date().toISOString().split('T')[0] }) => {
  const [mealData, setMealData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedMeal, setSelectedMeal] = useState('all')

  useEffect(() => {
    fetchMealData()
  }, [date])

  const fetchMealData = async () => {
    try {
      setLoading(true)
      const response = await foodAPI.getDailyNutrition(date)
      setMealData(response.data)
    } catch (error) {
      console.error('Failed to fetch meal data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMealIcon = (mealType) => {
    switch (mealType) {
      case 'breakfast': return '🌅'
      case 'lunch': return '☀️'
      case 'dinner': return '🌙'
      case 'snack': return '🍎'
      default: return '🍽️'
    }
  }

  const getMealTime = (mealType) => {
    switch (mealType) {
      case 'breakfast': return '6:00 AM - 10:00 AM'
      case 'lunch': return '12:00 PM - 2:00 PM'
      case 'dinner': return '6:00 PM - 9:00 PM'
      case 'snack': return 'Anytime'
      default: return ''
    }
  }

  const calculateMealNutrition = (foods) => {
    return foods.reduce((total, food) => ({
      calories: total.calories + (food.calories || 0),
      protein_g: total.protein_g + (food.protein_g || 0),
      carbs_g: total.carbs_g + (food.carbs_g || 0),
      fat_g: total.fat_g + (food.fat_g || 0)
    }), { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 })
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  if (loading) {
    return (
      <Card className="p-6">
        <LoadingSpinner />
        <p className="text-center mt-4">Loading meal nutrition summary...</p>
      </Card>
    )
  }

  if (!mealData) {
    return (
      <Card className="p-6">
        <p className="text-center text-gray-500">No meal data available for {formatDate(date)}</p>
      </Card>
    )
  }

  const meals = mealData.meals || {}
  const totalCalories = mealData.total_calories || 0
  const totalProtein = mealData.total_protein_g || 0
  const totalCarbs = mealData.total_carbs_g || 0
  const totalFat = mealData.total_fat_g || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Nutrition Summary</h2>
        <p className="text-gray-600 mt-1">{formatDate(date)}</p>
      </div>

      {/* Daily Totals */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Daily Totals</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalCalories.toFixed(0)}</div>
            <div className="text-sm text-gray-600">Calories</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{totalProtein.toFixed(1)}g</div>
            <div className="text-sm text-gray-600">Protein</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{totalCarbs.toFixed(1)}g</div>
            <div className="text-sm text-gray-600">Carbs</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{totalFat.toFixed(1)}g</div>
            <div className="text-sm text-gray-600">Fat</div>
          </div>
        </div>
      </Card>

      {/* Meal Filter */}
      <div className="flex flex-wrap gap-2 justify-center">
        <button
          onClick={() => setSelectedMeal('all')}
          className={`px-4 py-2 rounded-full text-sm font-medium ${
            selectedMeal === 'all'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All Meals
        </button>
        {Object.keys(meals).map(mealType => (
          <button
            key={mealType}
            onClick={() => setSelectedMeal(mealType)}
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              selectedMeal === mealType
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {getMealIcon(mealType)} {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
          </button>
        ))}
      </div>

      {/* Meal Details */}
      <div className="space-y-4">
        {Object.entries(meals)
          .filter(([mealType]) => selectedMeal === 'all' || selectedMeal === mealType)
          .map(([mealType, foods]) => {
            const mealNutrition = calculateMealNutrition(foods)
            const mealPercentage = totalCalories > 0 ? (mealNutrition.calories / totalCalories * 100) : 0

            return (
              <Card key={mealType} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getMealIcon(mealType)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 capitalize">
                        {mealType}
                      </h3>
                      <p className="text-sm text-gray-500">{getMealTime(mealType)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">
                      {mealNutrition.calories.toFixed(0)} cal
                    </div>
                    <div className="text-sm text-gray-500">
                      {mealPercentage.toFixed(0)}% of daily total
                    </div>
                  </div>
                </div>

                {/* Meal Nutrition Breakdown */}
                <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="font-semibold text-green-600">{mealNutrition.protein_g.toFixed(1)}g</div>
                    <div className="text-xs text-gray-600">Protein</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-orange-600">{mealNutrition.carbs_g.toFixed(1)}g</div>
                    <div className="text-xs text-gray-600">Carbs</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-purple-600">{mealNutrition.fat_g.toFixed(1)}g</div>
                    <div className="text-xs text-gray-600">Fat</div>
                  </div>
                </div>

                {/* Food Items */}
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-700">Food Items ({foods.length})</h4>
                  {foods.map((food, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-white border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{food.food_description}</div>
                        <div className="text-sm text-gray-500">
                          {food.quantity} {food.unit}
                          {food.notes && ` • ${food.notes}`}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-900">{food.calories?.toFixed(0)} cal</div>
                        <div className="text-xs text-gray-500">
                          P: {food.protein_g?.toFixed(1)}g • C: {food.carbs_g?.toFixed(1)}g • F: {food.fat_g?.toFixed(1)}g
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Meal Insights */}
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <h5 className="font-medium text-blue-900 mb-1">💡 Meal Insights</h5>
                  <div className="text-sm text-blue-800">
                    {mealNutrition.protein_g < 15 && mealType !== 'snack' && (
                      <p>• Consider adding more protein to this meal for better satiety</p>
                    )}
                    {mealNutrition.calories > 600 && mealType === 'snack' && (
                      <p>• This snack is quite calorie-dense, consider lighter options</p>
                    )}
                    {mealNutrition.carbs_g > mealNutrition.protein_g * 4 && (
                      <p>• High carb-to-protein ratio, consider balancing with more protein</p>
                    )}
                    {mealNutrition.fat_g < 5 && mealType !== 'snack' && (
                      <p>• Adding healthy fats could improve nutrient absorption</p>
                    )}
                  </div>
                </div>
              </Card>
            )
          })}
      </div>

      {/* Summary Stats */}
      <Card className="p-6 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Daily Summary</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-xl font-bold text-gray-900">{Object.keys(meals).length}</div>
            <div className="text-sm text-gray-600">Meals Logged</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-gray-900">{mealData.food_count || 0}</div>
            <div className="text-sm text-gray-600">Food Items</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-gray-900">
              {totalCalories > 0 ? (totalProtein * 4 / totalCalories * 100).toFixed(0) : 0}%
            </div>
            <div className="text-sm text-gray-600">Calories from Protein</div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default MealNutritionSummary
