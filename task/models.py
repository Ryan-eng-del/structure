from django.db import models

from django.contrib.auth.models import User


class AlgorithmSystemRuntimeStatus(models.Model):
    concurrency_status = models.IntegerField(default=2)
    mark = models.CharField(max_length=255)


class AlgorithmUserRuntimeStatus(models.Model):
    email = models.EmailField(primary_key=True)
    concurrency_status = models.IntegerField(default=9)
    last_time_run = models.DateTimeField(auto_now_add=True)


class AlgorithmSystemRuntimeControl(models.Model):
    concurrency_limit = models.IntegerField(default=2)

    class Meta:
        db_table = 'run_time_control'

    def is_exceed(self, count):
        return count >= self.concurrency_limit


# Create your models here.
class AlgorithmTask(models.Model):
    RUNNING = "running"
    SUCCESS = "success"
    CANCEL = "canceled"
    CREATED = "created"
    PENDING = "pending"

    STATUS_CHOICES = (
        (RUNNING, RUNNING),
        (SUCCESS, SUCCESS),
        (CANCEL, CANCEL),
        (CREATED, CREATED),
        (PENDING, PENDING)
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
    creator = models.ForeignKey(User, null=True, blank=True, on_delete=models.RESTRICT)

    class Meta:
        db_table = 'task'

# queue
class AlgorithmProcessQueue(models.Model):
    PENDING = "pending"
    RUNNING = "running"
    STATE_CHOICES = (
        (PENDING, PENDING),
        (RUNNING, RUNNING)
    )
    state=models.CharField(max_length=20, choices=STATE_CHOICES)
    task=models.ForeignKey(AlgorithmTask, on_delete=models.CASCADE)
    is_task_submit=models.BooleanField(default=False)

    class Meta:
        db_table = 'task_queue'


