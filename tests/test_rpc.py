# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import time
import six
import sgtk

import pytest
import contextlib

from rpc import (
    MultiprocessingRPCServerThread,
    HttpRPCServerThread,
    DualRPCServer,
    MultiprocessingRPCProxy,
    HttpRPCProxy,
)


class Boom(Exception):
    """
    Test exception that will be launched from an RPC call.
    """

    pass


class ComplexValue(object):
    """
    Class that will be pickled between the two RPC endpoints.
    """

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, rhs):
        """
        :returns: ``True`` if both sides of the equality are equal, ``False`` otherwise.
        """
        return isinstance(rhs, self.__class__) and rhs.a == self.a and rhs.b == self.b


class FakeEngine:
    """
    Fake desktop engine. Implements the interface expected for the engine to be
    usable by the RPC classes. It also provides a few test functions.
    """

    def execute_in_main_thread(self, func, *args, **kwargs):
        """
        Just call the function directly, don't worry about running it actually in
        the main thread, the test does not have any Qt dependency.
        """
        return func(*args, **kwargs)

    async_execute_in_main_thread = execute_in_main_thread

    def pass_arg(self, arg):
        """
        Stores are and returns it.
        """
        print("pass arg called", arg)
        self.arg = arg
        return arg

    def pass_named_arg(self, named_arg="arg"):
        """
        Stores named argument and returns it.
        """
        print("pass named arg called", named_arg)
        self.named_arg = named_arg
        return named_arg

    def set_something(self, something):
        """
        Method with a different name
        """
        print("set something called", something)
        self.something = something
        return something

    def boom(self):
        raise Boom()

    def long_call(self, close_proxy, return_value=None):
        if close_proxy:
            _close_proxy(self.proxy)
        time.sleep(3)
        return return_value


@pytest.fixture
def fake_engine():
    """
    Fixture returning the Fake engine instance.
    """
    return FakeEngine()


# We want to test every server version with their respective client.
# By using a parametrized server fixture, it means each test in this file
# that directly or indirectly uses the fixture will be called four times.
# Note that on Python 3, the multiprocessing server is never used by Desktop,
# we can ignore those servers.
@pytest.fixture(
    params=(
        [
            (MultiprocessingRPCServerThread, MultiprocessingRPCProxy),
            (DualRPCServer, MultiprocessingRPCProxy),
            (DualRPCServer, HttpRPCProxy),
        ]
        if six.PY2
        else []
    )
    + [(HttpRPCServerThread, HttpRPCProxy)]
)
def server(fake_engine, request):
    """
    Readies an RPCServerThread for use, preconfigure to be able to
    call method on a FakeEngine instance.

    :returns: A RPCServerThread instance.
    """
    server_factory = request.param[0]
    original_client_factory = request.param[1]

    # FIXME: There's some sort of race condition on Windows when the server and client
    # are started too quickly. It's spent a couple of hours trying to figure
    # it out but couldn't fix it. In real a world scenario, this is not an issue
    # since several seconds can elapse between the moment the server is started
    # and the moment the client connects, so we'll fix the flaky tests by adding
    # a 1 second sleep, which fixes the problem
    # if sgtk.util.is_windows() and original_client_factory == MultiprocessingRPCProxy:
    #     client_factory = lambda pipe, auth: time.sleep(1) or original_client_factory(
    #         pipe, auth
    #     )
    # else:
    #     client_factory = original_client_factory
    client_factory = lambda pipe, auth: time.sleep(1) or original_client_factory(
        pipe, auth
    )

    server = server_factory(fake_engine)
    server.register_function(fake_engine.pass_arg)
    server.register_function(fake_engine.pass_named_arg)
    server.register_function(fake_engine.boom)
    server.register_function(fake_engine.long_call)
    server.register_function(fake_engine.pass_arg, "pass_arg_as_another_name")
    server.start()

    if server_factory == DualRPCServer:
        if original_client_factory == HttpRPCProxy:
            factory = lambda server: client_factory(server.pipes[1], server.authkey)
        else:
            factory = lambda server: client_factory(server.pipes[0], server.authkey)
    else:
        factory = lambda server: client_factory(server.pipe, server.authkey)

    server.client_factory = factory
    try:
        yield server
    finally:
        if server.is_closed() is False:
            server.close()
        server.join()


