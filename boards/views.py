from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, MemberForm, ProjectForm, TaskForm
from .models import Member, Project, Task


def project_list(request):
    return render(
        request,
        "projects/list.html",
        {"projects": Project.objects.prefetch_related("tasks")},
    )


def project_new(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        return redirect(form.save())
    return render(
        request,
        "projects/form.html",
        {"form": form, "title": "New project", "submit_label": "Create project"},
    )


def project_board(request, pk):
    project = get_object_or_404(Project, pk=pk)
    members = list(Member.objects.all())
    # "unassigned", a member's id, or anything else for everyone.
    value = request.GET.get("assignee")
    if value == Project.UNASSIGNED:
        assignee = Project.UNASSIGNED
    else:
        assignee = next((m for m in members if str(m.pk) == value), None)
    filters = [("All", None, "")]
    filters += [(member.name, member, f"?assignee={member.pk}") for member in members]
    filters += [("Unassigned", Project.UNASSIGNED, f"?assignee={Project.UNASSIGNED}")]
    return render(
        request,
        "projects/board.html",
        {
            "project": project,
            "columns": project.board(assignee),
            "filters": filters,
            "assignee": assignee,
        },
    )


def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        return redirect(form.save())
    return render(
        request,
        "projects/form.html",
        {"form": form, "title": f"Edit {project.name}", "submit_label": "Save changes"},
    )


def task_new(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = TaskForm(request.POST or None)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        return redirect(task)
    return render(
        request,
        "tasks/form.html",
        {
            "form": form,
            "project": project,
            "title": "New task",
            "submit_label": "Create task",
        },
    )


def _task_page(request, task, comment_form):
    return render(
        request,
        "tasks/detail.html",
        {
            "task": task,
            "comments": task.comments.select_related("author"),
            "comment_form": comment_form,
        },
    )


def task_detail(request, pk):
    task = get_object_or_404(Task.objects.select_related("project", "assignee"), pk=pk)
    return _task_page(request, task, CommentForm())


def task_edit(request, pk):
    task = get_object_or_404(Task.objects.select_related("project"), pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        return redirect(form.save())
    return render(
        request,
        "tasks/form.html",
        {
            "form": form,
            "project": task.project,
            "title": f"Edit {task.title}",
            "submit_label": "Save changes",
        },
    )


@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task.objects.select_related("project"), pk=pk)
    task.delete()
    return redirect(task.project)


@require_POST
def task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.set_status(request.POST["status"])
    return redirect(task)


@require_POST
def comment_new(request, pk):
    task = get_object_or_404(Task.objects.select_related("project", "assignee"), pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.save()
        return redirect(task)
    return _task_page(request, task, form)


def member_list(request):
    return render(
        request,
        "members/list.html",
        {"members": Member.objects.with_open_task_counts()},
    )


def member_new(request):
    form = MemberForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("member_list")
    return render(request, "members/form.html", {"form": form})
