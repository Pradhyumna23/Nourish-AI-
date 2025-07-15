import React, { useState, useEffect } from 'react'
import { useFoodStore } from '../store/foodStore'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import MealNutritionSummary from '../components/MealNutritionSummary'

const FoodLog = () => {
  const {
    searchResults,
    isSearching,
    selectedFood,
    isLogging,
    dailyNutrition,
    isDailyLoading,
    foodHistory,
    searchFoods,
    getFoodDetails,
    logFood,
    getDailyNutrition,
    getFoodHistory,
    clearSearch,
    clearSelectedFood
  } = useFoodStore()

  const [showAddModal, setShowAddModal] = useState(false)
  const [searchInput, setSearchInput] = useState('')
  const [logData, setLogData] = useState({
    quantity: 1,
    unit: 'serving',
    meal_type: 'lunch',
    notes: ''
  })
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [activeTab, setActiveTab] = useState('log')

  useEffect(() => {
    getDailyNutrition(selectedDate)
    getFoodHistory(7)
  }, [getDailyNutrition, getFoodHistory, selectedDate])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (searchInput.trim()) {
      await searchFoods(searchInput.trim())
    }
  }

  const handleSelectFood = async (food) => {
    await getFoodDetails(food.fdc_id)
    setShowAddModal(true)
  }

  const handleLogFood = async (e) => {
    e.preventDefault()
    if (!selectedFood) return

    try {
      await logFood({
        fdc_id: selectedFood.fdc_id,
        date: new Date(selectedDate).toISOString(),
        meal_type: logData.meal_type,
        quantity: parseFloat(logData.quantity),
        unit: logData.unit,
        notes: logData.notes
      })

      setLogData({
        quantity: 1,
        unit: 'serving',
        meal_type: 'lunch',
        notes: ''
      })
      setShowAddModal(false)
      clearSelectedFood()
      clearSearch()
      setSearchInput('')
      getDailyNutrition(selectedDate)
      getFoodHistory(7)
    } catch (error) {
      console.error('Failed to log food:', error)
    }
  }

  const formatNutrition = (value, unit) => {
    if (!value) return '0'
    return `${Math.round(value)}${unit}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-12 animate-fadeInUp">
          <div className="mb-6 lg:mb-0">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-2">
              Food Log 📝
            </h1>
            <p className="text-lg text-gray-600">Track your daily nutrition journey</p>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
            <div className="relative">
              <Input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="input-enhanced pl-12 w-full sm:w-auto"
              />
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400">
                📅
              </div>
            </div>
            <Button 
              onClick={() => setShowAddModal(true)}
              variant="gradient"
              className="w-full sm:w-auto"
            >
              <span className="flex items-center space-x-2">
                <span>➕</span>
                <span>Add Food</span>
              </span>
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-12 animate-slideInRight">
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-2 border border-white/20 shadow-lg max-w-lg mx-auto">
            <nav className="flex space-x-2">
              <button
                onClick={() => setActiveTab('log')}
                className={`flex-1 py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-300 ${
                  activeTab === 'log'
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>📝</span>
                  <span>Food Log</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('nutrition-summary')}
                className={`flex-1 py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-300 ${
                  activeTab === 'nutrition-summary'
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>📊</span>
                  <span>Nutrition Summary</span>
                </span>
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'log' && (
          <div className="space-y-6">
            {/* Quick Summary */}
            <Card>
              <Card.Header>
                <Card.Title>Today's Summary</Card.Title>
              </Card.Header>
              <Card.Content>
                {isDailyLoading ? (
                  <LoadingSpinner center text="Loading..." />
                ) : (
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">
                        {formatNutrition(dailyNutrition?.total_calories, '')}
                      </div>
                      <div className="text-sm text-gray-600">Calories</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">
                        {formatNutrition(dailyNutrition?.total_protein_g, 'g')}
                      </div>
                      <div className="text-sm text-gray-600">Protein</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-orange-600">
                        {formatNutrition(dailyNutrition?.total_carbs_g, 'g')}
                      </div>
                      <div className="text-sm text-gray-600">Carbs</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-purple-600">
                        {formatNutrition(dailyNutrition?.total_fat_g, 'g')}
                      </div>
                      <div className="text-sm text-gray-600">Fat</div>
                    </div>
                  </div>
                )}
              </Card.Content>
            </Card>

            {/* Recent Foods */}
            <Card>
              <Card.Header>
                <Card.Title>Recent Foods</Card.Title>
              </Card.Header>
              <Card.Content>
                {foodHistory && foodHistory.length > 0 ? (
                  <div className="space-y-2">
                    {foodHistory.slice(0, 5).map((food, index) => (
                      <div key={index} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                        <div>
                          <div className="font-medium">{food.food_description}</div>
                          <div className="text-sm text-gray-500">
                            {food.quantity} {food.unit} • {food.meal_type}
                          </div>
                        </div>
                        <div className="text-sm text-gray-600">
                          {formatNutrition(food.calories, ' cal')}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No recent foods</p>
                )}
              </Card.Content>
            </Card>
          </div>
        )}

        {/* Nutrition Summary Tab */}
        {activeTab === 'nutrition-summary' && (
          <MealNutritionSummary date={selectedDate} />
        )}

        {/* Add Food Modal */}
        <Modal isOpen={showAddModal} onClose={() => {
          setShowAddModal(false)
          clearSelectedFood()
          clearSearch()
          setSearchInput('')
        }}>
          <Modal.Header>
            <Modal.Title>Add Food to Log</Modal.Title>
          </Modal.Header>
          <Modal.Content>
            <div className="space-y-4">
              {/* Search Section */}
              <div>
                <form onSubmit={handleSearch} className="flex space-x-2">
                  <Input
                    type="text"
                    placeholder="Search for foods..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={isSearching}>
                    {isSearching ? 'Searching...' : 'Search'}
                  </Button>
                </form>
              </div>

              {/* Search Results */}
              {searchResults && searchResults.length > 0 && (
                <div className="max-h-40 overflow-y-auto border rounded">
                  {searchResults.map((food) => (
                    <div
                      key={food.fdc_id}
                      className="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                      onClick={() => handleSelectFood(food)}
                    >
                      <div className="font-medium">{food.description}</div>
                      <div className="text-sm text-gray-500">FDC ID: {food.fdc_id}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Selected Food Form */}
              {selectedFood && (
                <form onSubmit={handleLogFood} className="space-y-4">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Selected Food:</h3>
                    <p className="text-sm text-gray-600">{selectedFood.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Quantity
                      </label>
                      <Input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={logData.quantity}
                        onChange={(e) => setLogData({ ...logData, quantity: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Unit
                      </label>
                      <select
                        value={logData.unit}
                        onChange={(e) => setLogData({ ...logData, unit: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="serving">Serving</option>
                        <option value="gram">Gram</option>
                        <option value="cup">Cup</option>
                        <option value="piece">Piece</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Meal Type
                    </label>
                    <select
                      value={logData.meal_type}
                      onChange={(e) => setLogData({ ...logData, meal_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="breakfast">Breakfast</option>
                      <option value="lunch">Lunch</option>
                      <option value="dinner">Dinner</option>
                      <option value="snack">Snack</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes (Optional)
                    </label>
                    <Input
                      type="text"
                      placeholder="Add any notes..."
                      value={logData.notes}
                      onChange={(e) => setLogData({ ...logData, notes: e.target.value })}
                    />
                  </div>
                </form>
              )}
            </div>
          </Modal.Content>
          {selectedFood && (
            <Modal.Footer>
              <Button
                type="submit"
                onClick={handleLogFood}
                disabled={isLogging}
              >
                Log Food
              </Button>
            </Modal.Footer>
          )}
        </Modal>
      </div>
    </div>
  )
}

export default FoodLog
