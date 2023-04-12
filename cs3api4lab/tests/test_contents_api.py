import pathlib
from base64 import decodebytes, encodebytes
from unicodedata import normalize

from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from traitlets.config import LoggingConfigurable

from nbformat import from_dict
from nbformat.v4 import new_markdown_cell, new_notebook

from .jupyter_server_utils import expected_http_error
from .conftest import test_resources
from pytest_jupyter.jupyter_server import *

# NOTE: this file was copied from https://github.com/jupyter-server/jupyter_server/blob/main/tests/services/contents
# and adjusted for the plugin use.
# The tests of hidden files were skipped, since the plugin allows operations on hidden resources.


@pytest.fixture
def file_api():
    return Cs3FileApi(LoggingConfigurable().log)

@pytest.fixture
def cs3_config():
    return Cs3ConfigManager.get_config()

def notebooks_only(dir_model):
    return [nb for nb in dir_model["content"] if nb["type"] == "notebook"]


def dirs_only(dir_model):
    return [x for x in dir_model["content"] if x["type"] == "directory"]


@pytest.fixture()
def jp_argv():
    return ["--ServerApp.contents_manager_class=cs3api4lab.CS3APIsManager"]


@pytest.mark.parametrize("path,name", test_resources)
async def test_list_notebooks(jp_fetch, contents, path, name):
    response = await jp_fetch(
        "api",
        "contents",
        path,
        method="GET",
    )
    data = json.loads(response.body.decode())
    nbs = notebooks_only(data)
    assert len(nbs) > 0
    assert name + ".ipynb" in [normalize("NFC", n["name"]) for n in nbs]
    assert url_path_join(path, name + ".ipynb") in [normalize("NFC", n["path"]) for n in nbs]


@pytest.mark.parametrize("path,name", test_resources)
async def test_get_dir_no_contents(jp_fetch, contents, path, name):
    response = await jp_fetch(
        "api",
        "contents",
        path,
        method="GET",
        params=dict(
            content="0",
        ),
    )
    model = json.loads(response.body.decode())
    assert model["path"] == path
    assert model["type"] == "directory"
    assert "content" in model
    assert model["content"] is None


async def test_list_nonexistant_dir(jp_fetch, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await jp_fetch(
            "api",
            "contents",
            "nonexistant",
            method="GET",
        )


@pytest.mark.parametrize("path,name", test_resources)
async def test_get_nb_contents(jp_fetch, contents, path, name):
    nbname = name + ".ipynb"
    nbpath = (path + "/" + nbname)
    r = await jp_fetch("api", "contents", nbpath, method="GET", params=dict(content="1"))
    model = json.loads(r.body.decode())
    assert model["name"] == nbname
    assert model["path"] == nbpath
    assert model["type"] == "notebook"
    assert "content" in model
    assert model["format"] == "json"
    assert "metadata" in model["content"]
    assert isinstance(model["content"]["metadata"], dict)


@pytest.mark.parametrize("path,name", test_resources)
async def test_get_nb_no_contents(jp_fetch, contents, path, name):
    nbname = name + ".ipynb"
    nbpath = (path + "/" + nbname)
    r = await jp_fetch("api", "contents", nbpath, method="GET", params=dict(content="0"))
    model = json.loads(r.body.decode())
    assert model["name"] == nbname
    assert model["path"] == nbpath
    assert model["type"] == "notebook"
    assert "content" in model
    assert model["content"] is None


async def test_get_nb_invalid(jp_fetch, contents, file_api):
    nb = {
        "nbformat": 4,
        "metadata": {},
        "cells": [
            {
                "cell_type": "wrong",
                "metadata": {},
            }
        ],
    }
    nbpath = "/Validate tést.ipynb"
    file_api.write_file(nbpath, json.dumps(nb))
    r = await jp_fetch(
        "api",
        "contents",
        nbpath,
        method="GET",
    )
    model = json.loads(r.body.decode())
    assert model["path"] == nbpath
    assert model["type"] == "notebook"
    assert "content" in model
    assert "message" in model
    assert "validation failed" in model["message"].lower()


async def test_get_contents_no_such_file(jp_fetch):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "foo/q.ipynb",
            method="GET",
        )
    assert e.value.code == 404


