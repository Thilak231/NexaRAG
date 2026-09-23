from contextvars import ContextVar

_current_user_id = ContextVar(
    "nexarag_user_id",
    default=None
)


def set_current_user(user_id):
    return _current_user_id.set(user_id)


def reset_current_user(token):
    _current_user_id.reset(token)


def get_current_user():
    user_id = _current_user_id.get()

    if not user_id:
        raise RuntimeError(
            "No NexaRAG session was provided."
        )

    return user_id