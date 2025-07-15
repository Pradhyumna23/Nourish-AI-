"""
Food management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, date

from app.models.user import User
from app.models.food import (
    Food, FoodItem, FoodSearch, FoodResponse,
    FoodItemCreate, FoodItemResponse, NutritionSummary
)
from app.services.auth import AuthService
from app.services.food import FoodService

router = APIRouter()


@router.get("/search")
async def search_foods(
    query: str,
    page_size: Optional[int] = 20,
    page_number: Optional[int] = 1,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Search for foods in the database."""
    food_service = FoodService()

    search_params = FoodSearch(
        query=query,
        page_size=page_size,
        page_number=page_number
    )

    results = await food_service.search_foods(search_params, current_user)
    return results


@router.get("/{fdc_id}")
async def get_food_details(
    fdc_id: int,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get detailed food information by FDC ID."""
    food_service = FoodService()

    food = await food_service.get_food_by_fdc_id(fdc_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food with FDC ID {fdc_id} not found"
        )

    return {
        "fdc_id": food.fdc_id,
        "description": food.description,
        "data_type": food.data_type,
        "brand_owner": food.brand_owner,
        "brand_name": food.brand_name,
        "food_category": food.food_category,
        "nutrients": food.nutrients,
        "food_portions": food.food_portions
    }


@router.post("/log")
async def log_food_item(
    food_item: FoodItemCreate,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Log a food item for the current user."""
    food_service = FoodService()

    logged_item = await food_service.log_food_item(
        user_id=str(current_user.id),
        fdc_id=food_item.fdc_id,
        date=food_item.date,
        meal_type=food_item.meal_type,
        quantity=food_item.quantity,
        unit=food_item.unit,
        notes=food_item.notes
    )

    # Get food details for response
    food = await food_service.get_food_by_fdc_id(food_item.fdc_id)

    return {
        "id": str(logged_item.id),
        "user_id": logged_item.user_id,
        "fdc_id": logged_item.fdc_id,
        "food_description": food.description if food else "Unknown",
        "date": logged_item.date,
        "meal_type": logged_item.meal_type,
        "quantity": logged_item.quantity,
        "unit": logged_item.unit,
        "gram_weight": logged_item.gram_weight,
        "calories": logged_item.calories,
        "protein_g": logged_item.protein_g,
        "carbs_g": logged_item.carbs_g,
        "fat_g": logged_item.fat_g,
        "fiber_g": logged_item.fiber_g,
        "notes": logged_item.notes,
        "created_at": logged_item.created_at
    }


@router.get("/log/daily")
async def get_daily_nutrition(
    target_date: Optional[date] = None,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get daily nutrition summary for a specific date."""
    food_service = FoodService()

    if target_date is None:
        target_date = date.today()

    summary = await food_service.get_daily_nutrition_summary(
        user_id=str(current_user.id),
        target_date=target_date
    )

    return summary


@router.get("/log/history")
async def get_food_log_history(
    days: Optional[int] = 7,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get food log history for the current user."""
    food_service = FoodService()

    food_items = await food_service.get_food_log_history(
        user_id=str(current_user.id),
        days=days
    )

    # Convert to response format
    response_items = []
    for item in food_items:
        food = await food_service.get_food_by_fdc_id(item.fdc_id)
        response_items.append({
            "id": str(item.id),
            "user_id": item.user_id,
            "fdc_id": item.fdc_id,
            "food_description": food.description if food else "Unknown",
            "date": item.date,
            "meal_type": item.meal_type,
            "quantity": item.quantity,
            "unit": item.unit,
            "gram_weight": item.gram_weight,
            "calories": item.calories,
            "protein_g": item.protein_g,
            "carbs_g": item.carbs_g,
            "fat_g": item.fat_g,
            "fiber_g": item.fiber_g,
            "notes": item.notes,
            "created_at": item.created_at
        })

    return response_items
