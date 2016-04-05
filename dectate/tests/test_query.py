import pytest

from dectate import (
    Query, execute, App, Action, Composite, commit, QueryError)


def test_query():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.foo('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction).attrs('name')

    assert list(execute(MyApp, q)) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_multi_action_query():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.directive('bar')
    class BarAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.bar('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction, BarAction).attrs('name')

    assert sorted(list(execute(MyApp, q))) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_filter():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.foo('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction).filter(name='a').attrs('name')

    assert list(execute(MyApp, q)) == [
        {'name': 'a'},
    ]


def test_filter_multiple_fields():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        filter_compare = {
            'model': lambda compared, value: issubclass(compared, value)
        }

        def __init__(self, model, name):
            self.model = model
            self.name = name

        def identifier(self, registry):
            return (self.model, self.name)

        def perform(self, obj, registry):
            registry.append((self.model, self.name, obj))

    class Alpha(object):
        pass

    class Beta(object):
        pass

    @MyApp.foo(model=Alpha, name='a')
    def f():
        pass

    @MyApp.foo(model=Alpha, name='b')
    def g():
        pass

    @MyApp.foo(model=Beta, name='a')
    def h():
        pass

    @MyApp.foo(model=Beta, name='b')
    def i():
        pass

    commit(MyApp)

    q = Query(FooAction)

    assert list(execute(MyApp, q.filter(model=Alpha, name='a').obj())) == [f]
    assert list(execute(MyApp, q.filter(model=Alpha, name='b').obj())) == [g]
    assert list(execute(MyApp, q.filter(model=Beta, name='a').obj())) == [h]
    assert list(execute(MyApp, q.filter(model=Beta, name='b').obj())) == [i]


def test_filter_not_found():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.foo('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction).filter(unknown='a').attrs('name')

    assert list(execute(MyApp, q)) == []


def test_filter_different_attribute_name():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        filter_name = {
            'name': '_name'
        }

        def __init__(self, name):
            self._name = name

        def identifier(self, registry):
            return self._name

        def perform(self, obj, registry):
            registry.append((self._name, obj))

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.foo('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction).filter(name='a').attrs('name')

    assert list(execute(MyApp, q)) == [{'name': 'a'}]


def test_filter_class():
    class MyApp(App):
        pass

    @MyApp.directive('view')
    class ViewAction(Action):
        config = {
            'registry': list
        }

        filter_compare = {
            'model': lambda compared, value: issubclass(compared, value)
        }

        def __init__(self, model):
            self.model = model

        def identifier(self, registry):
            return self.model

        def perform(self, obj, registry):
            registry.append((self.model, obj))

    class Alpha(object):
        pass

    class Beta(object):
        pass

    class Gamma(Beta):
        pass

    class Delta(Gamma):
        pass

    @MyApp.view(model=Alpha)
    def f():
        pass

    @MyApp.view(model=Beta)
    def g():
        pass

    @MyApp.view(model=Gamma)
    def h():
        pass

    @MyApp.view(model=Delta)
    def i():
        pass

    commit(MyApp)

    assert list(execute(
        MyApp,
        Query(ViewAction).filter(model=Alpha).obj())) == [f]

    assert list(execute(
        MyApp,
        Query(ViewAction).filter(model=Beta).obj())) == [g, h, i]

    assert list(execute(
        MyApp,
        Query(ViewAction).filter(model=Gamma).obj())) == [h, i]

    assert list(execute(
        MyApp,
        Query(ViewAction).filter(model=Delta).obj())) == [i]


def test_query_group_class():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.directive('bar')
    class BarAction(FooAction):
        group_class = FooAction

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.bar('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction).attrs('name')

    assert list(execute(MyApp, q)) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_query_on_group_class_action():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.directive('bar')
    class BarAction(FooAction):
        group_class = FooAction

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.bar('b')
    def g():
        pass

    commit(MyApp)

    q = Query(BarAction).attrs('name')

    assert list(execute(MyApp, q)) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_multi_query_on_group_class_action():
    class MyApp(App):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.directive('bar')
    class BarAction(FooAction):
        group_class = FooAction

    @MyApp.foo('a')
    def f():
        pass

    @MyApp.bar('b')
    def g():
        pass

    commit(MyApp)

    q = Query(FooAction, BarAction).attrs('name')

    assert sorted(list(execute(MyApp, q))) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_inheritance():
    class MyApp(App):
        pass

    class SubApp(MyApp):
        pass

    @MyApp.directive('foo')
    class FooAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.foo('a')
    def f():
        pass

    @SubApp.foo('b')
    def g():
        pass

    commit(SubApp)

    q = Query(FooAction).attrs('name')

    assert list(execute(SubApp, q)) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_composite_action():
    class MyApp(App):
        pass

    @MyApp.private_action_class
    class SubAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.directive('composite')
    class CompositeAction(Composite):
        query_classes = [
            SubAction
        ]

        def __init__(self, names):
            self.names = names

        def actions(self, obj):
            return [(SubAction(name), obj) for name in self.names]

    @MyApp.composite(['a', 'b'])
    def f():
        pass

    commit(MyApp)

    q = Query(CompositeAction).attrs('name')

    assert list(execute(MyApp, q)) == [
        {'name': 'a'},
        {'name': 'b'}
    ]


def test_composite_action_without_query_classes():
    class MyApp(App):
        pass

    @MyApp.private_action_class
    class SubAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.directive('composite')
    class CompositeAction(Composite):
        def __init__(self, names):
            self.names = names

        def actions(self, obj):
            return [(SubAction(name), obj) for name in self.names]

    @MyApp.composite(['a', 'b'])
    def f():
        pass

    commit(MyApp)

    q = Query(CompositeAction).attrs('name')

    with pytest.raises(QueryError):
        list(execute(MyApp, q))


def test_nested_composite_action():
    class MyApp(App):
        pass

    @MyApp.private_action_class
    class SubSubAction(Action):
        config = {
            'registry': list
        }

        def __init__(self, name):
            self.name = name

        def identifier(self, registry):
            return self.name

        def perform(self, obj, registry):
            registry.append((self.name, obj))

    @MyApp.private_action_class
    class SubAction(Composite):
        query_classes = [
            SubSubAction
        ]

        def __init__(self, names):
            self.names = names

        def actions(self, obj):
            return [(SubSubAction(name), obj) for name in self.names]

    @MyApp.directive('composite')
    class CompositeAction(Composite):
        query_classes = [
            SubAction
        ]

        def __init__(self, amount):
            self.amount = amount

        def actions(self, obj):
            for i in range(self.amount):
                yield SubAction(['a%s' % i, 'b%s' % i]), obj

    @MyApp.composite(2)
    def f():
        pass

    commit(MyApp)

    q = Query(CompositeAction).attrs('name')

    assert sorted(list(execute(MyApp, q))) == [
        {'name': 'a0'},
        {'name': 'a1'},
        {'name': 'b0'},
        {'name': 'b1'},
    ]