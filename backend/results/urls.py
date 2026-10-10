from django.urls import path

from .views import (
    BacktestView,
    ContestDetailView,
    GenerateGamesView,
    LatestContestView,
    StatisticsView,
    health_check,
)

urlpatterns = [
    path("statistics/", StatisticsView.as_view(), name="statistics"),
    path("games/generate/", GenerateGamesView.as_view(), name="generate-games"),
    path("backtests/", BacktestView.as_view(), name="backtests"),
    path("health/", health_check, name="health-check"),
    path("results/latest/", LatestContestView.as_view(), name="latest-contest"),
    path("results/<int:number>/", ContestDetailView.as_view(), name="contest-detail"),
]
