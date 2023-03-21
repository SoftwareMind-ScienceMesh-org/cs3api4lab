from enum import Enum


class State(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    INVALID = 'invalid'


class Role(Enum):
    VIEWER = 'viewer'
    EDITOR = 'editor'


class Grantee(Enum):
    USER = 'user'
    GROUP = 'group'
