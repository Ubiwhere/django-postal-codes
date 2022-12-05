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
    # Country serializers
    CountrySerializer,
    DetailCountrySerializer,
    # District serializers
    DistrictSerializer,
    DetailDistrictSerializer,
    # County serializers
    CountySerializer,
    DetailCountySerializer,
    # Locality serializers
    LocalitySerializer,
    DetailLocalitySerializer,
    # Postal code serializers
    PostalCodeSerializer,
    DetailPostalCodeSerializer,
)
from .filters import (
    CountryFilter,
    DistrictFilter,
    CountyFilter,
    LocalityFilter,
    PostalCodeFilter,
)


class BaseViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    def get_serializer_class(self):

        if hasattr(self, "action_serializers"):
            return self.action_serializers.get(self.action, self.serializer_class)

        return super().get_serializer_class()


class CountryViewset(BaseViewSet):
    """
    API endpoint to retrieve countries.
    """

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CountryFilter

    action_serializers = {
        "retrieve": DetailCountrySerializer,
        "list": CountrySerializer,
    }


class DistrictViewset(BaseViewSet):
    """
    API endpoint to retrieve districts.
    """

    # Select upstream foreign keys and prefetch downstream related
    queryset = District.objects.select_related("country").prefetch_related("counties")

    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = DistrictFilter

    action_serializers = {
        "retrieve": DetailDistrictSerializer,
        "list": DistrictSerializer,
    }


class CountyViewset(BaseViewSet):
    """
    API endpoint to retrieve counties.
    """

    # Select upstream foreign keys and prefetch downstream related
    queryset = County.objects.select_related("district__country").prefetch_related(
        "localities"
    )

    serializer_class = CountySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CountyFilter

    action_serializers = {
        "retrieve": DetailCountySerializer,
        "list": CountySerializer,
    }


class LocalityViewset(BaseViewSet):
    """
    API endpoint to retrieve localities.
    """

    # Select upstream foreign keys
    queryset = Locality.objects.select_related("county__district__country")
    serializer_class = LocalitySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = LocalityFilter

    action_serializers = {
        "retrieve": DetailLocalitySerializer,
        "list": LocalitySerializer,
    }


class PostalCodesViewSet(BaseViewSet):
    """
    API endpoint to retrieve postal codes.
    """

    queryset = PostalCode.objects.all()
    serializer_class = PostalCodeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = PostalCodeFilter

    action_serializers = {
        "retrieve": DetailPostalCodeSerializer,
        "list": PostalCodeSerializer,
    }
