"""
AI recommendation endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional

from app.models.user import User
from app.models.recommendation import (
    Recommendation, RecommendationRequest, RecommendationResponse,
    RecommendationFeedback, RecommendationStats
)
from app.services.auth import AuthService
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()


@router.post("/generate")
async def generate_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Generate AI-powered recommendations for the user."""
    try:
        recommendation_engine = RecommendationEngine()

        # Deactivate old recommendations first
        await recommendation_engine.deactivate_old_recommendations(str(current_user.id))

        # Generate new recommendations
        recommendations = await recommendation_engine.generate_comprehensive_recommendations(
            user=current_user,
            current_intake=None,  # Will be fetched automatically
            meal_type=None
        )

        # Save recommendations to database
        saved_recommendations = []
        for rec in recommendations:
            await rec.insert()
            saved_recommendations.append(rec)

        # Convert to response format
        response_recommendations = []
        for rec in saved_recommendations:
            response_rec = RecommendationResponse(
                id=str(rec.id),
                recommendation_type=rec.recommendation_type,
                title=rec.title,
                description=rec.description,
                confidence_level=rec.confidence_level,
                food_suggestions=rec.food_suggestions,
                meal_plan=rec.meal_plan,
                nutrient_adjustments=rec.nutrient_adjustments,
                priority=rec.priority,
                expected_impact=rec.expected_impact,
                implementation_difficulty=rec.implementation_difficulty,
                time_horizon=rec.time_horizon,
                is_viewed=rec.is_viewed,
                is_accepted=rec.is_accepted,
                user_rating=rec.user_rating,
                created_at=rec.created_at,
                valid_until=rec.valid_until
            )
            response_recommendations.append(response_rec)

        return response_recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/")
async def get_user_recommendations(
    active_only: Optional[bool] = True,
    limit: Optional[int] = 10,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get user's recommendations."""
    try:
        recommendation_engine = RecommendationEngine()

        recommendations = await recommendation_engine.get_user_recommendations(
            user_id=str(current_user.id),
            active_only=active_only,
            limit=limit
        )

        # Convert to response format
        response_recommendations = []
        for rec in recommendations:
            response_rec = RecommendationResponse(
                id=str(rec.id),
                recommendation_type=rec.recommendation_type,
                title=rec.title,
                description=rec.description,
                confidence_level=rec.confidence_level,
                food_suggestions=rec.food_suggestions,
                meal_plan=rec.meal_plan,
                nutrient_adjustments=rec.nutrient_adjustments,
                priority=rec.priority,
                expected_impact=rec.expected_impact,
                implementation_difficulty=rec.implementation_difficulty,
                time_horizon=rec.time_horizon,
                is_viewed=rec.is_viewed,
                is_accepted=rec.is_accepted,
                user_rating=rec.user_rating,
                created_at=rec.created_at,
                valid_until=rec.valid_until
            )
            response_recommendations.append(response_rec)

        return response_recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/{recommendation_id}")
async def get_recommendation_details(
    recommendation_id: str,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get detailed information about a specific recommendation."""
    try:
        recommendation_engine = RecommendationEngine()

        recommendation = await recommendation_engine.get_recommendation_by_id(
            recommendation_id=recommendation_id,
            user_id=str(current_user.id)
        )

        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )

        # Mark as viewed
        if not recommendation.is_viewed:
            recommendation.is_viewed = True
            await recommendation.save()

        return RecommendationResponse(
            id=str(recommendation.id),
            recommendation_type=recommendation.recommendation_type,
            title=recommendation.title,
            description=recommendation.description,
            confidence_level=recommendation.confidence_level,
            food_suggestions=recommendation.food_suggestions,
            meal_plan=recommendation.meal_plan,
            nutrient_adjustments=recommendation.nutrient_adjustments,
            priority=recommendation.priority,
            expected_impact=recommendation.expected_impact,
            implementation_difficulty=recommendation.implementation_difficulty,
            time_horizon=recommendation.time_horizon,
            is_viewed=recommendation.is_viewed,
            is_accepted=recommendation.is_accepted,
            user_rating=recommendation.user_rating,
            created_at=recommendation.created_at,
            valid_until=recommendation.valid_until
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation details: {str(e)}"
        )


@router.post("/{recommendation_id}/feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    feedback: RecommendationFeedback,
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Submit feedback for a recommendation."""
    try:
        recommendation_engine = RecommendationEngine()

        success = await recommendation_engine.update_recommendation_feedback(
            recommendation_id=recommendation_id,
            user_id=str(current_user.id),
            is_accepted=feedback.is_accepted,
            rating=feedback.rating,
            feedback=feedback.feedback
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )

        return {"message": "Feedback submitted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/stats/summary")
async def get_recommendation_stats(
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """Get recommendation statistics for the user."""
    try:
        recommendation_engine = RecommendationEngine()

        stats = await recommendation_engine.get_recommendation_stats(str(current_user.id))

        # Convert recent recommendations to response format
        recent_recommendations = []
        for rec in stats["recent_recommendations"]:
            response_rec = RecommendationResponse(
                id=str(rec.id),
                recommendation_type=rec.recommendation_type,
                title=rec.title,
                description=rec.description,
                confidence_level=rec.confidence_level,
                food_suggestions=rec.food_suggestions,
                meal_plan=rec.meal_plan,
                nutrient_adjustments=rec.nutrient_adjustments,
                priority=rec.priority,
                expected_impact=rec.expected_impact,
                implementation_difficulty=rec.implementation_difficulty,
                time_horizon=rec.time_horizon,
                is_viewed=rec.is_viewed,
                is_accepted=rec.is_accepted,
                user_rating=rec.user_rating,
                created_at=rec.created_at,
                valid_until=rec.valid_until
            )
            recent_recommendations.append(response_rec)

        return RecommendationStats(
            total_recommendations=stats["total_recommendations"],
            active_recommendations=stats["active_recommendations"],
            accepted_recommendations=stats["accepted_recommendations"],
            average_rating=stats["average_rating"],
            recommendations_by_type=stats["recommendations_by_type"],
            recent_recommendations=recent_recommendations
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation statistics: {str(e)}"
        )
