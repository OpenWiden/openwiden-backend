from openwiden.users import models as users_models, services as users_services
from openwiden.exceptions import ServiceException
from . import services, models, messages, enums


def add_repository(repository: models.Repository, user: users_models.User):
    try:
        services.add_repository(repository=repository, user=user)
    except ServiceException as e:
        services.update_repository_state(
            repository=repository, state=enums.RepositoryState.ADD_FAILED,
        )
        users_services.send_notification(user=user, message=e)
    else:
        message = users_services.RepositoryMessage(
            message=messages.REPOSITORY_IS_ADDED.format(name=repository.name),
            repository_id=str(repository.id),
            state=enums.RepositoryState.ADDED,
        )
        users_services.send_notification(user=user, message=message)


def remove_repository(repository: models.Repository, user: users_models.User):
    try:
        services.remove_repository(repository=repository, user=user)
    except ServiceException as e:
        services.update_repository_state(
            repository=repository, state=enums.RepositoryState.REMOVE_FAILED,
        )
        users_services.send_notification(user=user, message=e)
    else:
        message = users_services.RepositoryMessage(
            message=messages.REPOSITORY_IS_REMOVED.format(name=repository.name),
            repository_id=str(repository.id),
            state=enums.RepositoryState.REMOVED,
        )
        users_services.send_notification(user=user, message=message)
