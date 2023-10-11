class memoized(dict):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args):
        return self[args]
    
    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result
