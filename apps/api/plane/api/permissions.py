"""
Permissions for Agent API access
"""

from rest_framework import permissions


class AgentPermission(permissions.BasePermission):
    """
    Allow access to agent-authenticated requests.
    
    For now, allows all (development).
    In production, should check agent tokens.
    """
    
    def has_permission(self, request, view):
        # TODO: Implement proper agent authentication
        # For development, allow all
        return True
    
    def has_object_permission(self, request, view, obj):
        return True
