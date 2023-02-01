from unittest import TestCase
from tornado import web
from cs3api4lab.api.cs3apismanager import CS3APIsManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from traitlets.config import LoggingConfigurable
import posixpath


class TestCS3APIsManager(TestCase):
    user_id = None
    endpoint = None
    file_api = None
    contents_manager = None

    def setUp(self):
        self.log = LoggingConfigurable().log
        self.config = Cs3ConfigManager.get_config()
        self.user_id = self.config.client_id
        self.endpoint = self.config.endpoint
        self.file_api = Cs3FileApi(self.log)
        self.contents_manager = CS3APIsManager(None, self.log)

    def test_get_text_file(self):
        file_path = posixpath.join(self.config.mount_dir, "test_get_text_file.txt")
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.file_api.write_file(file_path, message, self.endpoint)
            model = self.contents_manager.get(file_path, True, 'file')
            self.assertEqual(model["name"], "test_get_text_file.txt")
            self.assertEqual(model["path"], file_path)
            self.assertEqual(model["content"], message)
            self.assertEqual(model["format"], "text")
            self.assertEqual(model["mimetype"], "text/plain")
            self.assertEqual(model["size"], 29)
            self.assertEqual(model["writable"], True)
            self.assertEqual(model["type"], "file")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    def test_get_text_file_without_type(self):
        file_path = posixpath.join(self.config.mount_dir, "test_get_text_file_no_type.txt")
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.file_api.write_file(file_path, message, self.endpoint)
            model = self.contents_manager.get(file_path, True, None)
            self.assertEqual(model["name"], "test_get_text_file_no_type.txt")
            self.assertEqual(model["path"], file_path)
            self.assertEqual(model["content"], message)
            self.assertEqual(model["format"], "text")
            self.assertEqual(model["mimetype"], "text/plain")
            self.assertEqual(model["size"], 29)
            self.assertEqual(model["writable"], True)
            self.assertEqual(model["type"], "file")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    # todo check
    def test_get_file_with_drive_name_starting_with_slash(self):
        file_path = "/cs3drive:test_get_text_file.txt"
        file_id = "/test_get_text_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.file_api.write_file(file_id, message, self.endpoint)
            model = self.contents_manager.get(file_path, True, 'file')
            self.assertEqual(model["name"], "test_get_text_file.txt")
        finally:
            self.file_api.remove(file_id, self.endpoint)

    # todo check
    def test_get_file_with_drive_name(self):
        file_path = "cs3drive:test_get_text_file.txt"
        file_id = "/test_get_text_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.file_api.write_file(file_id, message, self.endpoint)
            model = self.contents_manager.get(file_path, True, 'file')
            self.assertEqual(model["name"], "test_get_text_file.txt")
        finally:
            self.file_api.remove(file_id, self.endpoint)

    def test_get_file_with_drive_name_starting_with_slash(self):
        file_path = "/cs3drive:test_get_text_file.txt"
        file_id = "/test_get_text_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        self.file_api.write_file(file_id, message, self.endpoint)

        model = self.contents_manager.get(file_path, True, 'file')
        self.assertEqual(model["name"], "test_get_text_file.txt")

        self.file_api.remove(file_id, self.endpoint)

    def test_get_text_file_with_share_path(self):
        file_path = posixpath.join(self.config.mount_dir, "test_get_text_file.txt")
        share_file_id = "/reva/einstein/test_get_text_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.file_api.write_file(file_path, message, self.endpoint)
            model = self.contents_manager.get(share_file_id, True, 'file')
            self.assertEqual(model["name"], "test_get_text_file.txt")
            self.assertEqual(model["path"], share_file_id)
            self.assertEqual(model["content"], message)
            self.assertEqual(model["format"], "text")
            self.assertEqual(model["mimetype"], "text/plain")
            self.assertEqual(model["size"], 29)
            self.assertEqual(model["writable"], True)
            self.assertEqual(model["type"], "file")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    def test_get_notebook_file(self):
        file_path = posixpath.join(self.config.mount_dir, "test_get_notebook_file.ipynb")
        buffer = b'{\
					"cells": [\
						{\
							"cell_type": "markdown",\
							"metadata": {},\
							"source": [\
								"### Markdown example"\
							]\
						}\
					],\
					"metadata": {\
						"kernelspec": {\
							"display_name": "Python 3",\
							"language": "python",\
							"name": "python3"\
						},\
						"language_info": {\
							"codemirror_mode": {\
								"name": "ipython",\
								"version": 3\
							},\
							"file_extension": ".py",\
							"mimetype": "text/x-python",\
							"name": "python",\
							"nbconvert_exporter": "python",\
							"pygments_lexer": "ipython3",\
							"version": "3.7.4"\
						}\
					},\
					"nbformat": 4,\
					"nbformat_minor": 4\
					}'

        try:
            self.file_api.write_file(file_path, buffer, self.endpoint)
            model = self.contents_manager.get(file_path, True, "notebook")
            self.assertEqual(model["name"], "test_get_notebook_file.ipynb")
            self.assertEqual(model["path"], file_path)
            self.assertTrue("### Markdown example" in str(model["content"]))
            self.assertEqual(model["format"], "json")
            self.assertEqual(model["mimetype"], None)
            self.assertEqual(model["size"], 637)
            self.assertEqual(model["writable"], True)
            self.assertEqual(model["type"], "notebook")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    def test_save_text_model(self):
        file_path = posixpath.join(self.config.mount_dir, "test_save_text_model.txt")
        model = {
            "type": "file",
            "format": "text",
            "content": "Test content",
        }
        try:
            save_model = self.contents_manager.save(model, file_path)
            self.assertEqual(save_model["name"], "test_save_text_model.txt")
            self.assertEqual(save_model["path"], file_path)
            self.assertEqual(save_model["content"], None)
            self.assertEqual(save_model["format"], None)
            self.assertEqual(save_model["mimetype"], "text/plain")
            self.assertEqual(save_model["size"], 12)
            self.assertEqual(save_model["writable"], True)
            self.assertEqual(save_model["type"], "file")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    def test_save_notebook_model(self):
        file_id = posixpath.join(self.config.mount_dir, "test_save_notebook_model.ipynb")
        model = self._create_notebook_model()
        try:
            save_model = self.contents_manager.save(model, file_id)
            self.assertEqual(save_model["name"], "test_save_notebook_model.ipynb")
            self.assertEqual(save_model["path"], file_id)
            self.assertEqual(save_model["content"], None)
            self.assertEqual(save_model["format"], None)
            self.assertEqual(save_model["mimetype"], None)
            self.assertEqual(save_model["size"], 521)
            self.assertEqual(save_model["writable"], True)
            self.assertEqual(save_model["type"], "notebook")
        finally:
            self.file_api.remove(file_id, self.endpoint)

    def _create_notebook_model(self):
        model = {
            "type": "notebook",
            "format": None,
            "content": {
                "nbformat": 4,
                "cells": [
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": [
                            "### Markdown example"
                        ]
                    }
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    },
                    "language_info": {
                        "codemirror_mode": {
                            "name": "ipython",
                            "version": 3
                        },
                        "file_extension": ".py",
                        "mimetype": "text/x-python",
                        "name": "python",
                        "nbconvert_exporter": "python",
                        "pygments_lexer": "ipython3",
                        "version": "3.7.4"
                    }
                },
            },
        }
        return model

    def test_delete_file(self):
        file_path = posixpath.join(self.config.mount_dir, "test_delete_exits_file.txt")
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.file_api.write_file(file_path, message, self.endpoint)
            self.contents_manager.delete_file(file_path)
            with self.assertRaises(IOError):
                self.file_api.stat_info(file_path, self.endpoint)
        finally:
            try:
                self.contents_manager.delete_file(file_path)
            except: pass

    def test_delete_non_exits_file(self):
        file_path = posixpath.join(self.config.mount_dir, "test_delete_non_exits_file.txt")
        with self.assertRaises(web.HTTPError):
            self.contents_manager.delete_file(file_path)

    def test_rename_file(self):
        file_path = posixpath.join(self.config.mount_dir, "test_rename_file.txt")
        message = "Lorem ipsum dolor sit amet..."
        file_dest = posixpath.join(self.config.mount_dir, "test_after_rename_file.txt")
        try:
            self.file_api.write_file(file_path, message, self.endpoint)
            self.contents_manager.rename_file(file_path, file_dest)
            stat_info = self.file_api.stat_info(file_dest, self.endpoint)
            self.assertIsInstance(stat_info, dict)
            with self.assertRaises(IOError):
                self.file_api.stat_info(file_path, self.endpoint)
        finally:
            try:
                self.file_api.remove(file_dest, self.endpoint)
            except: pass
            try:
                self.file_api.remove(file_path, self.endpoint)
            except: pass

    def test_rename_file_non_exits_file(self):
        file_path = posixpath.join(self.config.mount_dir, "test_rename_file.txt")
        file_dest = posixpath.join(self.config.mount_dir, "test_after_rename_file.txt")

        with self.assertRaises(web.HTTPError):
            self.contents_manager.rename_file(file_path, file_dest)

    def test_rename_file_already_exits(self):
        try:
            file_path = posixpath.join(self.config.mount_dir, "test_rename_file.txt")
            file_dest = posixpath.join(self.config.mount_dir, "test_after_rename_file.txt")
            message = "Lorem ipsum dolor sit amet..."

            self.file_api.write_file(file_path, message, self.endpoint)
            self.file_api.write_file(file_dest, message, self.endpoint)

            with self.assertRaises(web.HTTPError) as context:
                self.contents_manager.rename_file(file_path, file_dest)
            self.assertEqual('Error renaming file: /test_rename_file.txt file already exists',
                             context.exception.log_message)
        finally:
            try:
                self.file_api.remove(file_path, self.endpoint)
            except: pass
            try:
                self.file_api.remove(file_dest, self.endpoint)
            except: pass

    def test_new_file_model(self):
        file_path = posixpath.join(self.config.mount_dir, "test_new_file_model.txt")
        model = {
            "type": "file",
            "format": "text",
            "content": "Test content",
        }
        try:
            self.contents_manager.new(model, file_path)
            model = self.contents_manager.get(file_path, True, 'file')
            self.assertEqual(model["name"], "test_new_file_model.txt")
            self.assertEqual(model["path"], file_path)
            self.assertEqual(model["content"], "Test content")
            self.assertEqual(model["format"], "text")
            self.assertEqual(model["mimetype"], "text/plain")
            self.assertEqual(model["size"], 12)
            self.assertEqual(model["writable"], True)
            self.assertEqual(model["type"], "file")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    def test_new_notebook_model(self):
        file_path = posixpath.join(self.config.mount_dir, "test_new_notebook_model.ipynb")
        model = self._create_notebook_model()
        try:
            save_model = self.contents_manager.new(model, file_path)
            self.assertEqual(save_model["name"], "test_new_notebook_model.ipynb")
            self.assertEqual(save_model["path"], file_path)
            self.assertEqual(save_model["content"], None)
            self.assertEqual(save_model["format"], None)
            self.assertEqual(save_model["mimetype"], None)
            self.assertEqual(save_model["size"], 521)
            self.assertEqual(save_model["writable"], True)
            self.assertEqual(save_model["type"], "notebook")
        finally:
            self.file_api.remove(file_path, self.endpoint)

    def test_file_exits(self):
        file_path = posixpath.join(self.config.mount_dir, "test_file_exits.txt")
        message = "Lorem ipsum dolor sit amet..."
        self.file_api.write_file(file_path, message, self.endpoint)

        file_exists = self.contents_manager.file_exists(file_path)
        self.assertTrue(file_exists)

        self.file_api.remove(file_path, self.endpoint)
        with self.assertRaises(IOError):
            self.file_api.stat_info(file_path, self.endpoint)

        file_exists = self.contents_manager.file_exists(file_path)
        self.assertFalse(file_exists)

    def test_is_hidden(self):
        file_path = posixpath.join(self.config.mount_dir, ".test_hidden_file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, "test_dir/.test_hidden_file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, ".test_dir/file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, "root_dir/.test_dir/file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, "test_normal_file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, "test_dir/test_normal_file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, "test_dir/file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

        file_path = posixpath.join(self.config.mount_dir, "root_dir/test_dir/file.txt")
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

    def test_create_directory(self):
        dir_path = posixpath.join(self.config.mount_dir, "test_create_directory")
        self.file_api.create_directory(dir_path, self.endpoint)

        self.contents_manager.delete_file(dir_path)

        with self.assertRaises(IOError):
            self.file_api.stat_info(dir_path, self.endpoint)

    def test_get_directory(self):
        try:
            dir_path = posixpath.join(self.config.mount_dir, "test_get_directory")
            self.file_api.create_directory(dir_path, self.endpoint)
            sub_dir_path = posixpath.join(self.config.mount_dir, "test_get_directory/sub_dir")
            self.file_api.create_directory(sub_dir_path, self.endpoint)

            model = self.contents_manager.get(dir_path, True, 'directory')
            self.assertEqual(model["path"], dir_path)
            self.assertEqual(model["content"][0]["path"], sub_dir_path)

        finally:
            self.contents_manager.delete(dir_path)

    def test_get_directory_without_type(self):
        try:
            dir_path = posixpath.join(self.config.mount_dir, "test_get_directory_no_type")
            self.file_api.create_directory(dir_path, self.endpoint)
            sub_dir_path = posixpath.join(self.config.mount_dir, "test_get_directory_no_type/sub_dir")
            self.file_api.create_directory(sub_dir_path, self.endpoint)

            model = self.contents_manager.get(dir_path, True, None)
            self.assertEqual(model["path"], dir_path)
            self.assertEqual(model["content"][0]["path"], sub_dir_path)

        finally:
            self.contents_manager.delete(dir_path)

    def test_returns_404_for_nonexisting_file(self):
        dir_path = posixpath.join(self.config.mount_dir, 'no_such_dir')
        with self.assertRaises(web.HTTPError) as err:
            self.contents_manager.get(dir_path, type='file')
        self.assertEqual(err.exception.status_code, 404)

    def test_returns_404_for_nonexisting_file_with_no_type(self):
        file_path = posixpath.join(self.config.mount_dir, 'no_such_file')
        with self.assertRaises(web.HTTPError) as err:
            self.contents_manager.get(file_path, type=None)
        self.assertEqual(err.exception.status_code, 404)

    def test_returns_404_for_nonexisting_dir(self):
        file_path = posixpath.join(self.config.mount_dir, 'no_such_file')
        with self.assertRaises(web.HTTPError) as err:
            self.contents_manager.get(file_path, type='directory')
        self.assertEqual(err.exception.status_code, 404)

    def test_returns_404_for_nonexisting_notebook(self):
        notebook_path = posixpath.join(self.config.mount_dir, 'no_such_notebook.ipynb')
        with self.assertRaises(web.HTTPError) as err:
            self.contents_manager.get(notebook_path, type='notebook')
        self.assertEqual(err.exception.status_code, 404)

    def test_returns_404_for_nonexisting_notebook_without_type(self):
        notebook_path = posixpath.join(self.config.mount_dir, 'no_such_notebook.ipynb')
        with self.assertRaises(web.HTTPError) as err:
            self.contents_manager.get(notebook_path, type=None)
        self.assertEqual(err.exception.status_code, 404)

    def test_recreate_directory(self):
        file_path = posixpath.join(self.config.mount_dir, "test_recreate_directory")
        try:
            self.file_api.create_directory(file_path, self.endpoint)
            with self.assertRaises(IOError):
                self.file_api.create_directory(file_path, self.endpoint)
            self.contents_manager.delete_file(file_path)
            with self.assertRaises(IOError):
                self.file_api.stat_info(file_path, self.endpoint)
        except:
            self.contents_manager.delete_file(file_path)

    def test_create_subdirectory(self):
        try:
            file_path = posixpath.join(self.config.mount_dir, "test_create_directory")
            self.file_api.create_directory(file_path, self.endpoint)

            file_path2 = posixpath.join(self.config.mount_dir, "test_create_directory/test_subdir")
            self.file_api.create_directory(file_path2, self.endpoint)

            self.contents_manager.delete_file(file_path2)
            with self.assertRaises(IOError):
                self.file_api.stat_info(file_path2, self.endpoint)

            self.contents_manager.delete_file(file_path)
            with self.assertRaises(IOError):
                self.file_api.stat_info(file_path, self.endpoint)
        finally:
            try:
                self.contents_manager.delete(file_path)
            except: pass

    def test_kernel_path_when_config_entry_provided(self):
        self.config.kernel_path = "/test/path"
        path = self.contents_manager.get_kernel_path('')
        self.assertEqual(path, "/test/path")

    def test_kernel_path_when_config_entry_default(self):
        path = self.contents_manager.get_kernel_path('')
        self.assertEqual(path, "/")
