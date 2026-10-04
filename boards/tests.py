from django.test import TestCase

from .models import Comment, Member, Project, Task, TaskStatusError


def titles(columns):
    return {column.status: [task.title for task in column.tasks] for column in columns}


class BoardTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Website relaunch")

    def add_task(self, project=None, title="A task", status="todo", assignee=None):
        return Task.objects.create(
            project=project or self.project,
            title=title,
            status=status,
            assignee=assignee,
        )

    def test_progress_counts_tasks_per_status_and_percent_done(self):
        for status in ["todo", "todo", "in_progress", "done", "done", "done"]:
            self.add_task(status=status)
        empty = Project.objects.create(name="Empty")

        progress = self.project.progress()
        self.assertEqual(
            (progress.todo, progress.in_progress, progress.done, progress.percent_done),
            (2, 1, 3, 50),
        )
        progress = empty.progress()
        self.assertEqual(
            (progress.todo, progress.in_progress, progress.done, progress.percent_done),
            (0, 0, 0, 0),
        )

    def test_board_filters_by_assignee_or_unassigned_and_groups_by_status(self):
        omar = Member.objects.create(name="Omar Haddad", email="omar@example.com")
        nina = Member.objects.create(name="Nina Patel", email="nina@example.com")
        other_project = Project.objects.create(name="Mobile app")

        self.add_task(title="Migrate blog posts", assignee=omar)
        self.add_task(title="Build pricing page", status="in_progress", assignee=omar)
        self.add_task(title="Ship launch post", status="done", assignee=omar)
        self.add_task(title="Write homepage copy", status="done", assignee=nina)
        self.add_task(title="Accessibility review")
        self.add_task(title="Contact form")
        self.add_task(title="Final check", status="done")
        self.add_task(project=other_project, title="Offline mode", assignee=omar)
        self.add_task(project=other_project, title="Dark mode")

        self.assertEqual(
            titles(self.project.board(omar)),
            {
                "todo": ["Migrate blog posts"],
                "in_progress": ["Build pricing page"],
                "done": ["Ship launch post"],
            },
        )
        self.assertEqual(
            titles(self.project.board(Project.UNASSIGNED)),
            {
                "todo": ["Accessibility review", "Contact form"],
                "in_progress": [],
                "done": ["Final check"],
            },
        )

    def test_unknown_status_is_refused_and_the_task_is_unchanged(self):
        task = self.add_task(status="in_progress")

        with self.assertRaises(TaskStatusError):
            task.set_status("archived")
        task.refresh_from_db()
        self.assertEqual(task.status, "in_progress")

    def test_deleting_a_task_deletes_its_comments(self):
        author = Member.objects.create(name="Nina Patel", email="nina@example.com")
        task = self.add_task()
        kept = self.add_task()
        Comment.objects.create(task=task, author=author, body="First pass is up.")
        Comment.objects.create(task=task, author=author, body="Looks good.")
        Comment.objects.create(task=kept, author=author, body="Still open.")
        task_id = task.pk

        task.delete()

        self.assertFalse(Comment.objects.filter(task_id=task_id).exists())
        self.assertEqual(
            list(Comment.objects.values_list("body", flat=True)), ["Still open."]
        )
