"""Replaces everything in the database with the sample team below. Due dates
and comment times are relative to now, so the board always has work due
soon and recent comments."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from boards.models import Comment, Member, Project, Task

SAMPLE_MEMBERS = [
    ("Nina Patel", "nina.patel@example.com"),
    ("Omar Haddad", "omar.haddad@example.com"),
    ("Lena Fischer", "lena.fischer@example.com"),
    ("Jamal Carter", "jamal.carter@example.com"),
    ("Yuki Tanaka", "yuki.tanaka@example.com"),
]

SAMPLE_PROJECTS = [
    ("Website relaunch", "New marketing site with the refreshed brand."),
    ("Mobile app", "Native iOS and Android app for our customers."),
    ("Customer onboarding", "Make the first week smoother for new customers."),
]

# (project, title, status, assignee, due in days from today, description);
# project and assignee are 1-based positions in the lists above.
SAMPLE_TASKS = [
    (1, "Write homepage copy", "done", 3, -10, "Headline, three benefit blocks and a closing call to action."),
    (1, "Design logo variations", "done", 5, -14, ""),
    (1, "Build pricing page", "in_progress", 2, 3, "Three plans with a monthly price each."),
    (1, "Migrate blog posts", "todo", 2, 12, "Move the 40 posts from the old site, keeping their URLs."),
    (1, "Choose hosting provider", "done", 4, -20, ""),
    (1, "Accessibility review", "todo", None, 15, "Check contrast, headings and keyboard navigation on every page."),
    (1, "Update product screenshots", "in_progress", 5, 5, ""),
    (1, "Redirect old URLs", "todo", 4, 18, ""),
    (1, "Contact form", "todo", None, None, "Name, email and message, sent to the support inbox."),
    (2, "Login screen design", "done", 5, -7, ""),
    (2, "Push notification settings", "in_progress", 2, 6, "Let people choose which notifications they get."),
    (2, "Offline mode for task list", "todo", 2, 25, ""),
    (2, "App store screenshots", "todo", 5, 20, ""),
    (2, "Crash reporting setup", "done", 4, -3, ""),
    (2, "Beta tester sign-up form", "in_progress", 1, 2, "Collect name, email and device type."),
    (2, "Dark mode", "todo", None, None, ""),
    (2, "Release checklist", "todo", 1, 30, ""),
    (3, "Welcome email sequence", "in_progress", 3, 4, "Three emails over the first week."),
    (3, "Product tour", "todo", 5, 10, ""),
    (3, "Help center articles", "in_progress", 3, 8, "Ten short articles for the most common questions."),
    (3, "Kickoff call template", "done", 1, -5, ""),
    (3, "Sample data for new accounts", "todo", 4, 14, ""),
    (3, "Onboarding survey", "todo", None, None, ""),
    (3, "Measure time to first project", "done", 1, -2, ""),
]

# (task, author, hours ago, body); task and author are 1-based positions.
SAMPLE_COMMENTS = [
    (1, 1, 300, "Approved, thanks!"),
    (3, 2, 30, "First pass is up on the preview site."),
    (3, 1, 26, "Looks good. Can we add a yearly plan toggle?"),
    (3, 2, 4, "Toggle added."),
    (7, 5, 50, "Waiting on the final dashboard design before I capture these."),
    (11, 2, 20, "iOS is done, Android next."),
    (11, 4, 18, "Remember the quiet-hours setting from the survey."),
    (14, 4, 80, "Errors now show up in the dashboard."),
    (15, 1, 72, "Draft form shared with the team."),
    (15, 3, 70, "Should we ask for device type?"),
    (15, 1, 3, "Added device type."),
    (18, 3, 48, "Three emails: welcome, first project, invite your team."),
    (18, 1, 40, "Let's send the second one on day 2, not day 3."),
    (20, 3, 10, "Eight articles drafted, two to go."),
]


class Command(BaseCommand):
    help = "Replaces everything in the database with a sample team."

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()

        models = (Comment, Task, Project, Member)
        for model in models:
            model.objects.all().delete()
        tables = [model._meta.db_table for model in models]
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM sqlite_sequence WHERE name IN (%s, %s, %s, %s)", tables
            )

        members = [
            Member.objects.create(name=name, email=email)
            for name, email in SAMPLE_MEMBERS
        ]
        projects = [
            Project.objects.create(name=name, description=description)
            for name, description in SAMPLE_PROJECTS
        ]
        tasks = [
            Task.objects.create(
                project=projects[project - 1],
                title=title,
                status=status,
                assignee=members[assignee - 1] if assignee else None,
                due_date=today + timedelta(days=due) if due is not None else None,
                description=description,
            )
            for project, title, status, assignee, due, description in SAMPLE_TASKS
        ]
        for task, author, hours_ago, body in SAMPLE_COMMENTS:
            Comment.objects.create(
                task=tasks[task - 1],
                author=members[author - 1],
                body=body,
                created_at=now - timedelta(hours=hours_ago),
            )

        self.stdout.write(
            f"Seeded {len(SAMPLE_MEMBERS)} members, {len(SAMPLE_PROJECTS)} projects, "
            f"{len(SAMPLE_TASKS)} tasks and {len(SAMPLE_COMMENTS)} comments."
        )
