import logging


def disabled(func):
    """
    Decorator to mark a function as disabled or blocked.

    When a function is decorated with @disabled, it will not be executed
    when called. Instead, it will return a constant value indicating that
    the function is disabled.

    Args:
        func: The function to be decorated.

    Returns:
        A wrapper function that always returns the disabled value.
    """

    def wrapper(*args, **kwargs):
        disabled_value = "Function is disabled"
        logging.warning(f"Function '{func.__name__}' is disabled and will not be executed.")
        return disabled_value

    return wrapper
