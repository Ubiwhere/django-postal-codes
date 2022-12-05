"""
Module containing API serializers.
"""
from rest_framework import serializers
from django_postal_codes.models import Country, District, County, Locality, PostalCode


class CountrySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `Country`.
    """

    districts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="district-detail",
    )

    class Meta:
        model = Country
        fields = ["url", "name", "districts"]


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `District`.
    """

    # Upstream fields
    country = serializers.HyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name="country-detail",
    )

    # Downstream fields
    counties = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="county-detail",
    )

    class Meta:
        model = District
        fields = ["url", "country", "name", "counties"]


class CountySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `County`.
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

    class Meta:
        model = County
        fields = ["url", "country", "district", "name", "localities"]


class LocalitySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `Locality`.
    """

    # Upstream fields
    country = serializers.ReadOnlyField(source="county.district.country.name")
    district = serializers.ReadOnlyField(source="county.district.name")
    county = serializers.ReadOnlyField(source="county.name")

    # Include url for parent object (county)
    parent_url = serializers.HyperlinkedRelatedField(
        source="county",
        read_only=True,
        view_name="county-detail",
    )
    # No downstream fields because postal codes are too many

    class Meta:
        model = Locality
        fields = [
            "url",
            "country",
            "district",
            "parent_url",
            "county",
            "name",
            "polygon",
        ]


class PostalCodeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for a `PostalCode`.
    """

    # Upstream fields
    country = serializers.ReadOnlyField(source="locality.county.district.country.name")
    district = serializers.ReadOnlyField(source="locality.county.district.name")
    county = serializers.ReadOnlyField(source="locality.county.name")
    locality = serializers.ReadOnlyField(source="locality.name")

    # Custom fields
    full_address = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    postal_code_extension = serializers.SerializerMethodField()

    def get_full_address(self, obj) -> str:
        full_name = " ".join(
            component
            for component in [
                obj.artery_type,
                obj.prep1,
                obj.artery_title,
                obj.prep2,
                obj.artery_name,
                obj.artery_local,
            ]
            if component is not None
        )
        # Check if locality and county are the same. If so dont include repeated name
        suffix = f"{obj.locality.county.name}, {obj.locality.county.district.name}, {obj.locality.county.district.country.name}"
        if obj.locality.name != obj.locality.county.name:
            suffix = f"{obj.locality.name}, {suffix}"
        if full_name:
            return f"{full_name}, {suffix}"
        return suffix

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
