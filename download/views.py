import mimetypes
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from public.utils import generate_file_stream

# Create your views here.
class DownloadFileAPIView(APIView):
  def get(self, request, *args, **kwargs):
    try:
      file_path = request.query_params["file_path"]
      file_name = request.query_params["file_name"]
    except Exception as e:
      raise ValidationError("please pass file_path")
    response=StreamingHttpResponse(generate_file_stream(file_path=file_path))
    response.headers['Content-Disposition'] = "attachment; filename="+file_name
    response.headers['Content-Type'] = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
    return response



    
