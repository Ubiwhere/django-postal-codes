"""
Module containing a base strategy to import Data for a specific
country
"""
from typing import Optional
from abc import ABC, abstractproperty, abstractmethod
from django.db import transaction
from django.contrib.gis.geos import Point
import pgeocode
import numpy as np
from django_postal_codes.models import Country, District, County, Locality


class CountryStrategy(ABC):
    """
    Abstract class that defines a strategy pattern to import data
    for a specific country
    """

    nominatim: pgeocode.Nominatim

    def __init__(self) -> None:
        """
        Class constructor
        """
        # Instantiate the country's nominatim
        self.nominatim = pgeocode.Nominatim(self.country_code)

    @abstractproperty
    def country_code(self) -> str:
        """
        Child classes must implement this property to return a string indicating
        the country code for Nominatim.
        """

    @abstractproperty
    def country_name(self) -> str:
        """
        Child classes must implement this property to return the country name.
        """

    @property
    def country(self) -> Country:
        """
        Returns the `Country` object based on `country_name`
        """
        return Country.objects.get_or_create(name=self.country_name)[0]

    def coordinates_from_postal_code(
        self,
        postal_code: str,
        postal_code_extension: str,
    ) -> Optional[Point]:
        """
        Returns a Django `Point` (coordinates) based on a provided postal code
        """
        full_postal_str = f"{postal_code}-{str(postal_code_extension).zfill(3)}"

        response = self.nominatim.query_postal_code(full_postal_str)

        latitude = response["latitude"], longitude = response["longitude"]

        if np.isnan(latitude) or np.isnan(longitude):
            return None

        return Point(longitude, latitude)

    def execute(self) -> None:
        """
        Executes the strategy to import the data. All database transactions are executed
        within an atomic block.
        """
        # Execute the pipeline inside atomic block
        with transaction.atomic():
            self.populate_country()
            self.populate_districts()
            self.populate_counties()
            self.populate_postal_codes()

    def populate_country(self) -> None:
        """
        Populates the `Country` table with a new row based on `.country_name` property.
        """
        # Delete existing country
        # Will cascade the deletion of entire data about this country
        Country.objects.filter(name=self.country_name).delete()
        # Create new instance
        Country.objects.create(name=self.country_name)

    @abstractmethod
    def populate_districts(self) -> None:
        """
        Child classes must implement this method to populate the `District` table.
        """

    @abstractmethod
    def populate_counties(self) -> None:
        """
        Child classes must implement this method to populate the `County` table.
        """

    @abstractmethod
    def populate_postal_codes(self) -> None:
        """
        Child classes must implement this method to populate the `PostalCode` table.
        """
