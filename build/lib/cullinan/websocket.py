from typing import Callable
from cullinan.controller import url_resolver, EncapsulationHandler


def websocket(**kwargs) -> Callable:
    url = kwargs.get('url', '')
    global url_params
    url_params = None
    if url != '':
        url, url_params = url_resolver(url)

    def inner(cls):
        EncapsulationHandler.add_url_ws(url, cls)

    return inner
