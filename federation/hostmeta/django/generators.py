import importlib
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotFound

from federation.hostmeta.generators import RFC3033Webfinger

logger = logging.getLogger("federation")


def get_configuration():
    """
    Combine defaults with the Django configuration.
    """
    configuration = {
        "hcard_path": "/hcard/users/",
    }
    configuration.update(settings.FEDERATION)
    if not all([
        "profile_id_function" in configuration,
        "base_url" in configuration,
        "hcard_path" in configuration,
    ]):
        raise ImproperlyConfigured("Missing required FEDERATION settings, please check documentation.")
    return configuration


def get_profile_id_func():
    """
    Import the function to get profile ID by handle.
    """
    config = get_configuration()
    profile_func_path = config.get("profile_id_function")
    module_path, func_name = profile_func_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    profile_func = getattr(module, func_name)
    return profile_func


def rfc3033_webfinger_view(request, *args, **kwargs):
    """
    Django view to generate an RFC3033 webfinger.
    """
    resource = request.GET.get("resource")
    if not resource:
        return HttpResponseBadRequest("No resource found")
    if not resource.startswith("acct:"):
        return HttpResponseBadRequest("Invalid resource")

    handle = resource.replace("acct:", "")
    profile_id_func = get_profile_id_func()

    try:
        profile_id = profile_id_func(handle)
    except Exception as exc:
        logger.warning("rfc3033_webfinger_view - Failed to get profile ID by handle %s: %s", handle, exc)
        return HttpResponseNotFound()

    config = get_configuration()
    webfinger = RFC3033Webfinger(
        id=profile_id,
        base_url=config.get('base_url'),
        hcard_path=config.get('hcard_path'),
    )

    return JsonResponse(
        webfinger.render(),
        content_type="application/jrd+json",
    )
