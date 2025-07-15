// MongoDB initialization script
db = db.getSiblingDB('nutrient_db');

// Create collections
db.createCollection('users');
db.createCollection('foods');
db.createCollection('food_items');
db.createCollection('nutrition_profiles');
db.createCollection('daily_intakes');
db.createCollection('recommendations');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });

db.foods.createIndex({ "fdc_id": 1 }, { unique: true });
db.foods.createIndex({ "description": "text" });

db.food_items.createIndex({ "user_id": 1, "date": 1 });

db.nutrition_profiles.createIndex({ "user_id": 1 }, { unique: true });

db.daily_intakes.createIndex({ "user_id": 1, "date": 1 });

db.recommendations.createIndex({ "user_id": 1, "created_at": 1 });

print('Database initialized successfully!');
