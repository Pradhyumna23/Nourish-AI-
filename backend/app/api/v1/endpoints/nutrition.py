"""
Nutrition profile and tracking endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.models.user import User
from app.models.nutrition import (
    NutritionProfile, NutritionProfileCreate, NutritionProfileUpdate,
    NutritionProfileResponse, DailyIntakeResponse, NutritionProgress,
    DailyIntake, MicronutrientTargets
)
from app.services.auth import AuthService
from app.ml.nutrition_calculator import NutritionCalculatorService
from app.services.food import FoodService

router = APIRouter()


@router.get("/profile")
async def get_nutrition_profile(
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get current user's nutrition profile."""
    try:
        # Check if user has existing nutrition profile
        profile = await NutritionProfile.find_one({"user_id": str(current_user.id)})

        if not profile:
            # Create new profile using nutrition calculator
            nutrition_calculator = NutritionCalculatorService()
            recommendations = nutrition_calculator.get_nutrition_recommendations(current_user)

            profile = NutritionProfile(
                user_id=str(current_user.id),
                macro_targets=recommendations['macro_targets'],
                micronutrient_targets=recommendations['micronutrient_targets'],
                bmr=recommendations['bmr'],
                tdee=recommendations['tdee'],
                calculation_method=recommendations['calculation_method']
            )
            await profile.insert()

        return NutritionProfileResponse(
            id=str(profile.id),
            user_id=profile.user_id,
            macro_targets=profile.macro_targets,
            micronutrient_targets=profile.micronutrient_targets,
            custom_adjustments=profile.custom_adjustments,
            meal_distribution=profile.meal_distribution,
            bmr=profile.bmr,
            tdee=profile.tdee,
            calculation_method=profile.calculation_method,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get nutrition profile: {str(e)}"
        )


@router.post("/profile")
async def create_nutrition_profile(
    profile_data: NutritionProfileCreate,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Create nutrition profile for current user."""
    try:
        # Check if profile already exists
        existing_profile = await NutritionProfile.find_one({"user_id": str(current_user.id)})
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nutrition profile already exists. Use PUT to update."
            )

        # Create new profile
        profile = NutritionProfile(
            user_id=str(current_user.id),
            macro_targets=profile_data.macro_targets,
            micronutrient_targets=profile_data.micronutrient_targets or MicronutrientTargets(),
            custom_adjustments=profile_data.custom_adjustments or {},
            meal_distribution=profile_data.meal_distribution or {
                "breakfast": 0.25,
                "lunch": 0.35,
                "dinner": 0.30,
                "snack": 0.10
            }
        )
        await profile.insert()

        return NutritionProfileResponse(
            id=str(profile.id),
            user_id=profile.user_id,
            macro_targets=profile.macro_targets,
            micronutrient_targets=profile.micronutrient_targets,
            custom_adjustments=profile.custom_adjustments,
            meal_distribution=profile.meal_distribution,
            bmr=profile.bmr,
            tdee=profile.tdee,
            calculation_method=profile.calculation_method,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create nutrition profile: {str(e)}"
        )


@router.put("/profile")
async def update_nutrition_profile(
    profile_data: NutritionProfileUpdate,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Update nutrition profile for current user."""
    try:
        profile = await NutritionProfile.find_one({"user_id": str(current_user.id)})
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition profile not found"
            )

        # Update fields that are provided
        update_data = profile_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(profile, field, value)

        profile.updated_at = datetime.utcnow()
        await profile.save()

        return NutritionProfileResponse(
            id=str(profile.id),
            user_id=profile.user_id,
            macro_targets=profile.macro_targets,
            micronutrient_targets=profile.micronutrient_targets,
            custom_adjustments=profile.custom_adjustments,
            meal_distribution=profile.meal_distribution,
            bmr=profile.bmr,
            tdee=profile.tdee,
            calculation_method=profile.calculation_method,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update nutrition profile: {str(e)}"
        )


