from django.db import models

from apps.common.models import BaseModel


class JournalType(models.TextChoices):
    SCOPUS = "scopus", "Scopus"
    WOS = "wos", "Web of Science"
    VAK = "vak", "ВАК"
    RINC = "rinc", "РИНЦ"
    OTHER = "other", "Прочее"


JOURNAL_POINTS = {
    JournalType.SCOPUS: 25,
    JournalType.WOS: 25,
    JournalType.VAK: 15,
    JournalType.RINC: 8,
    JournalType.OTHER: 3,
}


class Publication(BaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="publications",
    )
    title = models.CharField(max_length=1000)
    journal = models.CharField(max_length=500, blank=True, default="")
    journal_type = models.CharField(max_length=10, choices=JournalType.choices)
    pub_date = models.DateField()
    url = models.CharField(max_length=2048, blank=True, default="")
    coauthors = models.TextField(blank=True, default="")
    kpi_indicator = models.ForeignKey(
        "kpi.KPI",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publications",
    )
    evidence_file = models.CharField(max_length=500, blank=True, default="")
    is_archived = models.BooleanField(default=False)
    academic_year = models.CharField(max_length=10)

    @property
    def kpi_points(self):
        return JOURNAL_POINTS.get(self.journal_type, 0)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"
        ordering = ["-pub_date", "-created_at"]
