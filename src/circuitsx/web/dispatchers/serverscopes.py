'''


.. codeauthor:: mnl
'''

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from circuits import handler, BaseComponent


class ServerScopes(BaseComponent):
    """Prefix the target to the request path.
    """

    channel = "web"

    @handler("request", filter=True, priority=1.0)
    def _on_request(self, event, request, response):
        path = request.path.strip("/")

        prefix = event._target

        if prefix:
            path = urljoin("/%s/" % prefix, path)
            request.path = path