@pytest.mark.parametrize("path,name", test_resources)
async def test_get_text_file_contents(jp_fetch, contents, path, name, file_api):
    txtname = name + ".txt"
    txtpath = (path + "/" + txtname)
    r = await jp_fetch("api", "contents", txtpath, method="GET", params=dict(content="1"))
    model = json.loads(r.body.decode())
    assert model["name"] == txtname
    assert model["path"] == txtpath
    assert "content" in model
    assert model["format"] == "text"
    assert model["type"] == "file"
    assert model["content"] == f"{name} text file"

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "foo/q.txt",
            method="GET",
        )
    assert expected_http_error(e, 404)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "foo/bar/baz.blob",
            method="GET",
            params=dict(type="file", format="text"),
        )
    assert expected_http_error(e, 400)


async def test_get_text_file_contents_bad_request(jp_fetch):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "foo/bar/baz.blob",
            method="GET",
            params=dict(type="file", format="text"),
        )
    assert expected_http_error(e, 400)


@pytest.mark.skip("plugin allows hidden resources")
async def test_get_404_hidden(jp_fetch, contents, file_api):
    hidden_dir = ".hidden"
    file_api.create_directory(hidden_dir)
    txt = "visible text file in hidden dir"
    txtname = hidden_dir + "/visible.txt"
    file_api.write_file(txtname, txt)

    txt2 = "hidden text file"
    txtname2 = "/.hidden.txt"
    file_api.write_file(txtname2, txt2)
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            ".hidden/visible.txt",
            method="GET",
        )
    assert expected_http_error(e, 404)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            ".hidden.txt",
            method="GET",
        )
    assert expected_http_error(e, 404)


@pytest.mark.parametrize("path,name", test_resources)
async def test_get_binary_file_contents(jp_fetch, contents, path, name):
    blobname = name + ".blob"
    blobpath = (path + "/" + blobname)
    r = await jp_fetch("api", "contents", blobpath, method="GET", params=dict(content="1"))
    model = json.loads(r.body.decode())
    assert model["name"] == blobname
    assert model["path"] == blobpath
    assert "content" in model
    assert model["format"] == "base64"
    assert model["type"] == "file"
    data_out = decodebytes(model["content"].encode("ascii"))
    data_in = name.encode("utf-8") + b"\xFF"
    assert data_in == data_out

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "foo/q.txt",
            method="GET",
        )
    assert expected_http_error(e, 404)


async def test_get_bad_type(jp_fetch, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        path = "/unicodé"
        type = "file"
        await jp_fetch(
            "api",
            "contents",
            path,
            method="GET",
            params=dict(type=type),  # This should be a directory, and thus throw and error
        )
    assert expected_http_error(e, 400, f"{path} is a directory, not a {type}")

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        path = "/unicodé/innonascii.ipynb"
        type = "directory"
        await jp_fetch(
            "api",
            "contents",
            path,
            method="GET",
            params=dict(type=type),  # This should be a file, and thus throw and error
        )
    assert expected_http_error(e, 400, "%s is not a directory" % path)


@pytest.fixture
def _check_created(jp_base_url):
    def _inner(r, contents_dir, path, name, type="notebook"):
        fpath = path + "/" + name
        assert r.code == 201
        location = jp_base_url + "api/contents/" + tornado.escape.url_escape(fpath, plus=False)
        assert r.headers["Location"] == location
        model = json.loads(r.body.decode())
        assert model["name"] == name
        assert model["path"] == fpath
        assert model["type"] == type
        path = contents_dir + "/" + fpath
        if type == "directory":
            assert pathlib.Path(path).is_dir()
        else:
            assert pathlib.Path(path).is_file()

    return _inner


async def test_create_untitled_nb_in_dir(jp_fetch, contents, _check_created, file_api):
    path = "/å b"
    name = "/Untitled.ipynb"
    r = await jp_fetch("api", "contents", path, method="POST", body=json.dumps({"ext": ".ipynb"}))
    assert file_api.stat_info(path + name)


async def test_create_untitled_nb(jp_fetch, contents, _check_created, file_api):
    path = "/"
    name = "/Untitled.ipynb"
    r = await jp_fetch("api", "contents", path, method="POST", body=json.dumps({"ext": ".ipynb"}))
    assert file_api.stat_info(name)


async def test_create_untitled_txt(jp_fetch, contents):
    name = "untitled.txt"
    path = "/foo"
    r = await jp_fetch("api", "contents", path, method="POST", body=json.dumps({"ext": ".txt"}))

    r = await jp_fetch("api", "contents", path, name, method="GET")
    model = json.loads(r.body.decode())
    assert model["type"] == "file"
    assert model["format"] == "text"
    assert model["content"] == ""


async def test_upload_notebook(jp_fetch, contents, _check_created, file_api):
    nb = new_notebook()
    nbmodel = {"content": nb, "type": "notebook"}
    path = "/å b/Upload tést.ipynb"
    r = await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(nbmodel))
    assert file_api.stat_info(path)


