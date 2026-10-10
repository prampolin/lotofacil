from rest_framework import serializers

from .models import Contest


class ContestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = [
            "number",
            "draw_date",
            "numbers",
        ]


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                {"non_field_errors": ["Envie um objeto JSON."]}
            )
        unknown = data.keys() - self.fields.keys()
        if unknown:
            raise serializers.ValidationError(
                {key: ["Campo desconhecido."] for key in sorted(unknown)}
            )
        return super().to_internal_value(data)


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail("invalid")
        return super().to_internal_value(data)


class StatisticsQuerySerializer(StrictSerializer):
    window = serializers.IntegerField(default=100, min_value=1, max_value=1000)
    as_of_contest = serializers.IntegerField(
        required=False, min_value=1, max_value=2147483647
    )


class ConstraintsSerializer(StrictSerializer):
    odd_min = StrictIntegerField(required=False, min_value=0, max_value=15)
    odd_max = StrictIntegerField(required=False, min_value=0, max_value=15)
    sum_min = StrictIntegerField(required=False, min_value=120, max_value=270)
    sum_max = StrictIntegerField(required=False, min_value=120, max_value=270)


class GenerationSerializer(StrictSerializer):
    quantity = StrictIntegerField(default=1, min_value=1, max_value=100)
    seed = StrictIntegerField(
        required=False, allow_null=True, min_value=-(2**63), max_value=2**63 - 1
    )
    constraints = ConstraintsSerializer(required=False)


class BacktestSerializer(StrictSerializer):
    start_contest = StrictIntegerField(min_value=1, max_value=2147483647)
    end_contest = StrictIntegerField(min_value=1, max_value=2147483647)
    mode = serializers.ChoiceField(choices=["fixed_games", "rolling_baseline"])
    games = serializers.ListField(
        child=serializers.ListField(
            child=StrictIntegerField(min_value=1, max_value=25),
            min_length=15,
            max_length=15,
        ),
        min_length=1,
        max_length=100,
        required=False,
    )
    quantity = StrictIntegerField(required=False, min_value=1, max_value=100)
    seed = StrictIntegerField(
        required=False, allow_null=True, min_value=-(2**63), max_value=2**63 - 1
    )
