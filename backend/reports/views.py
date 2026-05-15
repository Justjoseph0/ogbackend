from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .ai import generate_report
from .data import build_activity_snapshot, detect_input_type
from .models import StoredReport
from .serializers import AnalyzeSerializer, StoreSerializer, StoredReportSerializer
from .storage_0g import retrieve_report_from_0g, upload_report_to_0g


@api_view(["POST"])
def analyze(request):
    serializer = AnalyzeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    query = serializer.validated_data["query"]
    raw_data = build_activity_snapshot(query, serializer.validated_data.get("chain_id"))
    report, ai_meta = generate_report(query, raw_data)
    return Response(
        {
            "query": query,
            "input_type": detect_input_type(query),
            "raw_data": raw_data,
            "report": report,
            "ai": ai_meta,
        }
    )


@api_view(["POST"])
def store(request):
    serializer = StoreSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    ai_meta = payload.pop("ai", None)
    if ai_meta:
        payload["report"] = {**payload["report"], "_ai": ai_meta}
    storage_payload = _compact_storage_payload(payload)
    try:
        storage_result = upload_report_to_0g(storage_payload)
    except Exception as exc:
        return Response(
            {
                "detail": "0G storage upload failed",
                "error": str(exc),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )
    stored = StoredReport.objects.create(**payload, **storage_result)
    return Response(StoredReportSerializer(stored).data, status=status.HTTP_201_CREATED)


def _compact_storage_payload(payload):
    raw_data = payload.get("raw_data", {})
    compact_raw = {
        key: value
        for key, value in raw_data.items()
        if key
        not in {
            "recent_transactions",
        }
    }
    if raw_data.get("recent_transactions"):
        compact_raw["recent_transactions"] = raw_data["recent_transactions"][:3]
    return {
        "query": payload.get("query"),
        "input_type": payload.get("input_type"),
        "report": payload.get("report"),
        "raw_data": compact_raw,
    }


@api_view(["GET"])
def history(request):
    reports = StoredReport.objects.all()
    return Response(StoredReportSerializer(reports, many=True).data)


@api_view(["GET"])
def report_detail(request, pk):
    try:
        stored = StoredReport.objects.get(pk=pk)
    except StoredReport.DoesNotExist as exc:
        raise NotFound("Report not found") from exc
    data = StoredReportSerializer(stored).data
    retrieved = retrieve_report_from_0g(stored.root_hash)
    if retrieved:
        data["retrieved_from_0g"] = retrieved
    return Response(data)
