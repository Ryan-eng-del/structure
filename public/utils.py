def get_files_from_request(request):
  files = []
  if len(request.FILES):
    for _, file in request.FILES.items():
      files.append(file)

  return files


