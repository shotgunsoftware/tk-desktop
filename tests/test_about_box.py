# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import pytest
from six.moves.html_parser import HTMLParser
from six.moves.urllib import request


@pytest.fixture
def license_file():
    """
    Gets the path to the licence html file.
    """
    license_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "python", "tk_desktop", "licenses.html"
        )
    )
    assert os.path.isfile(license_file)
    return license_file


@pytest.fixture
def licence_file_links(license_file):
    """
    Given the path to the licence html file, it extracts the URL link out and
    returns them in a list.
    """
    # This class was taken and modified from this SO post:
    # https://stackoverflow.com/a/3075561/4223964
    class MyHTMLParser(HTMLParser):
        tags = []

        def handle_starttag(self, tag, attrs):
            # Only parse the 'anchor' tag.
            if tag == "a":
                # Check the list of defined attributes.
                for name, value in attrs:
                    # If href is defined, store the URL
                    if name == "href":
                        self.tags.append(value)

    # Open the licence file and read the parse the contents.
    parser = MyHTMLParser()
    with open(license_file, "r") as f:
        parser.feed(f.read())

    # We expect to atleast get one URL
    assert len(parser.tags) > 0
    return parser.tags


def test_3rd_party_links(licence_file_links):
    """
    Check all found urls are valid and can accessed.
    """
    for url in licence_file_links:
        if (
            url == "https://www.autodesk.com/company/legal-notices-trademarks"
            "/trademarks/autodesk-inc"
        ):
            continue
        try:
            request.urlopen(url)
        except Exception as e:
            raise pytest.fail("Failed to open {0}, error: {1}".format(url, e))


@pytest.mark.parametrize(
    "expected_url",
    [
        "https://github.com/shotgunsoftware/python-api/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-3dsmax/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-3dsmaxplus/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-core/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-adobe/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-desktopserver/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-lmv/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-houdini/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-multi-pythonconsole/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-multi-reviewsubmission/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-nuke-quickreview/tree/master/software_credits",
    ],
)
def test_expected_url_exist(licence_file_links, expected_url):
    """
    Checks that the expected URL is in the list.
    """
    assert expected_url in licence_file_links
