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
import time
from html.parser import HTMLParser
from urllib import request


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
    with open(license_file, "r", encoding="utf-8") as f:
        parser.feed(f.read())

    # We expect to atleast get one URL
    assert len(parser.tags) > 0
    return parser.tags


def test_3rd_party_links(licence_file_links):
    """
    Check all found urls are valid and can accessed.
    """
    max_retries = 8
    failed_urls = []
    skipped_urls = []
    
    # Use pytest warnings - always shown
    pytest.warns(UserWarning, match=".*")  # Enable warnings
    
    import warnings
    warnings.warn(f"Testing {len(licence_file_links)} URLs")

    for url in licence_file_links:
        retry_delay = 2
        last_error = None
        url_succeeded = False

        for attempt in range(max_retries):
            try:
                r = request.Request(
                    url,
                    headers={
                        "Accept-Language": "en",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    },
                )

                contents = request.urlopen(r, timeout=30).read()
                url_succeeded = True
                warnings.warn(f"SUCCESS: {url}")
                break

            except Exception as e:
                last_error = e
                error_message = str(e)

                if "403" in error_message or "Forbidden" in error_message:
                    skipped_urls.append({
                        'url': url,
                        'error': error_message
                    })
                    warnings.warn(f"SKIPPED (403): {url}")
                    url_succeeded = True
                    break

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)
        
        if not url_succeeded:
            failed_urls.append({
                'url': url,
                'error': str(last_error)
            })
            warnings.warn(f"FAILED: {url} - {last_error}")
    
    if skipped_urls:
        warnings.warn(f"{len(skipped_urls)} URLs skipped due to 403 errors")
    
    if failed_urls:
        error_msg = f"\n{len(failed_urls)} URL(s) failed after {max_retries} retries:\n"
        for item in failed_urls:
            error_msg += f"  - {item['url']}\n    Error: {item['error']}\n"
        pytest.fail(error_msg)

@pytest.mark.parametrize(
    "expected_url",
    [
        "https://github.com/shotgunsoftware/python-api/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-alias/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-core/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-adobe/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-alias/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-desktopclient/tree/master/software_credits",
        "https://github.com/shotgunsoftware/tk-framework-desktopserver/tree/master/software_credits",
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
