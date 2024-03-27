def get_files_from_request(request):
  files = []
  if len(request.FILES):
    for _, file in request.FILES.items():
      files.append(file)

  return files


def generate_file_stream(file_path):
  with open(file_path) as f:
          while True:
              c=f.read(1024 * 1024 * 512)
              if c:
                  yield c
              else:
                  break