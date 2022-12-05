"""
Module containing the app API views.
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, viewsets, permissions
from django_filters import rest_framework as filters
from django.contrib.gis.db.models.aggregates import Union

from django_postal_codes.models import Country, District, County, Locality, PostalCode
from django_postal_codes.api.serializers import PostalCodeSerializer

from .serializers import (
    CountrySerializer,
    DistrictSerializer,
    CountySerializer,
    LocalitySerializer,
    PostalCodeSerializer,
)
from .filters import (
    CountryFilter,
    DistrictFilter,
    CountyFilter,
    LocalityFilter,
    PostalCodeFilter,
)


class CountryViewset(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    API endpoint to retrieve countries.
    """

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CountryFilter


class DistrictViewset(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    API endpoint to retrieve districts.
    """

    # Select upstream foreign keys and prefetch downstream related
    queryset = District.objects.select_related("country").prefetch_related("counties")

    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = DistrictFilter


class CountyViewset(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    API endpoint to retrieve counties.
    """

    # Select upstream foreign keys and prefetch downstream related
    queryset = (
        County.objects.select_related("district__country")
        .prefetch_related("localities")
        .annotate(polygon=Union("localities__polygon"))
    )

    serializer_class = CountySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CountyFilter


class LocalityViewset(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    API endpoint to retrieve localities.
    """

    # Select upstream foreign keys
    queryset = Locality.objects.select_related("county__district__country")
    serializer_class = LocalitySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = LocalityFilter


class PostalCodesViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    API endpoint to retrieve postal codes.
    """

    queryset = PostalCode.objects.select_related("locality__county__district__country")
    serializer_class = PostalCodeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = PostalCodeFilter
