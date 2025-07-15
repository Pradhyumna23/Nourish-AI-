# Nutrient Recommendation System - Backend

FastAPI-based backend for the AI-powered nutrient recommendation system.

## Features

- **User Management**: Registration, authentication, profile management
- **Food Database**: USDA FoodData Central integration with 200,000+ foods
- **Nutrition Tracking**: Daily intake logging and progress monitoring
- **AI Recommendations**: ML-powered personalized nutrition suggestions
- **Health Optimization**: Condition-specific dietary recommendations
- **Security**: JWT authentication, rate limiting, input validation

## Architecture

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Configuration, database, middleware
│   ├── models/               # Database models (Beanie ODM)
│   ├── services/             # Business logic services
│   ├── ml/                   # ML integration services
│   └── utils/                # Utility functions
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
└── Dockerfile               # Container configuration
```

## Setup

### Prerequisites
- Python 3.9+
- MongoDB 7.0+
- USDA FoodData Central API Key
- OpenAI API Key (optional)

### Installation

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Environment configuration**:
```bash
cp ../.env.example .env
# Edit .env with your configuration
```

4. **Start the server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/token` - Login (get JWT token)
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### User Management
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update profile
- `POST /api/v1/users/health-conditions` - Add health condition
- `DELETE /api/v1/users/health-conditions/{name}` - Remove condition
- `POST /api/v1/users/dietary-restrictions` - Add restriction
- `POST /api/v1/users/allergies` - Add allergy

### Food & Nutrition
- `GET /api/v1/foods/search?query={food}` - Search foods
- `GET /api/v1/foods/{fdc_id}` - Get food details
- `POST /api/v1/foods/log` - Log food consumption
- `GET /api/v1/foods/log/daily?date={date}` - Daily nutrition
- `GET /api/v1/foods/log/history?days={n}` - Food history

### Nutrition Profiles
- `GET /api/v1/nutrition/profile` - Get nutrition targets
- `POST /api/v1/nutrition/profile` - Create profile
- `PUT /api/v1/nutrition/profile` - Update targets
- `GET /api/v1/nutrition/intake/daily` - Daily intake tracking
- `GET /api/v1/nutrition/progress?days={n}` - Progress over time

### AI Recommendations
- `POST /api/v1/recommendations/generate` - Generate recommendations
- `GET /api/v1/recommendations/` - Get user recommendations
- `GET /api/v1/recommendations/{id}` - Get recommendation details
- `POST /api/v1/recommendations/{id}/feedback` - Submit feedback
- `GET /api/v1/recommendations/stats/summary` - Get statistics

## Services

### Authentication Service (`app/services/auth.py`)
- JWT token management
- Password hashing with bcrypt
- User authentication and authorization

### User Service (`app/services/user.py`)
- User CRUD operations
- Health profile management
- Dietary restrictions and allergies

### Food Service (`app/services/food.py`)
- USDA API integration
- Food search and details
- Nutrition calculation
- Food logging and history

### USDA API Service (`app/services/usda_api.py`)
- FoodData Central API client
- Food data parsing and storage
- Batch food retrieval

### OpenAI Service (`app/services/openai_service.py`)
- Natural language food parsing
- Meal plan generation
- Nutrition gap analysis
- Shopping list creation

### Recommendation Engine (`app/services/recommendation_engine.py`)
- ML-enhanced recommendations
- Health condition-specific advice
- Nutrient gap analysis
- Food suggestions and meal plans

### Nutrition Calculator (`app/ml/nutrition_calculator.py`)
- BMR/TDEE calculations
- Macro/micronutrient targets
- ML model integration
- Goal-based adjustments

## Database Models

### User Model
- Personal information and demographics
- Health conditions and dietary restrictions
- Goals and preferences
- Authentication data

### Food Model
- USDA food database entries
- Nutritional information
- Serving sizes and portions

### Nutrition Profile
- Personalized nutrition targets
- Macro and micronutrient goals
- Meal distribution preferences

### Daily Intake
- Daily nutrition tracking
- Meal-by-meal breakdown
- Progress toward targets

### Recommendations
- AI-generated suggestions
- User feedback and ratings
- Implementation tracking

## Machine Learning Integration

### Feature Engineering
- User demographics and health data
- Nutrition history and patterns
- Food preferences and restrictions

### Models
- **Calorie Recommendation**: XGBoost for personalized calorie targets
- **Macro Distribution**: Random Forest for optimal macro ratios
- **Traditional Fallbacks**: BMR/TDEE with goal adjustments

### Recommendation Types
- **Nutrient Adjustments**: Gap analysis and corrections
- **Food Suggestions**: Personalized food recommendations
- **Meal Plans**: Complete daily meal planning
- **Health Optimization**: Condition-specific advice

## Security Features

### Authentication
- JWT tokens with expiration
- Secure password hashing
- Token refresh mechanism

### Middleware
- Request logging and monitoring
- Rate limiting (100 requests/minute)
- Input validation and sanitization
- Security headers (HSTS, CSP, etc.)
- CORS configuration

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Request size limits

## Configuration

### Environment Variables
```env
# Database
MONGODB_URL=mongodb://localhost:27017/nutrient_db

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
OPENAI_API_KEY=your-openai-key
USDA_API_KEY=your-usda-key

# Application
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Logging
- Structured logging with Loguru
- Request/response logging
- Error tracking and monitoring
- Performance metrics

## Testing

Run tests with:
```bash
pytest tests/ -v
```

## Deployment

### Docker
```bash
docker build -t nutrient-backend .
docker run -p 8000:8000 nutrient-backend
```

### Production Considerations
- Use environment-specific configurations
- Set up proper logging and monitoring
- Configure reverse proxy (nginx)
- Enable SSL/TLS
- Set up database backups
- Monitor API rate limits and performance

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Write comprehensive tests

### Adding New Endpoints
1. Create route handler in `app/api/v1/endpoints/`
2. Add business logic to appropriate service
3. Update database models if needed
4. Add input validation
5. Write tests
6. Update API documentation

### Database Migrations
- Use Beanie ODM for schema management
- Test migrations in development
- Backup data before production changes
