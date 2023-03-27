class State:
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    INVALID = 'invalid'
    
    @staticmethod
    def states():
        return [State.PENDING, State.ACCEPTED, State.REJECTED, State.INVALID]


class Role:
    VIEWER = 'viewer'
    EDITOR = 'editor'

    @staticmethod
    def roles():
        return [Role.VIEWER, Role.EDITOR]


class Grantee:
    USER = 'user'
    GROUP = 'group'

    @staticmethod
    def grantee_types():
        return [Grantee.USER, Grantee.GROUP]