@pytest.fixture
def proxy(server):
    """
    Creates a proxy that can communicate with the RPCServerThread
    fixture.

    :returns: A RPCProxy instance.
    """
    client = server.client_factory(server)
    try:
        yield client
    finally:
        if client.is_closed() is False:
            _close_proxy(client)


def test_list_functions(server):
    """
    Ensure function enumeration works.
    """
    function_list = server.list_functions()
    assert isinstance(function_list, list)
    assert sorted(function_list) == [
        "boom",
        "list_functions",
        "long_call",
        "pass_arg",
        "pass_arg_as_another_name",
        "pass_named_arg",
    ]


def test_api_backward_and_forward_compatible(server, proxy):
    """
    Ensure the RPCServerThread and RPCProxy have not changed
    API so they remain forward and backward compatible with
    different versions of tk-desktop.
    """
    # These are all the available API calls as of tk-desktop
    # 2.4.14:
    # https://github.com/shotgunsoftware/tk-desktop/blob/208d07710b87b2341c5e0d439b74212cd8d27434/python/tk_desktop/rpc.py
    assert hasattr(server, "is_closed")
    assert hasattr(server, "list_functions")
    assert hasattr(server, "register_function")
    assert hasattr(server, "close")
    assert hasattr(server, "engine")

    if isinstance(server, DualRPCServer) is False:
        assert hasattr(server, "pipe")

    assert hasattr(server, "authkey")

    assert hasattr(proxy, "call_no_response")
    assert hasattr(proxy, "call")
    assert hasattr(proxy, "is_closed")
    assert hasattr(proxy, "close")


@pytest.mark.parametrize(
    "method,attr,value",
    [
        ("pass_arg", "arg", 3),
        ("pass_arg_as_another_name", "arg", 3.14),
        ("pass_arg_as_another_name", "arg", ComplexValue(1, 2)),
    ],
)
def test_call(fake_engine, proxy, method, attr, value):
    """
    Test synchronous calls with positional parameters
    """
    assert proxy.call(method, value) == value
    assert getattr(fake_engine, attr) == value


def test_call_named_arg(fake_engine, proxy):
    """
    Test synchronous calls with named parameters
    """
    assert proxy.call("pass_named_arg", named_arg=4) == 4
    assert fake_engine.named_arg == 4


def await_value(obj, attr, expected):
    """
    Waits at most 5 seconds for a value.
    """
    before = time.time()
    while before + 10 > time.time():
        if getattr(obj, attr, None) == expected:
            return

    raise RuntimeError(
        "Waited more than 5 seconds for value to settle. Expected %s, got %s"
        % (expected, getattr(obj, attr, None))
    )


def test_server_close(server, proxy):
    """
    Ensure closing the server actually closes it.
    """
    server.close()
    server.join()
    assert server.is_closed()
    assert not server.is_alive()

    with pytest.raises(Exception) as exc:
        proxy.call("pass_arg", 1)

    if sgtk.util.is_windows():
        assert "No connection could be made" in str(
            exc.value
        ) or "The pipe is being closed" in str(exc.value)
    else:
        assert "Connection refused" in str(exc.value) or "Broken pipe" in str(exc.value)


def test_proxy_close(proxy):
    """
    Ensure closing a proxy actually closes it.
    """
    _close_proxy(proxy)
    assert proxy.is_closed()


