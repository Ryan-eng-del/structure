
import uuid
import os
import logging
from . import models 
from django.http import JsonResponse
from django.template import Context, Template
from rest_framework.viewsets import ModelViewSet
from django.template.loader import render_to_string
from public.emali import send_mail_with_content
from public.utils import get_files_from_request
from django.utils import timezone
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.db import transaction

# 3 10
# Create your views here.
# 计算链
# 创建工作空间 上传文件
# 在指定工作空间，执行算法
class TaskViewSet(ModelViewSet):
  queryset = models.AlgorithmTask.objects.all()

  def create(self, request, *args, **kwargs):
    try:
       workspace_dir = request.data["workspace_dir"]
       email = request.data["email"]
    except Exception as e:
       raise ValidationError({"message": "please input email and workspace_dir"})

    user_status_control: models.AlgorithmUserRuntimeStatus = models.get_user_status_control(email)
    system_control : models.AlgorithmSystemRuntimeControl = models.get_runtime_control()


    if models.exceed_user_maximum_task(user_status_control, system_control):
      raise ValidationError({"message": "任务数量已经达到每日任务上限，请明天再来"})
  
    user_status_control.unfree()

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
    logging.info(f'{email} Join cmd {cmd}')
    logging.info("------------------------------------------")
    
    with transaction.atomic():
      # 记录任务
      t: models.AlgorithmTask = models.AlgorithmTask.objects.create(id=task_uuid, workspace_dir=workspace_path, workspace=workspace_dir, cmd=cmd, email=email)
      # 放入队列
      models.AlgorithmProcessQueue.objects.create(task=t)

    return JsonResponse({'uuid': task_uuid, 'workspace': workspace_dir, 'workspace_path': workspace_path})
  
class TaskQueryAPIView(APIView):
  def get(self, request, *args, **kwargs):
    logging.info("----- Begin Task Query ----- ")
    # 状态更新
    logging.info("--- Begin Status Update ---")
    try:
       models.update_status()
    except Exception as e:
       logging.error(e)
    logging.info("--- End Status Update ---")

    # 调度任务
    logging.info("--- Start Schedule Task ---")
    try:
      models.schedule()
    except Exception as e:
      logging.error(e)
    logging.info("--- End Schedule Task ---")

    logging.info("----- End Task Query ----- ")

    # 统计任务
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


