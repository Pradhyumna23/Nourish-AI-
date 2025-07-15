# 🥗 NourishAI - AI-Powered Nutrition Assistant

<div align="center">

![NourishAI Logo](https://img.shields.io/badge/NourishAI-Nutrition%20Assistant-green?style=for-the-badge&logo=nutrition)

**An intelligent nutrition recommendation system that provides personalized dietary suggestions using AI and real-world food data.**

[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=flat&logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat&logo=mongodb)](https://www.mongodb.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-4285F4?style=flat&logo=google)](https://ai.google.dev/)
[![USDA](https://img.shields.io/badge/USDA-FoodData-228B22?style=flat)](https://fdc.nal.usda.gov/)

</div>

## 🌟 Features

### 🔐 **Secure Authentication**
- User registration and login system
- JWT-based authentication
- Protected routes and API endpoints
- Secure password handling

### 👤 **Personalized Health Profiles**
- Comprehensive user health metrics
- Dietary restrictions and allergies management
- Personal nutrition goals tracking
- BMI and health indicators

### 🍽️ **Smart Food Logging**
- Real-time food search using USDA database
- Detailed nutritional information
- Daily food intake tracking
- Meal categorization (breakfast, lunch, dinner, snacks)

### 🤖 **AI-Powered Recommendations**
- **Gemini AI integration** for intelligent suggestions
- Personalized nutrition recommendations
- Dietary restriction-aware suggestions
- Health condition considerations

### 📊 **Comprehensive Analytics**
- Daily nutrition summaries
- Weekly nutrition trends
- Nutrient deficiency alerts
- Progress tracking dashboards

### 💬 **AI Chatbot Assistant**
- Interactive nutrition guidance
- Real-time dietary advice
- Personalized meal suggestions
- Health-conscious recommendations

## 🛠️ Technology Stack

### **Frontend**
- **React.js 18** - Modern UI library
- **Tailwind CSS** - Utility-first styling
- **Vite** - Fast build tool
- **Zustand** - State management
- **React Router** - Client-side routing
- **Axios** - HTTP client

### **Backend**
- **FastAPI** - High-performance Python web framework
- **MongoDB Atlas** - Cloud NoSQL database
- **Pydantic** - Data validation
- **JWT** - Secure authentication
- **Uvicorn** - ASGI server

### **AI & Data Sources**
- **Google Gemini AI** - Advanced language model
- **USDA FoodData Central** - Comprehensive food database
- **Real-time nutrition analysis**
- **Intelligent recommendation engine**

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- Node.js 16+
- MongoDB Atlas account (or local MongoDB)
- Gemini API key
- USDA API key

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/nourishai.git
cd nourishai
```

### **2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and database URL

# Start backend server
python mongodb_main.py
```

### **3. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### **4. Access Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs

## ⚙️ Configuration

### **Environment Variables**

Create `.env` file in the `backend` directory:

```env
# Database Configuration
MONGODB_URL=your_mongodb_atlas_connection_string

# API Keys
GEMINI_API_KEY=your_gemini_api_key
USDA_API_KEY=your_usda_api_key

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8002
DEBUG=True

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8002
```

## 📱 Usage Guide

### **1. Getting Started**
1. **Register** a new account or **login** to existing account
2. **Complete your health profile** with personal information
3. **Set dietary restrictions** and allergies if applicable

### **2. Daily Food Tracking**
1. **Search for foods** using the USDA database
2. **Log meals** with accurate portions
3. **View nutrition breakdown** for each meal
4. **Track daily progress** against nutrition goals

### **3. AI Recommendations**
1. **Generate personalized recommendations** based on your profile
2. **Chat with NourishAI** for instant nutrition advice
3. **Get meal suggestions** tailored to your dietary needs
4. **Receive alerts** for nutrient deficiencies

### **4. Progress Monitoring**
1. **View daily summaries** of nutrition intake
2. **Analyze weekly trends** and patterns
3. **Track progress** towards health goals
4. **Export data** for healthcare providers

## 🔒 Security Features

- ✅ **Environment variable protection** for sensitive data
- ✅ **JWT-based authentication** with secure tokens
- ✅ **API rate limiting** and input validation
- ✅ **CORS protection** for cross-origin requests
- ✅ **Secure password hashing** with bcrypt
- ✅ **Protected routes** for authenticated users only

## 📊 API Documentation

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

### **Key Endpoints**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/token` - User login
- `GET /api/v1/foods/search` - Search USDA food database
- `POST /api/v1/foods/log` - Log food intake
- `GET /api/v1/nutrition/recommendations` - Get AI recommendations
- `POST /api/v1/chat/message` - Chat with AI assistant

## 🏗️ Project Structure

```
nourishai/
├── frontend/                 # React.js application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── store/          # State management (Zustand)
│   │   └── utils/          # Utility functions
│   └── package.json
├── backend/                 # FastAPI application
│   ├── mongodb_main.py     # Main application entry
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── real_*.py          # Service implementations
│   └── requirements.txt
├── SECURITY.md             # Security documentation
├── .env.example           # Environment template
└── README.md              # This file
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Development Guidelines**
- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript/React
- Write comprehensive tests
- Update documentation for new features
- Ensure security best practices

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check our comprehensive docs
- **Issues**: Create an issue on GitHub
- **Email**: support@nourishai.com
- **Community**: Join our Discord server

## 🙏 Acknowledgments

- **USDA FoodData Central** for comprehensive nutrition data
- **Google Gemini AI** for intelligent recommendations
- **MongoDB Atlas** for reliable cloud database
- **FastAPI** and **React** communities for excellent frameworks

---

<div align="center">

**Made with ❤️ for better nutrition and health**

[⭐ Star this repo](https://github.com/yourusername/nourishai) | [🐛 Report Bug](https://github.com/yourusername/nourishai/issues) | [💡 Request Feature](https://github.com/yourusername/nourishai/issues)

</div>
