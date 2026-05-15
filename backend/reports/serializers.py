from rest_framework import serializers

from .models import StoredReport


class AnalyzeSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255, trim_whitespace=True)
    chain_id = serializers.IntegerField(required=False, min_value=1)


class StoreSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255)
    input_type = serializers.CharField(max_length=32)
    raw_data = serializers.JSONField()
    report = serializers.JSONField()
    ai = serializers.JSONField(required=False)


class StoredReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoredReport
        fields = [
            "id",
            "query",
            "input_type",
            "raw_data",
            "report",
            "root_hash",
            "tx_hash",
            "explorer_url",
            "storage_status",
            "created_at",
        ]
