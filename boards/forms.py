from django import forms

from .models import Comment, Member, Project, Task


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class TaskForm(forms.ModelForm):
    assignee = forms.ModelChoiceField(
        queryset=Member.objects.all(), required=False, empty_label="Unassigned"
    )

    class Meta:
        model = Task
        fields = ["title", "description", "status", "assignee", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class CommentForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        queryset=Member.objects.all(), empty_label="Choose a member"
    )

    class Meta:
        model = Comment
        fields = ["author", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["name", "email"]
