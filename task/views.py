from django.http import JsonResponse
from rest_framework.viewsets import ModelViewSet
import uuid
import subprocess
from . import models 
from django.utils import timezone
import os
from django.conf import settings
import logging
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.views import APIView

# Create your views here.
# 计算链
# 创建工作空间 上传文件
# 在指定工作空间，执行算法

class TaskViewSet(ModelViewSet):

  def create(self, request, *args, **kwargs):
    # 生成uuid和任务标识
    task_uuid = str(uuid.uuid4().hex)
    pid = None
    retry_time = 0
    workspace_time = timezone.now().strftime("%Y%m%d%H%M%S%f")[:-6]
    workspace_uuid = str(uuid.uuid4())[:6]
    workspace_dir = f'{workspace_time}{workspace_uuid}'
    workspace_path = os.path.join(settings.WORKSPACE_PATH, workspace_dir)
    while True:
       if os.path.exists(workspace_path):
          workspace_path = workspace_path + str(retry_time)
          retry_time += 1
       else:
          break  
       
    # 创建工作空间
    os.makedirs(workspace_path)
    # output 日志
    outputLog = os.path.join(workspace_path, "task_output.inf.log")
    # error 日志
    errorLog = os.path.join(workspace_path, "task_error.wf.log")

    # 执行算法任务
    cmd = f"nohup /bin/bash -c 'echo {task_uuid} && /bin/bash algorithm.sh' 1>{outputLog} 2>{errorLog} &"
    
    logging.info("------------------------------------------")
    logging.info(f'Running cmd {cmd}')
    logging.info("------------------------------------------")
    

    # 记录任务
    t: models.AlgorithmTask = models.AlgorithmTask.objects.create(id=task_uuid, workspace_dir=workspace_path, workspace=workspace_dir, cmd=cmd)

    # Run
    try:
      process = subprocess.Popen(cmd, shell=True)
    except Exception as e:
      logging.error("------------------------------------------")
      logging.error(f'Running cmd error {e}')
      logging.error("------------------------------------------")
      raise ValidationError("Execute Shell Error: 执行算法任务失败")
    pid = process.pid

    t.pid = pid
    t.status = models.AlgorithmTask.RUNNING
    t.save()

    logging.info("------------------------------------------")
    logging.info(f'Task pid {pid}')
    logging.info("------------------------------------------")
    return JsonResponse({'uuid': task_uuid, 'pid': pid})
  
class TaskQueryAPIView(APIView):
  def get(self, request, *args, **kwargs):
    logging.info("------------------------------------------")
    logging.info(f'调用 Query 接口 查询状态')
    logging.info("------------------------------------------")
    tasks = models.AlgorithmTask.objects.filter(status=models.AlgorithmTask.RUNNING)
    logging.info(f'{len(tasks)} 个正在运行的任务')
    logging.info("------------------------------------------")

    for task in tasks:
      # 获取任务标识
      task_uuid = task.id
      task_pid = task.pid

      # 检查进程是否存在
      try:
          # 尝试发送一个信号到进程
          os.kill(int(task_pid), 0)
      except OSError:
          # 进程不存在
          task.status = models.AlgorithmTask.SUCCESS
          task.finish_time = timezone.now()
          task.save()
          # todo 将结果发送给用户
          continue
      
      # 检查任务标识是否匹配
      try:
          with open(f"/proc/{task.pid}/cmdline", "r") as cmdline_file:
              cmdline = cmdline_file.read()
              if task_uuid not in cmdline:
                  # 进程存在但不是当前任务
                  task.status = models.AlgorithmTask.SUCCESS
                  task.finish_time = timezone.now()
                  task.save()
                  # todo 将结果发送给用户
                  
      except Exception:
          # 进程不存在 /proc 目录下
        pass

    return JsonResponse({"message": "query successfully"})
  


class WorkspaceAPIView(APIView):
  def post(self, request, *args, **kwargs):
    pass

class ChainFileAPIView(APIView):
  def post(self, request, *args, **kwargs):
    pass


class ChainIdAPIView(APIView):
  def post(self, request, *args, **kwargs):
    pass


