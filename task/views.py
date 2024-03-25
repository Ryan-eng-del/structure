from django.http import JsonResponse
from django.template import Context, Template
from rest_framework.viewsets import ModelViewSet
import uuid
import subprocess
from django.template.loader import render_to_string
from public.emali import send_mail_with_content
from public.utils import get_files_from_request
from . import models 
from django.utils import timezone
import os
from django.conf import settings
import logging
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

# Create your views here.
# 计算链
# 创建工作空间 上传文件
# 在指定工作空间，执行算法

class TaskViewSet(ModelViewSet):
  def create(self, request, *args, **kwargs):
    workspace_dir = request.data["workspace_dir"]
    # 生成uuid和任务标识
    task_uuid = str(uuid.uuid4().hex)
    pid = None
    workspace_path = os.path.join(settings.WORKSPACE_PATH, workspace_dir)

    if not os.path.exists(workspace_path):
       raise ValidationError({"message": "请先创建工作区"})
    
    # output 日志
    outputLog = os.path.join(workspace_path, "task_output.inf.log")
    # error 日志
    errorLog = os.path.join(workspace_path, "task_error.wf.log")
    # algorithm sh
    taskPath = os.path.join(workspace_path, "task.sh")
  
    if os.path.exists(taskPath):
       raise ValidationError({"message": "任务已经存在"})

    template_str = """
#!/bin/bash

echo "Started"
sh {{ algorithm_path }} --input {{ input }} --output {{ output }}
curl {{ callback_url }}
echo "Completed"

    """
    # 编译模板
    template = Template(template_str)

    variables = {
       "input": "-a 100 -c 50",
       "output": workspace_path,
       "algorithm_path": os.path.join(settings.WORKSPACE_PATH, "a.sh"),
       "callback_url":  f'{settings.APP_URL}/api/query/'
    }

    # 创建上下文并解析变量
    context = Context(variables)
    result = template.render(context)
    with open(taskPath, "w") as task_file:
      task_file.write(result) 

    # 执行算法任务
    cmd = f"nohup /bin/bash -c 'echo {task_uuid} && /bin/bash {taskPath}' 1>{outputLog} 2>{errorLog} &"
    
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
    tasks: list[models.AlgorithmTask] = models.AlgorithmTask.objects.filter(status=models.AlgorithmTask.RUNNING)
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
          text = render_to_string("result.html", {
              "username" : "cyan",
          })
          workspace_path = os.path.join(settings.WORKSPACE_PATH, 'pdb.zip')
          send_mail_with_content(["cyan0908@163.com"], "Task Execution Results", text, file_path=workspace_path)
          return JsonResponse({"message": "send successfully"})
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
    # 将所有文件放入工作空间
    files = get_files_from_request(request)

    # 写入文件
    for file in files:
       with open(f'{workspace_path}/{file.name}', 'w')  as f:
          f.write(str(file.read()))
    return JsonResponse({"work_dir": workspace_dir})

class ChainFileAPIView(APIView):
  def post(self, request, *args, **kwargs):
    file = get_files_from_request(request)[0]
    return JsonResponse({"file": file.name, "chains": ["A", "B", "AB"]})

class ChainIdAPIView(APIView):
  def post(self, request, *args, **kwargs):
    pid = request.data["pid"]
    return JsonResponse({"protein_id": pid, "chains": ["A", "B", "AB"]})


