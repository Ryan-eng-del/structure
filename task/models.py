
import os
import subprocess
import logging
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from public.emali import send_mail_with_content


class AlgorithmSystemRuntimeStatus(models.Model):
    concurrency_status = models.IntegerField(default=0)
    mark = models.CharField(max_length=255)

    class Meta:
        db_table = 'run_time_status_system'

    def free(self):
        self.concurrency_status -= 1;
        self.save()

def get_system_status_control():
    runtime_control = None

    try:
        runtime_control = AlgorithmSystemRuntimeStatus.objects.get(mark="system")
    except AlgorithmSystemRuntimeStatus.DoesNotExist:
        runtime_control = AlgorithmSystemRuntimeStatus.objects.create(mark="system", concurrency_status=0)
    return runtime_control

class AlgorithmUserRuntimeStatus(models.Model):
    email = models.EmailField(primary_key=True)
    concurrency_status = models.IntegerField(default=0)
    last_time_run = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'run_time_status_user'

    def unfree(self):
        self.concurrency_status += 1;
        self.save()

    def free(self):
        self.concurrency_status -= 1;
        self.save()

def get_user_status_control(email):
    runtime_control = None
    try:
        runtime_control = AlgorithmUserRuntimeStatus.objects.get(email=email)
    except AlgorithmUserRuntimeStatus.DoesNotExist:
        runtime_control = AlgorithmUserRuntimeStatus.objects.create(email=email, concurrency_status=0, last_time_run=timezone.now())
    return runtime_control


class AlgorithmSystemRuntimeControl(models.Model):
    concurrency_limit = models.IntegerField(default=2)
    mark = models.CharField(max_length=255)
    user_limit = models.IntegerField(default=9)

    class Meta:
        db_table = 'run_time_control'

    def is_exceed(self, count):
        return count > self.concurrency_limit
    
    def is_user_exceed(self, count):
        return count > self.user_limit

def get_runtime_control():
    runtime_control = None
    try:
        runtime_control = AlgorithmSystemRuntimeControl.objects.get(mark="system")
    except AlgorithmSystemRuntimeControl.DoesNotExist:
        runtime_control = AlgorithmSystemRuntimeControl.objects.create(mark="system", concurrency_limit=2, user_limit=9)
    return runtime_control


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
    status = models.CharField(max_length=32,choices=STATUS_CHOICES, default=PENDING)
    workspace = models.CharField(max_length=5012, null=True, blank=True)
    workspace_dir = models.CharField(max_length=5012, null=True, blank=True)
    cmd =  models.CharField(max_length=5012, null=True, blank=True)
    finish_time = models.DateTimeField(null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True, db_comment="更新时间")
    create_time = models.DateTimeField(auto_now_add=True, db_comment="创建时间")
    email = models.EmailField(null=True, blank=True)

    class Meta:
        db_table = 'task'

# queue
class AlgorithmProcessQueue(models.Model):
    PENDING = "pending"
    RUNNING = "running"
    ACCOMPLISH = "accomplish"
    CANCEL = "cancel"
    STATE_CHOICES = (
        (PENDING, PENDING),
        (RUNNING, RUNNING),
        (ACCOMPLISH, ACCOMPLISH),
        (CANCEL, CANCEL)
    )
    state=models.CharField(max_length=20, choices=STATE_CHOICES, default=PENDING)
    task=models.ForeignKey(AlgorithmTask, on_delete=models.CASCADE)
    is_task_submit=models.BooleanField(default=False)

    class Meta:
        db_table = 'task_queue'

    def done(self):
      self.state = self.ACCOMPLISH
      self.save()


def exceed_user_maximum_task(user_control_status: AlgorithmUserRuntimeStatus, system_control: AlgorithmSystemRuntimeControl):
    now_time = timezone.now()
    now_day = now_time.day
    last_day = user_control_status.last_time_run.day

    if now_day == last_day and system_control.is_user_exceed(user_control_status.concurrency_status):
        return True
    
    if now_day != last_day:
        user_control_status.last_time_run = now_time
        user_control_status.concurrency_status = 0;
        user_control_status.save()
    
    return False


def require_task_queue():
    runtime_control_status: AlgorithmSystemRuntimeStatus = get_system_status_control()
    system_control: AlgorithmSystemRuntimeControl = get_runtime_control()

    if not system_control.is_exceed(runtime_control_status.concurrency_status):
        return True
    
    return False


