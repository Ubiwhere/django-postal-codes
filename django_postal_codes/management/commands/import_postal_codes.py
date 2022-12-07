"""
Custom Django command to import data from a GitHub repository
into the local database
"""
import shutil
import runpy
from pathlib import Path
from django.db import transaction
from django.core.management import call_command
from django.conf import settings
from django.core.management.base import BaseCommand
import glob

# Check if user configured which countries data should be imported
COUNTRIES_TO_IMPORT = getattr(settings, "DJANGO_POSTAL_CODES_COUNTRIES", None)


def load_country_fixture(fixture_folder: str) -> None:
    """
    Receives a fixture folder path and rebuilds a json file from the existing
    parts. The json is splitted so each part is under 100mb and can be added to source control.
    To load fixture into django we need to glue the file back together
    """
    file_parts = [
        path
        for path in glob.glob(fixture_folder + "/*.json")
        if not Path(path).stem.startswith("MERGED_")
    ]
    country_name: str = Path(fixture_folder).stem
    final_fixture_path: str = (
        f"django_postal_codes/fixtures/{country_name}/MERGED_{country_name}.json"
    )
    with open(final_fixture_path, "wb") as wfd:
        for f in file_parts:
            with open(f, "rb") as fd:
                shutil.copyfileobj(fd, wfd)

    # Now time to load into django
    # Use a single transaction to speed up loading
    # https://stackoverflow.com/questions/19306807/django-fixture-loading-very-slow
    with transaction.atomic():
        call_command("loaddata", final_fixture_path)


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        Adds a --make and --no-make argument to command
        """
        import argparse

        parser.add_argument(
            "--make",
            action=argparse.BooleanOptionalAction,
            default=False,
            help="If True it will build a fixture for each country based on it's data pipeline",
        )

    def handle(self, *args, **options):
        """
        Imports data from a github repository and saves it in the database
        """
        make: bool = options["make"]

        if make:
            paths = [
                path
                for path in glob.glob(
                    "django_postal_codes/data_pipelines/*",
                    recursive=True,
                )
                if not Path(path).stem.startswith("__")
            ]
            for pth in paths:
                runpy.run_module(pth.replace("/", "."))

        else:
            # Import fixture into database
            paths = [
                path
                for path in glob.glob("django_postal_codes/fixtures/*")
                if not Path(path).stem.startswith("__")
            ]
            raise ValueError("Debug : ", paths)
            for pth in paths:
                load_country_fixture(pth)
