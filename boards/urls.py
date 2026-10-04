from django.urls import path

from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("projects/new", views.project_new, name="project_new"),
    path("projects/<int:pk>", views.project_board, name="project"),
    path("projects/<int:pk>/edit", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/tasks/new", views.task_new, name="task_new"),
    path("tasks/<int:pk>", views.task_detail, name="task"),
    path("tasks/<int:pk>/edit", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete", views.task_delete, name="task_delete"),
    path("tasks/<int:pk>/status", views.task_status, name="task_status"),
    path("tasks/<int:pk>/comments", views.comment_new, name="comment_new"),
    path("members", views.member_list, name="member_list"),
    path("members/new", views.member_new, name="member_new"),
]
