from django.apps import apps


def get_navigation_items(user):
    items = []

    for app_config in apps.get_app_configs():
        for item in getattr(app_config, 'navigation_items', ()):
            permission = item.get('permission')

            if user.is_authenticated and (
                    permission is None or user.has_perm(permission)
            ):
                items.append(item)

    return sorted(items, key=lambda item: item.get('order', 100))
