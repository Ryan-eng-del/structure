from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TaskViewSet, basename='task')

urlpatterns = [
    path('task/', include(router.urls)),
    path('query/', views.TaskQueryAPIView.as_view()),
    path('workspace/', views.WorkspaceAPIView.as_view()),
    path('chain_file/', views.ChainFileAPIView.as_view()),
    path('chain_id/', views.ChainIdAPIView.as_view()),
] 