def test_call_no_response(fake_engine, proxy):
    """
    Ensures an asynchronous call actually happens.
    """
    assert proxy.call_no_response("pass_arg", 3) is None
    await_value(fake_engine, "arg", 3)

    assert proxy.call_no_response("pass_named_arg", 4) is None
    await_value(fake_engine, "named_arg", 4)

    assert proxy.call_no_response("pass_arg_as_another_name", 3.14) is None
    await_value(fake_engine, "arg", 3.14)


def test_call_unknown_method(proxy):
    """
    Ensures unknown method raise an error.
    """
    with pytest.raises(ValueError) as exc:
        proxy.call("unknown")
    assert str(exc.value) == "unknown function call: 'unknown'"

    # This should not raise, it's fire and forget.
    proxy.call_no_response("unknown")


def test_call_with_wrong_arguments(proxy):
    """
    Ensures passing the wrong number of arguments raise an error.
    """
    with pytest.raises(TypeError) as exc:
        proxy.call("pass_arg", 1, 2, 3)
    if six.PY3:
        assert (
            str(exc.value) == "pass_arg() takes 2 positional arguments but 4 were given"
        )
    else:
        assert str(exc.value) == "pass_arg() takes exactly 2 arguments (4 given)"


def test_proxy_close_during_long_call(proxy, fake_engine, server):
    """
    Ensure proxy being clone while a call is ongoing will raise an error.
    """
    fake_engine.proxy = proxy
    with pytest.raises(RuntimeError) as exc:
        proxy.call("long_call", close_proxy=True)
    assert str(exc.value) == "client closed while waiting for a response"


def test_long_call(proxy):
    """
    Ensure a long_call works.
    """
    assert proxy.call("long_call", close_proxy=False, return_value=1) == 1


def test_call_with_exception_raised(proxy):
    """
    Ensure exceptions raise by the server are sent back to the client correctly.
    """
    with pytest.raises(Boom):
        proxy.call("boom")


def test_bad_http_auth_key(fake_engine):
    """
    Ensure connecting to a server with the wrong auth key will reject
    the request.
    """
    with contextlib.closing(HttpRPCServerThread(fake_engine)) as server:
        server.start()
        with contextlib.closing(HttpRPCProxy(server.pipe, "12345")) as proxy:
            with pytest.raises(ValueError) as exc:
                proxy.call("list_functions")
            assert str(exc.value) == "invalid auth key"


@pytest.mark.skipif(six.PY3, reason="Multiprocessing server not supported on Python 3.")
def test_bad_multi_auth_key(fake_engine):
    """
    Ensure connecting to a server with the wrong auth key will reject
    the request.
    """
    with contextlib.closing(MultiprocessingRPCServerThread(fake_engine)) as server:
        server.start()
        # FIXME: There's some sort of race condition on Windows when the server and client
        # are started too quickly. It's spent a couple of hours trying to figure
        # it out but couldn't fix it. In real a world scenario, this is not an issue
        # since several seconds can elapse between the moment the server is started
        # and the moment the client connects, so we'll fix the flaky tests by adding
        # a 1 second sleep, which fixes the problem
        if sgtk.util.is_windows():
            time.sleep(1)
        with pytest.raises(Exception) as exc:
            MultiprocessingRPCProxy(server.pipe, b"12345")
        assert str(exc.value) == "digest sent was rejected"


def _close_proxy(proxy):
    if isinstance(proxy, HttpRPCProxy):
        proxy.close(join=True)
    else:
        proxy.close()


def test_calling_when_closed(proxy):
    """
    Ensure calling a method on the clietn when it is closed fails.
    """
    _close_proxy(proxy)
    client_type = "multi" if isinstance(proxy, MultiprocessingRPCProxy) else "http"
    with pytest.raises(RuntimeError) as exc:
        proxy.call("anything")
    assert (
        str(exc.value)
        == "closed %s client waiting call 'anything((), {})'" % client_type
    )

    with pytest.raises(RuntimeError) as exc:
        proxy.call_no_response("anything")
    assert str(exc.value) == "closed %s client calling 'anything((), {})'" % client_type