async def test_mkdir_untitled(jp_fetch, contents, file_api):
    name = "/Untitled Folder"
    path = "/å b"
    r = await jp_fetch(
        "api", "contents", path, method="POST", body=json.dumps({"type": "directory"})
    )
    assert file_api.stat_info(path + name)

    name = "/Untitled Folder 1"
    r = await jp_fetch(
        "api", "contents", path, method="POST", body=json.dumps({"type": "directory"})
    )
    assert file_api.stat_info(path + name)

    name = "/Untitled Folder"
    path = "/foo"
    r = await jp_fetch(
        "api", "contents", path, method="POST", body=json.dumps({"type": "directory"})
    )
    assert file_api.stat_info(path + name)


async def test_mkdir(jp_fetch, contents, file_api):
    name = "/New ∂ir"
    path = "/å b"
    r = await jp_fetch(
        "api",
        "contents",
        path,
        name,
        method="PUT",
        body=json.dumps({"type": "directory"}),
    )
    assert file_api.stat_info(path + name)


@pytest.mark.skip("plugin allows hidden files")
async def test_mkdir_hidden_400(jp_fetch):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "å b/.hidden",
            method="PUT",
            body=json.dumps({"type": "directory"}),
        )
    assert expected_http_error(e, 400)


async def test_upload_txt(jp_fetch, contents, _check_created):
    body = "ünicode téxt"
    model = {
        "content": body,
        "format": "text",
        "type": "file",
    }
    name = "Uploåd tést.txt"
    await jp_fetch("api", "contents", name, method="PUT", body=json.dumps(model))

    # check roundtrip
    r = await jp_fetch("api", "contents", name, method="GET")
    model = json.loads(r.body.decode())
    assert model["type"] == "file"
    assert model["format"] == "text"
    assert model["path"] == "/" + name
    assert model["content"] == body


@pytest.mark.skip("plugin allows hidden resources")
async def test_upload_txt_hidden(jp_fetch, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        body = "ünicode téxt"
        model = {
            "content": body,
            "format": "text",
            "type": "file",
        }
        path = ".hidden/Upload tést.txt"
        await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(model))
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        body = "ünicode téxt"
        model = {"content": body, "format": "text", "type": "file", "path": ".hidden/test.txt"}
        path = "Upload tést.txt"
        await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(model))
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        body = "ünicode téxt"
        model = {
            "content": body,
            "format": "text",
            "type": "file",
        }
        path = ".hidden.txt"
        await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(model))
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        body = "ünicode téxt"
        model = {"content": body, "format": "text", "type": "file", "path": ".hidden.txt"}
        path = "Upload tést.txt"
        await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(model))
    assert expected_http_error(e, 400)


async def test_upload_b64(jp_fetch, contents):
    body = b"\xFFblob"
    b64body = encodebytes(body).decode("ascii")
    model = {
        "content": b64body,
        "format": "base64",
        "type": "file",
    }
    path = "/å b"
    name = "Upload tést.blob"
    await jp_fetch("api", "contents", path, name, method="PUT", body=json.dumps(model))
    r = await jp_fetch("api", "contents", path, name, method="GET")
    model = json.loads(r.body.decode())
    assert model["type"] == "file"
    assert model["path"] == path + "/" + name
    assert model["format"] == "base64"
    decoded = decodebytes(model["content"].encode("ascii"))
    assert decoded == body


async def test_copy(jp_fetch, file_api, contents):
    path = "/å b"
    name = "ç d.ipynb"
    original_file_path = path + "/" + name
    copy = "ç d-Copy1.ipynb"
    copy_file_path = path + "/" + copy
    r = await jp_fetch(
        "api",
        "contents",
        path,
        method="POST",
        body=json.dumps({"copy_from": original_file_path}),
    )
    assert file_api.stat_info(copy_file_path)

    copy2 = "ç d-Copy2.ipynb"
    copy2_file_path = path + "/" + copy2
    r = await jp_fetch(
        "api",
        "contents",
        path,
        method="POST",
        body=json.dumps({"copy_from": original_file_path}),
    )
    assert file_api.stat_info(copy2_file_path)


