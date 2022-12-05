"""
Custom Django command to import data from a GitHub repository
into the local database
"""
import runpy
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
import glob

# Check if user configured which countries data should be imported
COUNTRIES_TO_IMPORT = getattr(settings, "DJANGO_POSTAL_CODES_COUNTRIES", None)
# If not configured we execute every script in "scripts" folder
if COUNTRIES_TO_IMPORT is None:
    COUNTRIES_TO_IMPORT = glob.glob(
        "django_postal_codes/data/*",
        recursive=True,
    )
# Transform to paths
COUNTRIES_TO_IMPORT = [
    path
    for path in COUNTRIES_TO_IMPORT
    if not (stem := Path(path).stem).startswith("__")
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        Adds a --overwrite and --no-overwrite argument to command
        """
        import argparse

        parser.add_argument(
            "--overwrite",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

    def handle(self, *args, **options):
        """
        Imports data from a github repository and saves it in the database
        """
        # TODO: Implement overwrite mechanism
        overwrite: bool = options["overwrite"]

        for country in COUNTRIES_TO_IMPORT:
            # Replace "/" with "."
            runpy.run_module(country.replace("/", "."))
