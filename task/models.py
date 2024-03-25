from django.db import models

# Create your models here.
class AlgorithmTask(models.Model):
    RUNNING = "running"
    SUCCESS = "success"
    CANCEL = "canceled"
    CREATED = "created"

    STATUS_CHOICES = (
        (RUNNING, RUNNING),
        (SUCCESS, SUCCESS),
        (CANCEL, CANCEL),
        (CREATED, CREATED)
    )

    id = models.UUIDField(max_length=128, primary_key=True)
    pid = models.CharField(max_length=256, null=True, blank=True)
    status = models.CharField(max_length=32,choices=STATUS_CHOICES, default=CREATED)
    workspace = models.CharField(max_length=5012, null=True, blank=True)
    workspace_dir = models.CharField(max_length=5012, null=True, blank=True)
    cmd =  models.CharField(max_length=5012, null=True, blank=True)
    finish_time = models.DateTimeField(null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True, db_comment="更新时间")
    create_time = models.DateTimeField(auto_now_add=True, db_comment="创建时间")

    class Meta:
        db_table = 'task'