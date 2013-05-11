from macropy.core import *
from macropy.core.util import *
from ast import *


stop = object()


class GenericWalker(object):
    def __init__(self, func):
        self.func = func
        #self.flatten = lambda mylist: [l for sub in mylist for l in sub]

    def walk_children(self, tree, ctx=None):
        if isinstance(tree, AST):
            aggregates = []
            for field, old_value in iter_fields(tree):
                old_value = getattr(tree, field, None)
                new_value, new_aggregate = self.recurse_real(old_value, ctx)
                aggregates.append(new_aggregate)

                setattr(tree, field, new_value)
            return aggregates
        elif isinstance(tree, list) and len(tree) > 0:
            x = zip(*map(lambda x: self.recurse_real(x, ctx), tree))
            [trees, aggregates] = x
            tree[:] = flatten(trees)
            return flatten(aggregates)
        else:
            return []

    def recurse(self, tree, ctx=None):
        return self.recurse_real(tree, ctx)

    def recurse_real(self, tree, ctx=None):
        if ctx is stop:
            return tree, []
        else:
            x = self.func(tree, ctx)
            if x is not None :
                tree, new_ctx, aggregate = x
                aggregates = self.walk_children(tree, new_ctx)
                return tree, flatten([aggregate] + aggregates)
            else:
                return tree, []


class AggregateWalker(GenericWalker):
    def __init__(self, func):
        self.func = lambda tree, ctx: (lambda x: (x[0], [], x[1]))(func(tree))

    def recurse(self, tree):
        return self.recurse_real(tree)


class ContextWalker(GenericWalker):
    def __init__(self, func):
        self.func = lambda tree, ctx: (lambda x: (x[0], x[1], []))(func(tree, ctx))

    def recurse(self, tree, ctx):
        return self.recurse_real(tree, ctx)[0]


class Walker(GenericWalker):
    def __init__(self, func):
        self.func = lambda tree, ctx: (func(tree), [], [])

    def recurse(self, tree):
        res, agg = self.recurse_real(tree)
        return res