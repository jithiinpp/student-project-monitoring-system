from projects.models import ProjectProposal

def unread_proposals(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        if getattr(request.user, 'role', None) == 'COORDINATOR':
            count = ProjectProposal.objects.filter(status='SUBMITTED').count()
            return {'unread_proposal_count': count}
    return {}
