from django.db import models


class StoredReport(models.Model):
    query = models.CharField(max_length=255)
    input_type = models.CharField(max_length=32)
    raw_data = models.JSONField(default=dict)
    report = models.JSONField(default=dict)
    root_hash = models.CharField(max_length=132, blank=True)
    tx_hash = models.CharField(max_length=132, blank=True)
    explorer_url = models.URLField(blank=True)
    storage_status = models.CharField(max_length=64, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.query} ({self.storage_status})"
