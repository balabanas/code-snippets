#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable(func):
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    e.g. memo = disable

    """
    def wrapper_do_nothing(*args):
        return func(*args)
    return wrapper_do_nothing


def decorator(func):
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """

    def wrapper_deco(*args):
        return func(*args)
    update_wrapper(wrapper_deco, func)
    return wrapper_deco


def countcalls(func):
    """Decorator that counts calls made to the function decorated."""
    @decorator
    def wrapper_cnt(*args):
        wrapper_cnt.calls += 1
        return func(*args)
    wrapper_cnt.calls = 0
    return wrapper_cnt


def memo(func):
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """
    cache = {}

    @decorator
    def wrapper_memo(*args):
        """Memo wrapper doc"""
        cache_key = args
        res = cache[cache_key] if cache_key in cache else func(*args)
        cache[cache_key] = res
        update_wrapper(wrapper_memo, func, assigned=('calls', ))  # loads .calls from countcalls deco to current wrapper
        return res
    return wrapper_memo


def n_ary(func):
    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    """
    @decorator
    def wrapper(*args):
        len_args = len(args)
        if len_args > 2:
            return func(args[0], wrapper(*args[1:]))
        elif len_args == 2:
            return func(*args)
        else:  # meant len_args == 1
            return args[0]
    return wrapper


def trace(indent='____'):
    """Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

     fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    """
    def trace_decorator(func):
        nest = -1

        @decorator
        def wrapper(*args):
            nonlocal nest
            nest += 1
            called = f'{func.__name__}({str(*args)})'
            print(indent * nest, '-->', called)
            res = func(*args)
            print(indent * nest, '<--', called, '==', res)
            nest -= 1
            return res
        return wrapper
    return trace_decorator


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b

# To disable some decorators:
# memo = disable
# countcalls = disable

@countcalls
@trace("####")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    print(fib(3))
    print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()
