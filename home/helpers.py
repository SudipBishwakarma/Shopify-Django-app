from .models import FirstRun


def first_run(store_url, status=None):
    """Checks if the app is run for the first time."""
    obj, created = FirstRun.objects.get_or_create(myshopify_domain=store_url)
    if type(status) == bool and not status:
        obj.status = status
        obj.save()
    return obj.status
