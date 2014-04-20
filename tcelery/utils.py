class route(object):
    """route decorator from https://github.com/peterbe/tornado-utils"""
    _routes = []

    def __init__(self, regexp):
        self._regexp = regexp

    def __call__(self, handler):
        """gets called when we class decorate"""
        self._routes.append((self._regexp, handler))
        return handler

    @classmethod
    def get_routes(cls):
        return cls._routes
