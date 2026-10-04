from collections import Counter
from dataclasses import dataclass

from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import Now
from django.urls import reverse


class MemberQuerySet(models.QuerySet):
    def with_open_task_counts(self):
        """Annotates each member with `open_tasks`: their tasks not yet done."""
        return self.annotate(
            open_tasks=Count("tasks", filter=~Q(tasks__status=Task.Status.DONE))
        )


class Member(models.Model):
    name = models.CharField()
    email = models.EmailField()
    created_at = models.DateTimeField(db_default=Now())

    objects = MemberQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


@dataclass
class Progress:
    todo: int
    in_progress: int
    done: int

    @property
    def percent_done(self):
        total = self.todo + self.in_progress + self.done
        return 0 if total == 0 else self.done * 100 // total


@dataclass
class BoardColumn:
    status: "Task.Status"
    tasks: list["Task"]


class Project(models.Model):
    # Board filter for tasks nobody is assigned to.
    UNASSIGNED = "unassigned"

    name = models.CharField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project", args=[self.pk])

    # Worked out from the tasks every time, never stored. Prefetch `tasks`
    # when listing projects.
    def progress(self):
        counts = Counter(task.status for task in self.tasks.all())
        return Progress(
            todo=counts[Task.Status.TODO],
            in_progress=counts[Task.Status.IN_PROGRESS],
            done=counts[Task.Status.DONE],
        )

    def board(self, assignee=None):
        """The three columns, oldest task first. `assignee` is a member,
        UNASSIGNED, or None for everyone."""
        tasks = self.tasks.select_related("assignee").annotate(
            comment_count=Count("comments")
        )
        if assignee == self.UNASSIGNED:
            tasks = tasks.filter(assignee__isnull=True)
        elif assignee is not None:
            tasks = tasks.filter(assignee=assignee)
        tasks = list(tasks.order_by("id"))
        return [
            BoardColumn(status, [task for task in tasks if task.status == status])
            for status in Task.Status
        ]


class TaskStatusError(Exception):
    """A task was given a status that is not one of the three."""

    def __init__(self, status):
        super().__init__(f'"{status}" is not a task status.')


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField()
    description = models.TextField(blank=True)
    status = models.CharField(choices=Status, default=Status.TODO)
    assignee = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("task", args=[self.pk])

    def other_statuses(self):
        return [status for status in self.Status if status != self.status]

    def set_status(self, status):
        if status not in self.Status.values:
            raise TaskStatusError(status)
        self.status = status
        self.save(update_fields=["status"])


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="comments"
    )
    body = models.TextField()
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return self.body
