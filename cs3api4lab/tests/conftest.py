# NOTE: this file was copied from https://github.com/jupyter-server/jupyter_server/blob/main/tests/services/contents
# and adjusted for the plugin use.

import pytest
from nbformat import writes
from nbformat.v4 import new_notebook
from pytest_jupyter.jupyter_server import url_path_join
from ..tests.app import MockExtensionApp

pytest_plugins = ["jupyter_server.pytest_plugin"]

test_resources = [
    ("/Directory with spaces in", "inspace"),
    ("/unicodé", "innonascii"),
    ("/foo", "a"),
    ("/foo", "b"),
    ("/foo", "name with spaces"),
    ("/foo", "unicodé"),
    ("/ordering", "A"),
    ("/ordering", "b"),
    ("/ordering", "C"),
    ("/å b", "ç d"),
]

test_dirs = set([f[0] for f in test_resources])


@pytest.fixture
def contents(file_api, cs3_config):
    paths: dict = {"notebooks": [], "textfiles": [], "blobs": []}
    for d, _ in test_resources:
        try:
            file_api.create_directory(url_path_join(cs3_config.mount_dir, d))
        except OSError as e:
            if 'container already exists' not in e.args:
                raise e
    for d, name in test_resources:
        nb = writes(new_notebook(), version=4)
        nbname = url_path_join(cs3_config.mount_dir, d, f"{name}.ipynb")
        file_api.write_file(nbname, nb)
        paths["notebooks"].append(nbname)

        txt = f"{name} text file".encode('utf-8')
        txtname = url_path_join(cs3_config.mount_dir, d, f"{name}.txt")
        file_api.write_file(txtname, txt)
        paths["textfiles"].append(txtname)

        blob = name.encode("utf-8") + b"\xFF"
        blobname = url_path_join(cs3_config.mount_dir, d, f"{name}.blob")
        file_api.write_file(blobname, blob)
        paths["blobs"].append(blobname)
    paths["all"] = list(paths.values())
    yield paths
    for d in test_dirs:
        try:
            file_api.remove(url_path_join(cs3_config.mount_dir, d))
        except FileNotFoundError:
            # file might have been deleted
            pass


@pytest.fixture
def extension_manager(jp_serverapp):
    return jp_serverapp.extension_manager


@pytest.fixture(autouse=True)
def jp_mockextension_cleanup():
    yield
    MockExtensionApp.clear_instance()

@pytest.fixture
def folders():
    return list({item[0] for item in test_resources})
