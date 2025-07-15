import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authAPI, handleApiError } from '../services/api'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Card from '../components/ui/Card'

const RegisterPage = () => {
  const navigate = useNavigate()
  const { login, setLoading } = useAuthStore()
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    activity_level: '',
    primary_goal: '',
  })
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required'
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters'
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid'
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }
    
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required'
    }
    
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required'
    }
    
    if (formData.age && (formData.age < 13 || formData.age > 120)) {
      newErrors.age = 'Age must be between 13 and 120'
    }
    
    if (formData.height_cm && (formData.height_cm < 100 || formData.height_cm > 250)) {
      newErrors.height_cm = 'Height must be between 100 and 250 cm'
    }
    
    if (formData.weight_kg && (formData.weight_kg < 20 || formData.weight_kg > 500)) {
      newErrors.weight_kg = 'Weight must be between 20 and 500 kg'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) return
    
    setIsLoading(true)
    setLoading(true)
    
    try {
      // Prepare registration data
      const registrationData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
      }
      
      // Add optional fields if provided
      if (formData.age) registrationData.age = parseInt(formData.age)
      if (formData.gender) registrationData.gender = formData.gender
      if (formData.height_cm) registrationData.height_cm = parseFloat(formData.height_cm)
      if (formData.weight_kg) registrationData.weight_kg = parseFloat(formData.weight_kg)
      if (formData.activity_level) registrationData.activity_level = formData.activity_level
      if (formData.primary_goal) registrationData.primary_goal = formData.primary_goal
      
      const response = await authAPI.register(registrationData)
      const user = response.data
      
      // Auto-login after registration
      const loginData = new FormData()
      loginData.append('username', formData.username)
      loginData.append('password', formData.password)
      
      const loginResponse = await authAPI.login(loginData)
      const { access_token } = loginResponse.data
      
      // Store auth data
      login(user, access_token)
      
      // Redirect to dashboard
      navigate('/dashboard')
    } catch (error) {
      const errorInfo = handleApiError(error)
      
      if (errorInfo.status === 400) {
        setErrors({ general: 'User with this email or username already exists' })
      } else {
        setErrors({ general: errorInfo.message })
      }
    } finally {
      setIsLoading(false)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <Link
            to="/login"
            className="font-medium text-primary-600 hover:text-primary-500"
          >
            sign in to your existing account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            {errors.general && (
              <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded">
                {errors.general}
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="First Name"
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                error={errors.first_name}
                required
              />
              
              <Input
                label="Last Name"
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                error={errors.last_name}
                required
              />
            </div>
            
            <Input
              label="Username"
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              error={errors.username}
              required
              helperText="At least 3 characters"
            />
            
            <Input
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              required
            />
            
            <Input
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              required
              helperText="At least 8 characters"
            />
            
            <Input
              label="Confirm Password"
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              error={errors.confirmPassword}
              required
            />
            
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Optional Profile Information
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Age"
                  name="age"
                  type="number"
                  value={formData.age}
                  onChange={handleChange}
                  error={errors.age}
                  min="13"
                  max="120"
                />
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-4">
                <Input
                  label="Height (cm)"
                  name="height_cm"
                  type="number"
                  value={formData.height_cm}
                  onChange={handleChange}
                  error={errors.height_cm}
                  min="100"
                  max="250"
                />
                
                <Input
                  label="Weight (kg)"
                  name="weight_kg"
                  type="number"
                  value={formData.weight_kg}
                  onChange={handleChange}
                  error={errors.weight_kg}
                  min="20"
                  max="500"
                />
              </div>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Activity Level
                </label>
                <select
                  name="activity_level"
                  value={formData.activity_level}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Select activity level</option>
                  <option value="sedentary">Sedentary (little/no exercise)</option>
                  <option value="lightly_active">Lightly Active (light exercise 1-3 days/week)</option>
                  <option value="moderately_active">Moderately Active (moderate exercise 3-5 days/week)</option>
                  <option value="very_active">Very Active (hard exercise 6-7 days/week)</option>
                  <option value="extremely_active">Extremely Active (very hard exercise, physical job)</option>
                </select>
              </div>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Primary Goal
                </label>
                <select
                  name="primary_goal"
                  value={formData.primary_goal}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Select primary goal</option>
                  <option value="weight_loss">Weight Loss</option>
                  <option value="weight_gain">Weight Gain</option>
                  <option value="muscle_gain">Muscle Gain</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="health_improvement">Health Improvement</option>
                </select>
              </div>
            </div>
            
            <Button
              type="submit"
              className="w-full"
              loading={isLoading}
              disabled={isLoading}
            >
              Create Account
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}

export default RegisterPage
