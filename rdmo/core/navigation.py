from django.apps import apps


def get_navigation_items():
    items = []

    for app_config in apps.get_app_configs():
        items.extend(getattr(app_config, 'navigation_items', ()))

    return sorted(
        items,
        key=lambda item: item.get('order', 100),
    )
