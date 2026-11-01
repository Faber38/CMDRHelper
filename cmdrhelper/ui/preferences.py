"""Noncritical view preferences use QSettings' existing write buffer."""


def set_preference(settings, key, value):
    """Avoid dirtying unchanged values; normal exit verifies the final sync.

    QSettings flushes pending values through its event loop. Do not use this
    helper for inventory evidence or actions requiring durable confirmation.
    """
    if settings.value(key) != value:
        settings.setValue(key, value)
