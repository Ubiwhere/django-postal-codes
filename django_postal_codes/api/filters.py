"""
Module containing filters for API endpoints
"""
from django.db.models import QuerySet
from django_filters import rest_framework as filters

from ..models import Country, District, County, Locality, PostalCode

base = "Filters the results so that the {name} name contains this string"
COUNTRY_HELP_TEXT = base.format(name="country")
DISTRICT_HELP_TEXT = base.format(name="district")
COUNTY_HELP_TEXT = base.format(name="county")
LOCALITY_HELP_TEXT = base.format(name="locality")


class CountryFilter(filters.FilterSet):
    """
    Filter class for `Country` model.
    """

    country_name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        help_text=COUNTRY_HELP_TEXT,
    )

    class Meta:
        model = Country
        fields = ["country_name"]


class DistrictFilter(filters.FilterSet):
    """
    Filter class for `District` model.
    """

    # Allow filtering on country name
    country_name = filters.CharFilter(
        field_name="country__name",
        lookup_expr="icontains",
        help_text=COUNTRY_HELP_TEXT,
    )

    district_name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        help_text=DISTRICT_HELP_TEXT,
    )

    class Meta:
        model = District
        fields = ["country_name", "district_name"]


class CountyFilter(filters.FilterSet):
    """
    Filter class for `County` model.
    """

    # Allow filtering on country name
    country_name = filters.CharFilter(
        field_name="district__country__name",
        help_text=COUNTRY_HELP_TEXT,
    )

    # Allow filtering on district
    district_name = filters.CharFilter(
        field_name="district__name",
        lookup_expr="icontains",
        help_text=DISTRICT_HELP_TEXT,
    )

    county_name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        help_text=COUNTY_HELP_TEXT,
    )

    class Meta:
        model = County
        fields = ["country_name", "district_name", "county_name"]


class LocalityFilter(filters.FilterSet):
    """
    Filter class for `Locality` model.
    """

    # Allow filtering on country name
    country_name = filters.CharFilter(
        field_name="county__district__country__name",
        lookup_expr="icontains",
        help_text=COUNTRY_HELP_TEXT,
    )

    # Allow filtering on district
    district_name = filters.CharFilter(
        field_name="county__district__name",
        lookup_expr="icontains",
        help_text=DISTRICT_HELP_TEXT,
    )

    # Allow filtering on county
    county_name = filters.CharFilter(
        field_name="county__name",
        lookup_expr="icontains",
        help_text=COUNTY_HELP_TEXT,
    )

    locality_name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        help_text=LOCALITY_HELP_TEXT,
    )

    class Meta:
        model = Locality
        fields = ["country_name", "district_name", "county_name", "locality_name"]


class PostalCodeFilter(filters.FilterSet):
    """
    Filter class for `PostalCode` model.
    """

    # Allow filtering on country name
    country_name = filters.CharFilter(
        field_name="locality__county__district__country__name",
        lookup_expr="icontains",
        help_text=COUNTRY_HELP_TEXT,
    )

    # Allow filtering on district
    district_name = filters.CharFilter(
        field_name="locality__county__district__name",
        lookup_expr="icontains",
        help_text=DISTRICT_HELP_TEXT,
    )

    # Allow filtering on county
    county_name = filters.CharFilter(
        field_name="locality__county__name",
        lookup_expr="icontains",
        help_text=COUNTY_HELP_TEXT,
    )

    # Allow filtering on locality
    locality_name = filters.CharFilter(
        field_name="locality__name",
        lookup_expr="icontains",
        help_text=LOCALITY_HELP_TEXT,
    )

    # full_address = filters.CharFilter(
    #     field_name="full_address",
    #     method="filter_full_address",
    # )

    # def filter_full_address(
    #     self,
    #     queryset: QuerySet,
    #     name: str,
    #     value: str,
    # ) -> QuerySet:
    #     queryset.filter()

    class Meta:
        model = PostalCode
        fields = "__all__"
