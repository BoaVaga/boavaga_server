from unittest.mock import Mock

from tests.utils.singleton_provider import singleton_provider


def disable_email_sender(container):
    container.email_sender.override(singleton_provider(Mock()))
