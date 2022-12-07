"""
Module containing API serializers.
"""
from django.contrib.gis.geos import MultiPolygon
from rest_framework import serializers
from django_postal_codes.models import (
    Country,
    District,
    County,
    Locality,
    PostalCode,
    compute_polygon_union,
)


class CountrySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `Country`.
    """

    class Meta:
        model = Country
        fields = ["id", "url", "name"]


class DetailCountrySerializer(CountrySerializer):
    """
    Serializer class for a `Country` in Detail view.
    """

    # Downstream objects
    districts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="district-detail",
    )

    class Meta:
        model = Country
        fields = ["id", "url", "name", "created_on", "updated_on", "districts"]


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `District` in List view.
    """

    # Include url for parent object (country)
    parent_url = serializers.HyperlinkedRelatedField(
        source="country",
        read_only=True,
        view_name="country-detail",
    )

    class Meta:
        model = District
        fields = ["id", "url", "parent_url", "name"]


class DetailDistrictSerializer(DistrictSerializer):
    """
    Serializer class for a `District` in Detail view.
    """

    # Upstream fields
    country = serializers.ReadOnlyField(source="country.name")

    # Downstream fields
    counties = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="county-detail",
    )

    # Compute polygon of district by merging polygons of all localities
    # of all counties
    polygon = serializers.SerializerMethodField(read_only=True)

    def get_polygon(self, obj: County) -> MultiPolygon:
        """
        Computes the polygon of `County` from the union of all
        child `Locality` polygons.
        """
        polygons = list(obj.counties.values_list("localities__polygon", flat=True))

        return compute_polygon_union(polygons)

    class Meta:
        model = District
        fields = [
            "id",
            "url",
            "parent_url",
            "country",
            "name",
            "created_on",
            "updated_on",
            "counties",
            "polygon",
        ]


class CountySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `County` in List view.
    """

    # Include url for parent object (district)
    parent_url = serializers.HyperlinkedRelatedField(
        source="district",
        read_only=True,
        view_name="district-detail",
    )

    class Meta:
        model = County
        fields = ["id", "url", "parent_url", "name"]


class DetailCountySerializer(CountySerializer):
    """
    Serializer class for a `County` in Detail view.
    """

    # Upstream fields
    country = serializers.ReadOnlyField(source="district.country.name")
    district = serializers.ReadOnlyField(source="district.name")

    # Downstream fields
    localities = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="locality-detail",
    )

    # Compute polygon of county by merging all localities polygons
    polygon = serializers.SerializerMethodField(read_only=True)

    def get_polygon(self, obj: County) -> MultiPolygon:
        """
        Computes the polygon of `County` from the union of all
        child `Locality` polygons.
        """
        polygons = list(obj.localities.values_list("polygon", flat=True))

        return compute_polygon_union(polygons)

    class Meta:
        model = County
        fields = [
            "id",
            "url",
            "parent_url",
            "country",
            "district",
            "name",
            "created_on",
            "updated_on",
            "localities",
            "polygon",
        ]


class LocalitySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `Locality`.
    """

    # Include url for parent object (county)
    parent_url = serializers.HyperlinkedRelatedField(
        source="county",
        read_only=True,
        view_name="county-detail",
    )

    class Meta:
        model = Locality
        fields = [
            "id",
            "url",
            "parent_url",
            "name",
        ]


class DetailLocalitySerializer(LocalitySerializer):
    """
    Serializer class for a `Locality` in Detail view.
    """

    # Upstream fields
    country = serializers.ReadOnlyField(source="county.district.country.name")
    district = serializers.ReadOnlyField(source="county.district.name")
    county = serializers.ReadOnlyField(source="county.name")

    # No downstream fields because postal codes are too many

    class Meta:
        model = Locality
        fields = [
            "id",
            "url",
            "parent_url",
            "country",
            "district",
            "county",
            "name",
            "updated_on",
            "created_on",
            "polygon",
        ]


class PostalCodeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `PostalCode` in List view.
    """

    # Include link for parent object (locality)
    parent_url = serializers.HyperlinkedRelatedField(
        source="locality",
        read_only=True,
        view_name="locality-detail",
    )

    full_postal_code = serializers.SerializerMethodField(read_only=True)

    def get_full_postal_code(self, obj: PostalCode) -> str:
        """
        Returns the full postal code in a string version
        """
        return (
            f"{str(obj.postal_code).zfill(4)}-{str(obj.postal_code_extension).zfill(3)}"
        )

    class Meta:
        model = PostalCode
        fields = ["id", "url", "parent_url", "full_address", "full_postal_code"]


class DetailPostalCodeSerializer(PostalCodeSerializer):
    """
    Serializer class for a `PostalCode` in Detail view.
    """

    # Upstream fields
    country = serializers.ReadOnlyField(source="locality.county.district.country.name")
    district = serializers.ReadOnlyField(source="locality.county.district.name")
    county = serializers.ReadOnlyField(source="locality.county.name")
    locality = serializers.ReadOnlyField(source="locality.name")

    # Custom fields
    postal_code = serializers.SerializerMethodField()
    postal_code_extension = serializers.SerializerMethodField()

    def get_postal_code(self, obj) -> str:
        """
        Returns the postal code as fixed 4 digits string
        """
        return str(obj.postal_code).zfill(4)

    def get_postal_code_extension(self, obj) -> str:
        """
        Returns the postal code extension as fixed 3 digits string
        """
        return str(obj.postal_code_extension).zfill(3)

    class Meta:
        model = PostalCode
        fields = "__all__"
