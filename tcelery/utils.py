import tornado.web


class route(object):
    """route decorator from https://github.com/peterbe/tornado-utils"""
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self._name = name

    def __call__(self, handler):
        """gets called when we class decorate"""
        name = self._name or handler.__name__
        self._routes.append(tornado.web.url(self._uri, handler, name=name))
        return handler

    @classmethod
    def get_routes(cls):
        return cls._routes
