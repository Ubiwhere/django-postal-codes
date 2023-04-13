from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoPostalCodesConfig(AppConfig):
    name = "django_postal_codes"
    verbose_name = _("Postal Codes")
