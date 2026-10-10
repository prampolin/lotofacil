from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Contest
from .serializers import (
    BacktestSerializer,
    ContestSerializer,
    GenerationSerializer,
    StatisticsQuerySerializer,
)
from .services.backtesting import stored_backtest
from .services.game_generator import generate_games
from .services.statistics import DomainError, EmptyDataError, stored_statistics


def health_check(request):
    return JsonResponse(
        {"status": "ok", "service": "lotofacil-api", "version": "1.0.0"}
    )


class LatestContestView(APIView):
    def get(self, request):
        contest = Contest.objects.order_by("-number").first()

        if contest is None:
            return Response({"error": "Nenhum concurso encontrado."}, status=404)

        serializer = ContestSerializer(contest)

        return Response(serializer.data)


class ContestDetailView(APIView):
    def get(self, request, number):
        contest = get_object_or_404(Contest, number=number)

        serializer = ContestSerializer(contest)

        return Response(serializer.data)


class DomainView(APIView):
    def respond(self, serializer):
        serializer.is_valid(raise_exception=True)
        try:
            return Response(self.service(**serializer.validated_data))
        except EmptyDataError as error:
            return Response({"detail": str(error)}, status=404)
        except DomainError as error:
            return Response({"detail": str(error)}, status=400)


class StatisticsView(DomainView):
    service = staticmethod(stored_statistics)

    def get(self, request):
        return self.respond(StatisticsQuerySerializer(data=request.query_params))


class GenerateGamesView(DomainView):
    service = staticmethod(generate_games)

    def post(self, request):
        return self.respond(GenerationSerializer(data=request.data))


class BacktestView(DomainView):
    service = staticmethod(stored_backtest)

    def post(self, request):
        return self.respond(BacktestSerializer(data=request.data))
