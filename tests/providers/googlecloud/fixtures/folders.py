import os

import pytest

from aquavalet.core.path import AquaValetPath


@pytest.fixture()
def folder_wb_path():
    return AquaValetPath('/xml-api/folder-1/')


@pytest.fixture()
def folder_name():
    return 'folder-1'


@pytest.fixture()
def folder_obj_name():
    return 'xml-api/folder-1/'


@pytest.fixture()
def meta_folder_raw():
    with open(os.path.join(os.path.dirname(__file__), 'metadata/folder-raw.json'), 'r') as fp:
        return fp.read()


@pytest.fixture()
def meta_folder_parsed():
    with open(os.path.join(os.path.dirname(__file__), 'metadata/folder-parsed.json'), 'r') as fp:
        return fp.read()


@pytest.fixture()
def meta_folder_resp_headers_raw():
    with open(os.path.join(os.path.dirname(__file__), 'resp_headers/folder-raw.json'), 'r') as fp:
        return fp.read()
