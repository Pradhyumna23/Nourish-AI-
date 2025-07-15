import React from 'react'

const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              NourishAI
            </h3>
            <p className="text-gray-600 text-sm">
              AI-powered personalized nutrition recommendations to help you achieve your health goals.
              Get customized meal plans, track your nutrition, and optimize your diet with intelligent insights.
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Features</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>Personalized Recommendations</li>
              <li>Food Tracking</li>
              <li>Nutrition Analysis</li>
              <li>Meal Planning</li>
              <li>Progress Tracking</li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Support</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>Help Center</li>
              <li>Contact Us</li>
              <li>Privacy Policy</li>
              <li>Terms of Service</li>
            </ul>
          </div>
        </div>
        
        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-center text-sm text-gray-500">
            © 2024 NourishAI. All rights reserved. Powered by AI and nutritional science.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