@router.get("/intake/daily")
async def get_daily_intake(
    target_date: Optional[date] = None,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get daily intake for a specific date."""
    try:
        if target_date is None:
            target_date = date.today()

        # Get or create daily intake record
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        daily_intake = await DailyIntake.find_one({
            "user_id": str(current_user.id),
            "date": {"$gte": start_datetime, "$lte": end_datetime}
        })

        if not daily_intake:
            # Create new daily intake record
            daily_intake = DailyIntake(
                user_id=str(current_user.id),
                date=start_datetime
            )
            await daily_intake.insert()

        # Get nutrition profile for targets
        profile = await NutritionProfile.find_one({"user_id": str(current_user.id)})
        if profile:
            daily_intake.target_calories = profile.macro_targets.calories
            daily_intake.target_protein_g = profile.macro_targets.protein_g
            daily_intake.target_carbs_g = profile.macro_targets.carbs_g
            daily_intake.target_fat_g = profile.macro_targets.fat_g

            # Calculate remaining
            daily_intake.calories_remaining = max(0, daily_intake.target_calories - daily_intake.actual_calories)
            daily_intake.protein_remaining_g = max(0, daily_intake.target_protein_g - daily_intake.actual_protein_g)
            daily_intake.carbs_remaining_g = max(0, daily_intake.target_carbs_g - daily_intake.actual_carbs_g)
            daily_intake.fat_remaining_g = max(0, daily_intake.target_fat_g - daily_intake.actual_fat_g)

        return DailyIntakeResponse(
            id=str(daily_intake.id),
            user_id=daily_intake.user_id,
            date=daily_intake.date,
            actual_calories=daily_intake.actual_calories,
            actual_protein_g=daily_intake.actual_protein_g,
            actual_carbs_g=daily_intake.actual_carbs_g,
            actual_fat_g=daily_intake.actual_fat_g,
            actual_fiber_g=daily_intake.actual_fiber_g,
            target_calories=daily_intake.target_calories,
            target_protein_g=daily_intake.target_protein_g,
            target_carbs_g=daily_intake.target_carbs_g,
            target_fat_g=daily_intake.target_fat_g,
            calories_remaining=daily_intake.calories_remaining,
            protein_remaining_g=daily_intake.protein_remaining_g,
            carbs_remaining_g=daily_intake.carbs_remaining_g,
            fat_remaining_g=daily_intake.fat_remaining_g,
            meals=daily_intake.meals
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily intake: {str(e)}"
        )


@router.get("/progress")
async def get_nutrition_progress(
    days: Optional[int] = 30,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get nutrition progress over time."""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get daily intake records for the period
        daily_intakes = await DailyIntake.find({
            "user_id": str(current_user.id),
            "date": {
                "$gte": datetime.combine(start_date, datetime.min.time()),
                "$lte": datetime.combine(end_date, datetime.max.time())
            }
        }).sort([("date", 1)]).to_list()

        if not daily_intakes:
            return NutritionProgress(
                date_range=[datetime.combine(start_date, datetime.min.time()),
                           datetime.combine(end_date, datetime.min.time())],
                daily_intakes=[],
                average_calories=0,
                average_protein_g=0,
                average_carbs_g=0,
                average_fat_g=0,
                target_adherence_percent=0,
                trends={}
            )

        # Convert to response format
        daily_intake_responses = []
        for intake in daily_intakes:
            response = DailyIntakeResponse(
                id=str(intake.id),
                user_id=intake.user_id,
                date=intake.date,
                actual_calories=intake.actual_calories,
                actual_protein_g=intake.actual_protein_g,
                actual_carbs_g=intake.actual_carbs_g,
                actual_fat_g=intake.actual_fat_g,
                actual_fiber_g=intake.actual_fiber_g,
                target_calories=intake.target_calories,
                target_protein_g=intake.target_protein_g,
                target_carbs_g=intake.target_carbs_g,
                target_fat_g=intake.target_fat_g,
                calories_remaining=intake.calories_remaining,
                protein_remaining_g=intake.protein_remaining_g,
                carbs_remaining_g=intake.carbs_remaining_g,
                fat_remaining_g=intake.fat_remaining_g,
                meals=intake.meals
            )
            daily_intake_responses.append(response)

        # Calculate averages
        total_days = len(daily_intakes)
        average_calories = sum(intake.actual_calories for intake in daily_intakes) / total_days
        average_protein_g = sum(intake.actual_protein_g for intake in daily_intakes) / total_days
        average_carbs_g = sum(intake.actual_carbs_g for intake in daily_intakes) / total_days
        average_fat_g = sum(intake.actual_fat_g for intake in daily_intakes) / total_days

        # Calculate target adherence (simplified)
        target_adherence_count = 0
        for intake in daily_intakes:
            if (intake.target_calories and
                abs(intake.actual_calories - intake.target_calories) / intake.target_calories < 0.2):
                target_adherence_count += 1

        target_adherence_percent = (target_adherence_count / total_days) * 100 if total_days > 0 else 0

        # Simple trend analysis
        trends = {}
        if len(daily_intakes) >= 7:
            recent_avg = sum(intake.actual_calories for intake in daily_intakes[-7:]) / 7
            earlier_avg = sum(intake.actual_calories for intake in daily_intakes[:7]) / 7

            if recent_avg > earlier_avg * 1.05:
                trends["calories"] = "increasing"
            elif recent_avg < earlier_avg * 0.95:
                trends["calories"] = "decreasing"
            else:
                trends["calories"] = "stable"

        return NutritionProgress(
            date_range=[datetime.combine(start_date, datetime.min.time()),
                       datetime.combine(end_date, datetime.min.time())],
            daily_intakes=daily_intake_responses,
            average_calories=average_calories,
            average_protein_g=average_protein_g,
            average_carbs_g=average_carbs_g,
            average_fat_g=average_fat_g,
            target_adherence_percent=target_adherence_percent,
            trends=trends
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get nutrition progress: {str(e)}"
        )