def process_queue_update_status():
    if require_task_queue():
        tasks = AlgorithmProcessQueue.objects.filter(state=AlgorithmProcessQueue.PENDING, is_task_submit=False)
        if not tasks.exists():
            return
        task: AlgorithmProcessQueue = tasks[0]
        task.state = AlgorithmProcessQueue.RUNNING
        runtime_control_status: AlgorithmSystemRuntimeStatus = get_system_status_control()
        runtime_control_status.concurrency_status += 1
        runtime_control_status.save()
        task.save()
    else:
        logging.info("Processing queue have been to maximum number of tasks")

def cancel_task(algorithm_task: AlgorithmTask):
    algorithm_task.pid = -1
    algorithm_task.status = AlgorithmTask.CANCEL
    algorithm_task.save()


def run_task(algorithm_task: AlgorithmTask):
    cmd = algorithm_task.cmd
    try:
       subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
      logging.error(f'cmd: {algorithm_task.cmd} | workspace: {algorithm_task.workspace}')
      logging.error(f'--- Running cmd error {e} ---')

    # 使用ps命令查询相关进程
    ps_cmd = f"ps -ef | grep {algorithm_task.id.hex} | grep -v grep"
    ps_process = subprocess.Popen(ps_cmd, shell=True, stdout=subprocess.PIPE)

    # 读取ps命令的输出，获取PID
    ps_output = ps_process.stdout.read().decode('utf-8').strip()
    relevant_pid = None

    # 提取PID
    if ps_output:
        relevant_pid = ps_output.split()[1]

    if not relevant_pid:
        cancel_task(algorithm_task)
        return False

    pid = relevant_pid
    algorithm_task.pid = pid
    algorithm_task.status = AlgorithmTask.RUNNING
    algorithm_task.save()
    logging.info(f'--- Star run of task pid {pid} ---')
    return True

def process_queue_execute():
    tasks: list[AlgorithmProcessQueue] = AlgorithmProcessQueue.objects.filter(state=AlgorithmProcessQueue.RUNNING, is_task_submit=False)

    for t in tasks:
        algorithm_task: AlgorithmTask = t.task
        if run_task(algorithm_task):
            t.is_task_submit = True
            t.save()
        else:
            system_status_control = get_system_status_control()
            system_status_control.free()
            user_status_control = get_user_status_control(algorithm_task.email)
            user_status_control.free()
            t.state = AlgorithmProcessQueue.CANCEL
            t.is_task_submit = False
            t.save()

def schedule():
    # Status From Pending -> Running
    process_queue_update_status()

    # Execute Process Queue
    process_queue_execute()
    


def update_status():
    tasks: list[AlgorithmProcessQueue] = AlgorithmProcessQueue.objects.filter(state=AlgorithmProcessQueue.RUNNING, is_task_submit=True)
    for task in tasks:
      # 获取任务标识
      algorithm_task: AlgorithmTask = task.task
      task_uuid = algorithm_task.id
      task_pid = algorithm_task.pid

      # 检查进程是否存在
      try:
          # 尝试发送一个信号到进程
          os.kill(int(task_pid), 0)
      except OSError:
          # 进程不存在
          if algorithm_task.status == AlgorithmTask.SUCCESS:
              return
          
          algorithm_task.status = AlgorithmTask.SUCCESS
          algorithm_task.finish_time = timezone.now()
          algorithm_task.save()
          text = render_to_string("result.html", {
              "username" : "cyan",
          })
          workspace_path = os.path.join(settings.WORKSPACE_PATH, 'pdb.zip')
          send_mail_with_content(["cyan0908@163.com"], "Task Execution Results", text, file_path=workspace_path)
          task.done()
          system_status_control = get_system_status_control()
          system_status_control.free()
          return
      
      # 检查任务标识是否匹配
      try:
          with open(f"/proc/{task.pid}/cmdline", "r") as cmdline_file:
              cmdline = cmdline_file.read()
              if task_uuid not in cmdline:
                  # 进程存在但不是当前任务
                if algorithm_task.status == AlgorithmTask.SUCCESS:
                  return
                algorithm_task.status = models.AlgorithmTask.SUCCESS
                algorithm_task.finish_time = timezone.now()
                algorithm_task.save()

                text = render_to_string("result.html", {
                    "username" : "cyan",
                })
                workspace_path = os.path.join(settings.WORKSPACE_PATH, 'pdb.zip')
                send_mail_with_content(["cyan0908@163.com"], "Task Execution Results", text, file_path=workspace_path)
                task.done()
                system_status_control = get_system_status_control()
                system_status_control.free()
      except Exception:
        pass