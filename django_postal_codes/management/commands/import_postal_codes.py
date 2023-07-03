"""
Custom Django command to import data from a GitHub repository
into the local database
"""
import os
import runpy
from django_postal_codes import BASE_DIR
from pathlib import Path
from django.db import transaction
from django.core.management import call_command
from django.conf import settings
from django.core.management.base import BaseCommand
import glob
import subprocess

# Check if the user configured which countries' data should be imported
COUNTRIES_TO_IMPORT = getattr(settings, "DJANGO_POSTAL_CODES_COUNTRIES", None)


def load_country_fixture(fixture_folder: str) -> None:
    """
    Receives a fixture folder path and rebuilds a JSON file from the existing
    parts. The JSON is split so each part is under 100 MB and can be added to source control.
    To load the fixture into Django, we need to glue the file back together
    """
    country_name: str = Path(fixture_folder).stem
    final_fixture_path: str = (
        f"{BASE_DIR}/fixtures/{country_name}/MERGED_{country_name}.json"
    )

    if os.path.exists(final_fixture_path):
        os.remove(final_fixture_path)
    with open(final_fixture_path, "w") as file:
        # Call is needed to block execution until the script ends
        # Otherwise, Django will start reading from the file, and it is not
        # fully merged yet, resulting in an error
        subprocess.call(f"cat {fixture_folder}/*.json", stdout=file, shell=True)

    # Now time to load into Django
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
            help="If True, it will build a fixture for each country based on its data pipeline",
        )

    def handle(self, *args, **options):
        """
        Imports data from a GitHub repository and saves it in the database
        """
        make: bool = options["make"]

        if make:
            paths = [
                path
                for path in glob.glob(
                    f"{BASE_DIR}/data_pipelines/*",
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
                for path in glob.glob(f"{BASE_DIR}/fixtures/*")
                if not Path(path).stem.startswith("__")
            ]
            for pth in paths:
                load_country_fixture(pth)
