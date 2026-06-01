from cullinan.core import service


@service
class UserDirectoryService:
    def __init__(self):
        self._users = {
            1: {"id": 1, "name": "Ada", "role": "architect"},
            2: {"id": 2, "name": "Linus", "role": "maintainer"},
        }

    def list_users(self):
        return list(self._users.values())

    def get_user(self, user_id: int):
        return self._users.get(user_id)
