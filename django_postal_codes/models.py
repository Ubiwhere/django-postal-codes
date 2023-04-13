"""
Module containing the app models.
"""
from shapely.ops import unary_union
from shapely.geometry.multipolygon import MultiPolygon as ShapelyMultiPolygon
import json
import shapely
from shapely import wkt
from django.contrib.gis.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _


def compute_polygon_union(polygons) -> dict:
    """
    Computes the union of django polygons, and returns
    the result as a GeoJSON multipolygon dictionary
    """
    # Convert to shapely polygons
    polygons = [wkt.loads(obj.wkt) for obj in polygons]
    merged = unary_union(polygons)

    # Make sure it is MultiPolygon
    if merged.geom_type == "Polygon":
        merged = ShapelyMultiPolygon([merged])

    # Return as geojson dictionary
    return json.loads(json.dumps(shapely.geometry.mapping(merged)))


class BaseModel(models.Model):
    """
    Abstract model that adds created/updated timestamps
    """

    # Add timestamps to know when items were created/updated
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Country(BaseModel):
    """
    Model that defines a country
    """

    name = models.CharField(
        verbose_name=_("Country"),
        max_length=255,
        unique=True,
    )

    class Meta:
        ordering = ["name"]


class District(BaseModel):
    """
    Model that defines a district
    """

    # Name of district
    name = models.CharField(
        max_length=255,
        verbose_name=_("District"),
    )

    # country the district belongs too
    country = models.ForeignKey(
        Country,
        verbose_name=_("Country that the district belongs to"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="districts",
    )

    def __str__(self) -> str:
        """
        String representation of this model.
        """
        return gettext(f"{self.name}")

    class Meta:
        ordering = ["country", "name"]


class County(BaseModel):
    """
    Model that defines a county ("concelho" in Portuguese )
    """

    # county belongs to a district
    district = models.ForeignKey(
        District,
        verbose_name=_("District that the county belongs to"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="counties",
    )

    # The name of the county
    name = models.CharField(
        max_length=255,
        verbose_name=_("County"),
        null=False,
        blank=False,
    )

    def __str__(self) -> str:
        """
        String representation of this model.
        """
        return gettext(f"{self.name}")

    class Meta:
        ordering = ["district", "name"]


class Locality(BaseModel):
    """
    Model that defines a locality
    """

    # A locality belongs to a county
    county = models.ForeignKey(
        County,
        verbose_name=_("County that the locality belongs to"),
        related_name="localities",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Locality"),
        null=False,
        blank=False,
    )

    polygon = models.MultiPolygonField(
        verbose_name=_("Administrative region"),
        null=True,
        blank=True,
        geography=False,
        srid=4326,
    )

    def save(self, *args, **kwargs):
        from django.contrib.gis import geos

        # if mygeom ends up as a Polgon, make it into a MultiPolygon
        if self.polygon and isinstance(self.polygon, geos.Polygon):
            self.polygon = geos.MultiPolygon(self.polygon)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        String representation of this model.
        """
        return gettext(f"{self.name}")

    class Meta:
        ordering = ["county", "name"]


class PostalCode(BaseModel):
    """
    Model that defines a specific postal code.
    """

    # A postal code belongs to a specific locality
    locality = models.ForeignKey(
        Locality,
        verbose_name=_(
            "County that the postal code belongs too",
        ),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    artery_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Artery type"),
    )
    prep1 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("prep 1"),
    )
    artery_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Artery title"),
    )
    prep2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("prep 2"),
    )
    artery_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Artery name"),
    )
    artery_local = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Artery local"),
    )

    postal_code = models.IntegerField(
        verbose_name=_("Postal Code"),
        help_text="cp4",
        blank=True,
        null=False,
        db_index=True,
    )
    postal_code_extension = models.IntegerField(
        verbose_name=_("Postal Code Extension"),
        help_text="cp3",
        blank=True,
        null=False,
        db_index=True,
    )
    postal_designation = models.CharField(
        max_length=255,
        verbose_name=_("Postal Designation"),
        blank=True,
        null=True,
    )

    full_address = models.TextField(
        verbose_name=_("Full address"),
        blank=True,
        null=False,
    )

    def __str__(self) -> str:
        """
        String representation of this model.
        """
        return f"{str(self.postal_code)}-{str(self.postal_code_extension).zfill(3)} / {self.full_address}"

    def get_full_address(self):
        """
        Computes a full address based on the
        model fields.
        """
        full_name = " ".join(
            component
            for component in [
                self.artery_type,
                self.prep1,
                self.artery_title,
                self.prep2,
                self.artery_name,
                self.artery_local,
            ]
            if component is not None
        )
        # Check if locality and county are the same. If so dont include repeated name
        suffix = f"{self.locality.county.name}, {self.locality.county.district.name}, {self.locality.county.district.country.name}"
        if self.locality.name != self.locality.county.name:
            suffix = f"{self.locality.name}, {suffix}"
        if full_name:
            return f"{full_name}, {suffix}"
        return suffix

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        # Fill full address
        self.full_address = self.get_full_address()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Postal Code")
        verbose_name_plural = _("Postal Codes")
        ordering = ["locality", "full_address"]
