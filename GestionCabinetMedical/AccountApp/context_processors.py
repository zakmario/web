from .utils import get_role


def user_role(request):
    return {'user_role': get_role(request.user)}
