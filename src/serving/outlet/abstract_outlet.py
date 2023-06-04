import abc


class AbstractOutlet(metaclass=abc.ABCMeta):
    def __init__(self, configs):
        self.configs = configs
        self.outlet_object = None
        self._init_outlet()
        if self.outlet_object is None:
            raise RuntimeError()

    def __str__(self):
        return '<Outlet: %s>' % self.configs
    __repr__ = __str__

    @abc.abstractmethod
    def _init_outlet(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def post_result(self, task, data):
        raise NotImplementedError()
