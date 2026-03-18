"""
Agent API URL Routes for PlaneAgent

Maps agent-specific endpoints to views.
"""

from django.urls import path
from plane.api.views import agent

urlpatterns = [
    # Agent Task Discovery
    path(
        'agents/tasks/available/',
        agent.list_available_tasks,
        name='agent-tasks-available'
    ),
    
    # Agent Task Execution
    path(
        'agents/tasks/<uuid:issue_id>/claim/',
        agent.claim_task,
        name='agent-task-claim'
    ),
    path(
        'agents/tasks/<uuid:issue_id>/progress/',
        agent.update_progress,
        name='agent-task-progress'
    ),
    path(
        'agents/tasks/<uuid:issue_id>/complete/',
        agent.complete_task,
        name='agent-task-complete'
    ),
    path(
        'agents/tasks/<uuid:issue_id>/artifacts/',
        agent.upload_artifact,
        name='agent-task-artifact'
    ),
    
    # Human Review
    path(
        'human/review/queue/',
        agent.review_queue,
        name='human-review-queue'
    ),
    path(
        'human/review/<uuid:issue_id>/approve/',
        agent.approve_task,
        name='human-review-approve'
    ),
    path(
        'human/review/<uuid:issue_id>/reject/',
        agent.reject_task,
        name='human-review-reject'
    ),
]
