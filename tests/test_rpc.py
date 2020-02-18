# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import imp
import os
import time

import pytest

rpc_lib = imp.load_source(
    "rpc",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "python", "tk_desktop", "rpc.py"
    ),
)
RPCServerThread = rpc_lib.RPCServerThread
RPCProxy = rpc_lib.RPCProxy


class Boom(Exception):
    pass


class ComplexValue(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, rhs):
        return rhs.a == self.a and rhs.b == self.b


class FakeEngine:
    def execute_in_main_thread(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def pass_arg(self, arg):
        self.arg = arg
        return arg

    def pass_named_arg(self, named_arg="arg"):
        self.named_arg = named_arg
        return named_arg

    def set_something(self, something):
        self.something = something
        return something

    def boom(self):
        raise Boom()


@pytest.fixture
def fake_engine():
    return FakeEngine()


@pytest.fixture
def server(fake_engine):
    server = RPCServerThread(fake_engine)
    server.register_function(fake_engine.pass_arg)
    server.register_function(fake_engine.pass_named_arg)
    server.register_function(fake_engine.boom)
    server.register_function(fake_engine.set_something, "assign_something")
    server.start()
    try:
        yield server
    finally:
        server.close()


@pytest.fixture
def proxy(server):
    client = RPCProxy(server.pipe, server.authkey)
    try:
        yield client
    finally:
        client.close()


def test_list_functions(server):
    """
    Ensure function enumeration works.
    """
    assert sorted(server.list_functions()) == sorted(
        ["assign_something", "boom", "list_functions", "pass_arg", "pass_named_arg"]
    )


def test_initial_state(server, fake_engine):
    """
    Ensure initial state is expected.
    """
    assert server.is_closed() is False
    assert server.engine == fake_engine
    assert hasattr(server, "pipe")
    assert hasattr(server, "authkey")


@pytest.mark.parametrize(
    "method,attr,value",
    [
        ("pass_arg", "arg", 3),
        ("assign_something", "something", 3.14),
        ("assign_something", "something", ComplexValue(1, 2)),
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
    assert proxy.call("pass_named_arg", 4) == 4
    assert fake_engine.named_arg == 4


def await_value(obj, attr, expected):
    """
    Waits at most 5 seconds for a value.
    """
    before = time.time()
    while before + 5 > time.time():
        if getattr(obj, attr, None) == expected:
            return

    raise RuntimeError("Waited more than 5 seconds for value to settle.")


def test_server_close(server):
    server.close()
    assert server.is_closed()


def test_proxy_close(proxy):
    proxy.close()
    assert proxy.is_closed()


def test_call_no_response(fake_engine, proxy):
    """
    Test asynchronous calls
    """
    assert proxy.call_no_response("pass_arg", 3) is None
    await_value(fake_engine, "arg", 3)

    assert proxy.call_no_response("pass_named_arg", 4) is None
    await_value(fake_engine, "named_arg", 4)

    assert proxy.call_no_response("assign_something", 3.14) is None
    await_value(fake_engine, "something", 3.14)


def test_call_unknown_method(proxy):
    with pytest.raises(ValueError) as exc:
        proxy.call("unknown")
    assert str(exc).endswith("unknown function call: 'unknown'")

    # This should not raise, it's fire and forget.
    proxy.call_no_response("unknown")


def test_call_with_wrong_arguments(proxy):
    with pytest.raises(TypeError) as exc:
        proxy.call("pass_arg", 1, 2, 3)
    assert str(exc).endswith(
        "TypeError: pass_arg() takes exactly 2 arguments (4 given)"
    )


def test_call_with_exception_raised(proxy):
    with pytest.raises(Boom) as exc:
        proxy.call("boom")
