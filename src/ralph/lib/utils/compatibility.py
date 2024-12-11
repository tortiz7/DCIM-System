import django

if django.VERSION >= (4, 0):
    from django.utils.translation import gettext_lazy as _
    from django.utils.translation import gettext, ngettext
    from django.core.cache import caches
else:
    from django.utils.translation import ugettext_lazy as _  # noqa
    from django.utils.translation import ugettext as gettext  # noqa
    from django.utils.translation import ungettext as ngettext  # noqa
    from django.core.cache import get_cache as caches  # noqa

__all__ = ['_', 'gettext', 'ngettext', 'caches']