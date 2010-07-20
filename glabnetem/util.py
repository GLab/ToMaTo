# -*- coding: utf-8 -*-

class static:
  
    def __init__(self, anycallable):
        self.__call__ = anycallable
        
class curry:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, selfref, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(selfref, *(self.pending + args), **kw)
