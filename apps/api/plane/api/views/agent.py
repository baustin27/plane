"""
Agent API Views for PlaneAgent

Provides endpoints for agent-first task management:
- List available (claimable) tasks
- Claim task (atomic locking)
- Update progress
- Mark blocked
- Mark complete with artifacts
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from plane.db.models import Issue, Project
from plane.api.permissions import AgentPermission
from plane.api.serializers import IssueSerializer


@api_view(['GET'])
@permission_classes([AgentPermission])
def list_available_tasks(request, project_id=None):
    """
    List tasks that can be claimed by agents.
    
    Query params:
    - project_id: Filter by project (optional)
    - auto_executable: Only auto-executable tasks (default: true)
    - limit: Max results (default: 50)
    
    Returns: List of claimable issues
    """
    auto_executable = request.query_params.get('auto_executable', 'true').lower() == 'true'
    limit = int(request.query_params.get('limit', 50))
    
    queryset = Issue.issue_objects.filter(
        agent_status='unclaimed',
        draft=False,
        project__archived_at__isnull=True,
    )
    
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    if auto_executable:
        queryset = queryset.filter(auto_executable=True)
    
    queryset = queryset.select_related('project', 'state')[:limit]
    
    serializer = IssueSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AgentPermission])
def claim_task(request, issue_id):
    """
    Atomically claim a task for the requesting agent.
    
    Uses SELECT FOR UPDATE to prevent race conditions.
    
    Body:
    - agent_id: (required) Agent identifier
    - context: (optional) Initial agent context
    
    Returns: Updated issue or error if already claimed
    """
    agent_id = request.data.get('agent_id')
    context = request.data.get('context', {})
    
    if not agent_id:
        return Response(
            {'error': 'agent_id required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            # SELECT FOR UPDATE - locks this row
            issue = Issue.issue_objects.select_for_update().get(
                id=issue_id,
                agent_status='unclaimed'
            )
            
            # Claim it
            issue.assigned_agent = agent_id
            issue.agent_status = 'claimed'
            issue.agent_context = context
            issue.claimed_at = timezone.now()
            issue.save()
            
            serializer = IssueSerializer(issue)
            return Response(serializer.data)
            
    except Issue.DoesNotExist:
        return Response(
            {'error': 'Task not found or already claimed'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AgentPermission])
def update_progress(request, issue_id):
    """
    Update agent progress on a task.
    
    Body:
    - agent_id: (required) Must match assigned_agent
    - status: (optional) 'in_progress', 'blocked', 'completed'
    - progress_message: (optional) Human-readable progress
    - context_update: (optional) Merge into agent_context
    - blocked_reason: (required if status='blocked')
    
    Returns: Updated issue
    """
    agent_id = request.data.get('agent_id')
    new_status = request.data.get('status')
    progress_message = request.data.get('progress_message')
    context_update = request.data.get('context_update', {})
    blocked_reason = request.data.get('blocked_reason')
    
    if not agent_id:
        return Response(
            {'error': 'agent_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        issue = Issue.issue_objects.get(id=issue_id, assigned_agent=agent_id)
    except Issue.DoesNotExist:
        return Response(
            {'error': 'Task not found or not assigned to this agent'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Update status
    if new_status:
        if new_status == 'blocked' and not blocked_reason:
            return Response(
                {'error': 'blocked_reason required when status=blocked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        issue.agent_status = new_status
        if new_status == 'blocked':
            issue.blocked_reason = blocked_reason
        elif new_status == 'in_progress':
            issue.blocked_reason = None
    
    # Merge context
    if context_update:
        issue.agent_context = {**issue.agent_context, **context_update}
    
    # Add progress message to context
    if progress_message:
        history = issue.agent_context.get('progress_history', [])
        history.append({
            'message': progress_message,
            'timestamp': timezone.now().isoformat(),
        })
        issue.agent_context['progress_history'] = history
    
    issue.save()
    
    serializer = IssueSerializer(issue)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AgentPermission])
def complete_task(request, issue_id):
    """
    Mark task as completed with artifacts.
    
    Body:
    - agent_id: (required) Must match assigned_agent
    - artifacts: (required) List of artifacts
        [{type: 'screenshot'|'log'|'file', url: string, description: string}]
    - summary: (optional) Completion summary
    - context_update: (optional) Final context update
    
    Returns: Updated issue (status='completed' or 'in_progress' if review required)
    """
    agent_id = request.data.get('agent_id')
    artifacts = request.data.get('artifacts', [])
    summary = request.data.get('summary')
    context_update = request.data.get('context_update', {})
    
    if not agent_id:
        return Response(
            {'error': 'agent_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        issue = Issue.issue_objects.get(id=issue_id, assigned_agent=agent_id)
    except Issue.DoesNotExist:
        return Response(
            {'error': 'Task not found or not assigned to this agent'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Add artifacts
    issue.artifacts = artifacts
    
    # Add summary
    if summary:
        issue.agent_context['completion_summary'] = summary
    
    # Merge context
    if context_update:
        issue.agent_context = {**issue.agent_context, **context_update}
    
    # Update status
    if issue.human_review_required:
        # Needs review - stay in_progress but flag as completed
        issue.agent_status = 'completed'
    else:
        # Auto-verified
        issue.agent_status = 'verified'
        issue.verified_at = timezone.now()
    
    issue.save()
    
    serializer = IssueSerializer(issue)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AgentPermission])
def upload_artifact(request, issue_id):
    """
    Upload a single artifact to a task.
    
    Body (multipart/form-data):
    - agent_id: (required)
    - file: (required) The artifact file
    - type: (required) 'screenshot', 'log', 'file'
    - description: (optional)
    
    Returns: Updated issue with new artifact
    """
    agent_id = request.data.get('agent_id')
    artifact_type = request.data.get('type')
    description = request.data.get('description', '')
    uploaded_file = request.FILES.get('file')
    
    if not all([agent_id, artifact_type, uploaded_file]):
        return Response(
            {'error': 'agent_id, type, and file required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        issue = Issue.issue_objects.get(id=issue_id, assigned_agent=agent_id)
    except Issue.DoesNotExist:
        return Response(
            {'error': 'Task not found or not assigned to this agent'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # TODO: Upload file to storage (S3, local, etc.)
    # For now, store as base64 in artifacts
    import base64
    file_content = base64.b64encode(uploaded_file.read()).decode('utf-8')
    
    artifact = {
        'type': artifact_type,
        'filename': uploaded_file.name,
        'content_base64': file_content,
        'description': description,
        'uploaded_at': timezone.now().isoformat(),
    }
    
    artifacts = issue.artifacts or []
    artifacts.append(artifact)
    issue.artifacts = artifacts
    issue.save()
    
    return Response({'artifact_id': len(artifacts) - 1})


# Human Review Endpoints

@api_view(['GET'])
@permission_classes([AgentPermission])  # TODO: Create HumanPermission
def review_queue(request, project_id=None):
    """
    List completed tasks awaiting human review.
    """
    queryset = Issue.issue_objects.filter(
        agent_status='completed',
        human_review_required=True,
    )
    
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    queryset = queryset.select_related('project', 'state')
    
    serializer = IssueSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AgentPermission])  # TODO: Create HumanPermission
def approve_task(request, issue_id):
    """
    Approve completed agent work.
    
    Body:
    - feedback: (optional) Approval feedback
    
    Returns: Updated issue (status='verified')
    """
    feedback = request.data.get('feedback')
    
    try:
        issue = Issue.issue_objects.get(
            id=issue_id,
            agent_status='completed',
            human_review_required=True
        )
    except Issue.DoesNotExist:
        return Response(
            {'error': 'Task not found or not awaiting review'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    issue.agent_status = 'verified'
    issue.verified_at = timezone.now()
    issue.verified_by = request.user
    
    if feedback:
        issue.agent_context['review_feedback'] = feedback
    
    issue.save()
    
    serializer = IssueSerializer(issue)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AgentPermission])  # TODO: Create HumanPermission
def reject_task(request, issue_id):
    """
    Reject completed agent work (requires rework).
    
    Body:
    - feedback: (required) What needs to be fixed
    
    Returns: Updated issue (status='in_progress')
    """
    feedback = request.data.get('feedback')
    
    if not feedback:
        return Response(
            {'error': 'feedback required for rejection'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        issue = Issue.issue_objects.get(
            id=issue_id,
            agent_status='completed',
            human_review_required=True
        )
    except Issue.DoesNotExist:
        return Response(
            {'error': 'Task not found or not awaiting review'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    issue.agent_status = 'in_progress'
    issue.agent_context['review_feedback'] = feedback
    issue.agent_context['rejection_count'] = issue.agent_context.get('rejection_count', 0) + 1
    issue.save()
    
    serializer = IssueSerializer(issue)
    return Response(serializer.data)
