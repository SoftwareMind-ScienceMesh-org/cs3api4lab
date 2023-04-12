# NOTE: this file was copied from https://github.com/jupyter-server/jupyter_server/blob/main/tests/services/contents
# and adjusted for the plugin use.

from traitlets import List, Unicode
from jupyter_server.extension.application import ExtensionApp


def _jupyter_server_extension_points():
    return [{"module": __name__, "app": MockExtensionApp}]


class MockExtensionApp(ExtensionApp):

    name = "mockextension"
    template_paths = List().tag(config=True)
    mock_trait = Unicode("mock trait", config=True)
    loaded = False

    serverapp_config = {"jpserver_extensions": {"tests.extension.mockextensions.mock1": True}}

    @staticmethod
    def get_extension_package():
        return "tests.extension.mockextensions"


if __name__ == "__main__":
    MockExtensionApp.launch_instance()
