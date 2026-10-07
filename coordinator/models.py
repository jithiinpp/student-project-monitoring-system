from django.db import models

# =========================================================
# SCHEDULE DOCUMENT
# =========================================================

class ScheduleDocument(models.Model):
    document = models.FileField(upload_to="schedules/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Schedule Document uploaded on {self.uploaded_at.strftime('%Y-%m-%d')}"