async def test_copy_path(jp_fetch, contents, file_api):
    path1 = "/foo"
    path2 = "/å b"
    name = "a.ipynb"
    copy = "a-Copy1.ipynb"
    r = await jp_fetch(
        "api",
        "contents",
        path2,
        method="POST",
        body=json.dumps({"copy_from": path1 + "/" + name}),
    )
    file_api.stat_info(path2 + "/" + name)

    r = await jp_fetch(
        "api",
        "contents",
        path2,
        method="POST",
        body=json.dumps({"copy_from": path1 + "/" + name}),
    )
    file_api.stat_info(path2 + "/" + copy)


async def test_copy_put_400(jp_fetch, contents, _check_created):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "å b/cøpy.ipynb",
            method="PUT",
            body=json.dumps({"copy_from": "å b/ç d.ipynb"}),
        )
    assert expected_http_error(e, 400)


async def test_copy_put_400_hidden(
        jp_fetch,
        contents,
):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            ".hidden/old.txt",
            method="PUT",
            body=json.dumps({"copy_from": "new.txt"}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "old.txt",
            method="PUT",
            body=json.dumps({"copy_from": ".hidden/new.txt"}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            ".hidden.txt",
            method="PUT",
            body=json.dumps({"copy_from": "new.txt"}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "old.txt",
            method="PUT",
            body=json.dumps({"copy_from": ".hidden.txt"}),
        )
    assert expected_http_error(e, 400)


async def test_copy_dir_400(jp_fetch, contents, _check_created):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "foo",
            method="POST",
            body=json.dumps({"copy_from": "å b"}),
        )
    assert expected_http_error(e, 400)


@pytest.mark.skip("plugin allows hidden resources")
async def test_copy_400_hidden(
        jp_fetch,
        contents,
        file_api
):
    hidden_dir = "/.hidden"
    file_api.create_directory(hidden_dir)
    txt = "visible text file in hidden dir"
    txtname = hidden_dir + "/new.txt"
    file_api.write_file(txtname, txt)

    paths = ["new.txt", ".hidden.txt"]
    for name in paths:
        txt = f"{name} text file"
        txtname = contents_dir.joinpath(f"{name}.txt")
        file_api.write_file(txtname, txt)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            ".hidden/old.txt",
            method="POST",
            body=json.dumps({"copy_from": "new.txt"}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "old.txt",
            method="POST",
            body=json.dumps({"copy_from": ".hidden/new.txt"}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            ".hidden.txt",
            method="POST",
            body=json.dumps({"copy_from": "new.txt"}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch(
            "api",
            "contents",
            "old.txt",
            method="POST",
            body=json.dumps({"copy_from": ".hidden.txt"}),
        )
    assert expected_http_error(e, 400)


@pytest.mark.parametrize("path,name", test_resources)
async def test_delete(jp_fetch, contents, path, name, _check_created):
    nbname = name + ".ipynb"
    nbpath = (path + "/" + nbname)
    r = await jp_fetch(
        "api",
        "contents",
        nbpath,
        method="DELETE",
    )
    assert r.code == 204


async def test_delete_dirs(jp_fetch, contents, folders):
    for name in sorted(["/"], key=len, reverse=True):
        r = await jp_fetch("api", "contents", name, method="GET")
        listing = json.loads(r.body.decode())["content"]
        for model in listing:
            if "MyShares" in model["path"]:
                continue
            await jp_fetch("api", "contents", model["path"], method="DELETE")
    r = await jp_fetch("api", "contents", method="GET")
    model = json.loads(r.body.decode())
    assert len(model['content']) == 1
    assert model['content'][0]['name'] == 'MyShares'


async def test_delete_non_empty_dir(jp_fetch, contents):
    path = "/å b"
    await jp_fetch("api", "contents", path, method="DELETE")
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch("api", "contents", "/å b", method="GET")
    assert expected_http_error(e, 404)


@pytest.mark.skip("plugin allows hidden resources")
async def test_delete_hidden_dir(jp_fetch, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch("api", "contents", ".hidden", method="DELETE")
    assert expected_http_error(e, 400)


@pytest.mark.skip("plugin allows hidden resources")
async def test_delete_hidden_file(jp_fetch, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch("api", "contents", ".hidden/test.txt", method="DELETE")
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch("api", "contents", ".hidden.txt", method="DELETE")
    assert expected_http_error(e, 400)


async def test_rename(jp_fetch, jp_base_url, contents):
    path = "/foo"
    name = "a.ipynb"
    new_name = "z.ipynb"
    new_path = path + "/" + new_name
    r = await jp_fetch(
        "api",
        "contents",
        path,
        name,
        method="PATCH",
        body=json.dumps({"path": new_path}),
    )
    assert r.code == 200
    location = url_path_join(jp_base_url, "api/contents", new_path)
    assert r.headers["Location"] == location
    model = json.loads(r.body.decode())
    assert model["name"] == new_name
    assert model["path"] == new_path

    r = await jp_fetch("api", "contents", path, method="GET")
    listing = json.loads(r.body.decode())
    nbnames = [name["name"] for name in listing["content"]]
    assert "z.ipynb" in nbnames
    assert "a.ipynb" not in nbnames


@pytest.mark.skip("plugin allows hidden resources")
async def test_rename_400_hidden(jp_fetch, jp_base_url, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        old_path = ".hidden/old.txt"
        new_path = "new.txt"
        # Rename the file
        r = await jp_fetch(
            "api",
            "contents",
            old_path,
            method="PATCH",
            body=json.dumps({"path": new_path}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        old_path = "old.txt"
        new_path = ".hidden/new.txt"
        # Rename the file
        r = await jp_fetch(
            "api",
            "contents",
            old_path,
            method="PATCH",
            body=json.dumps({"path": new_path}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        old_path = ".hidden.txt"
        new_path = "new.txt"
        # Rename the file
        r = await jp_fetch(
            "api",
            "contents",
            old_path,
            method="PATCH",
            body=json.dumps({"path": new_path}),
        )
    assert expected_http_error(e, 400)

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        old_path = "old.txt"
        new_path = ".hidden.txt"
        # Rename the file
        r = await jp_fetch(
            "api",
            "contents",
            old_path,
            method="PATCH",
            body=json.dumps({"path": new_path}),
        )
    assert expected_http_error(e, 400)


@pytest.mark.skip("todo implement checkpoints")
async def test_checkpoints_follow_file(jp_fetch, contents):
    path = "foo"
    name = "a.ipynb"

    # Read initial file.
    r = await jp_fetch("api", "contents", path, name, method="GET")
    model = json.loads(r.body.decode())

    # Create a checkpoint of initial state
    r = await jp_fetch(
        "api",
        "contents",
        path,
        name,
        "checkpoints",
        method="POST",
        allow_nonstandard_methods=True,
    )
    cp1 = json.loads(r.body.decode())

    # Modify file and save.
    nbcontent = model["content"]
    nb = from_dict(nbcontent)
    hcell = new_markdown_cell("Created by test")
    nb.cells.append(hcell)
    nbmodel = {"content": nb, "type": "notebook"}
    await jp_fetch("api", "contents", path, name, method="PUT", body=json.dumps(nbmodel))

    # List checkpoints
    r = await jp_fetch(
        "api",
        "contents",
        path,
        name,
        "checkpoints",
        method="GET",
    )
    cps = json.loads(r.body.decode())
    assert cps == [cp1]

    r = await jp_fetch("api", "contents", path, name, method="GET")
    model = json.loads(r.body.decode())
    nbcontent = model["content"]
    nb = from_dict(nbcontent)
    assert nb.cells[0].source == "Created by test"


async def test_rename_existing(jp_fetch, contents):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        path = "foo"
        name = "a.ipynb"
        new_name = "b.ipynb"
        # Rename the file
        await jp_fetch(
            "api",
            "contents",
            path,
            name,
            method="PATCH",
            body=json.dumps({"path": path + "/" + new_name}),
        )
    assert expected_http_error(e, 409)


async def test_save_notebook(jp_fetch, contents):
    r = await jp_fetch("api", "contents", "foo/a.ipynb", method="GET")
    model = json.loads(r.body.decode())
    nbmodel = model["content"]
    nb = from_dict(nbmodel)
    nb.cells.append(new_markdown_cell("Created by test ³"))
    nbmodel = {"content": nb, "type": "notebook", "format": ""}
    await jp_fetch("api", "contents", "foo/a.ipynb", method="PUT", body=json.dumps(nbmodel))
    # Round trip.
    r = await jp_fetch("api", "contents", "foo/a.ipynb", method="GET")
    model = json.loads(r.body.decode())
    newnb = from_dict(model["content"])
    assert newnb.cells[0].source == "Created by test ³"


@pytest.mark.skip("todo implement checkpoints")
async def test_checkpoints(jp_fetch, contents):
    path = "foo/a.ipynb"
    resp = await jp_fetch("api", "contents", path, method="GET")
    model = json.loads(resp.body.decode())
    r = await jp_fetch(
        "api",
        "contents",
        path,
        "checkpoints",
        method="POST",
        allow_nonstandard_methods=True,
    )
    assert r.code == 201
    cp1 = json.loads(r.body.decode())
    assert set(cp1) == {"id", "last_modified"}
    assert r.headers["Location"].split("/")[-1] == cp1["id"]

    # Modify it.
    nbcontent = model["content"]
    nb = from_dict(nbcontent)
    hcell = new_markdown_cell("Created by test")
    nb.cells.append(hcell)

    # Save it.
    nbmodel = {"content": nb, "type": "notebook"}
    await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(nbmodel))

    # List checkpoints
    r = await jp_fetch("api", "contents", path, "checkpoints", method="GET")
    cps = json.loads(r.body.decode())
    assert cps == [cp1]

    r = await jp_fetch("api", "contents", path, method="GET")
    nbcontent = json.loads(r.body.decode())["content"]
    nb = from_dict(nbcontent)
    assert nb.cells[0].source == "Created by test"

    # Restore Checkpoint cp1
    r = await jp_fetch(
        "api",
        "contents",
        path,
        "checkpoints",
        cp1["id"],
        method="POST",
        allow_nonstandard_methods=True,
    )
    assert r.code == 204

    r = await jp_fetch("api", "contents", path, method="GET")
    nbcontent = json.loads(r.body.decode())["content"]
    nb = from_dict(nbcontent)
    assert nb.cells == []

    # Delete cp1
    r = await jp_fetch("api", "contents", path, "checkpoints", cp1["id"], method="DELETE")
    assert r.code == 204

    r = await jp_fetch("api", "contents", path, "checkpoints", method="GET")
    cps = json.loads(r.body.decode())
    assert cps == []


@pytest.mark.skip("todo implement checkpoints")
async def test_file_checkpoints(jp_fetch, contents):
    path = "foo/a.txt"
    resp = await jp_fetch("api", "contents", path, method="GET")
    orig_content = json.loads(resp.body.decode())["content"]
    r = await jp_fetch(
        "api",
        "contents",
        path,
        "checkpoints",
        method="POST",
        allow_nonstandard_methods=True,
    )
    assert r.code == 201
    cp1 = json.loads(r.body.decode())
    assert set(cp1) == {"id", "last_modified"}
    assert r.headers["Location"].split("/")[-1] == cp1["id"]

    # Modify it.
    new_content = orig_content + "\nsecond line"
    model = {
        "content": new_content,
        "type": "file",
        "format": "text",
    }

    # Save it.
    await jp_fetch("api", "contents", path, method="PUT", body=json.dumps(model))

    # List checkpoints
    r = await jp_fetch("api", "contents", path, "checkpoints", method="GET")
    cps = json.loads(r.body.decode())
    assert cps == [cp1]

    r = await jp_fetch("api", "contents", path, method="GET")
    content = json.loads(r.body.decode())["content"]
    assert content == new_content

    # Restore Checkpoint cp1
    r = await jp_fetch(
        "api",
        "contents",
        path,
        "checkpoints",
        cp1["id"],
        method="POST",
        allow_nonstandard_methods=True,
    )
    assert r.code == 204

    r = await jp_fetch("api", "contents", path, method="GET")
    restored_content = json.loads(r.body.decode())["content"]
    assert restored_content == orig_content

    # Delete cp1
    r = await jp_fetch("api", "contents", path, "checkpoints", cp1["id"], method="DELETE")
    assert r.code == 204

    r = await jp_fetch("api", "contents", path, "checkpoints", method="GET")
    cps = json.loads(r.body.decode())
    assert cps == []


async def test_trust(jp_fetch, contents):
    # It should be able to trust a notebook that exists
    for path in contents["notebooks"]:
        r = await jp_fetch(
            "api",
            "contents",
            str(path),
            "trust",
            method="POST",
            allow_nonstandard_methods=True,
        )
        assert r.code == 201
