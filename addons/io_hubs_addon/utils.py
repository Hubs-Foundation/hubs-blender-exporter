import functools


def get_addon_package():
    return __package__


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def delayed_gather(func):
    """ It delays the gather until all resources are available """
    def wrapper_delayed_gather(*args, **kwargs):
        def gather():
            return func(*args, **kwargs)
        gather.delayed_gather = True
        return gather
    return wrapper_delayed_gather
