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
    storage_result = upload_report_to_0g(payload)
    stored = StoredReport.objects.create(**payload, **storage_result)
    return Response(StoredReportSerializer(stored).data, status=status.HTTP_201_CREATED)


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
