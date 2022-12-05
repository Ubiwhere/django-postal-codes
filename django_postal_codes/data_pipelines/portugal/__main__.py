"""
Loads data from Portugal into the database
"""
import logging
import tqdm
from django.contrib.gis.geos import GEOSGeometry, fromstr
import ast
import glob
import pandas as pd
import numpy as np
from joblib import Parallel, delayed
from shapely.ops import unary_union
from shapely.geometry import shape
from django.contrib.gis.geos import MultiPolygon
from tqdm import tqdm
from django.contrib.gis.gdal import DataSource
from django_postal_codes.models import District, PostalCode, County, Locality

from ..base import CountryStrategy


class PortugalStrategy(CountryStrategy):
    """
    Defines a data import strategy for country "Portugal"
    """

    def __init__(self) -> None:
        """
        Class constructor
        """
        super().__init__()
        # Read caop file
        self.caop_sheet = pd.read_excel(
            "django_postal_codes/data_pipelines/portugal/caop2021.xls",
            sheet_name="Areas_Freguesias_CAOP2021",
        )
        # Load administrative regions from CAOP files
        self.features = [
            feature
            for file in glob.glob("django_postal_codes/data/portugal/*.gpkg")
            for feature in DataSource(file)[0]
        ]
        # Load postal codes data
        self.postal_codes_sheet = pd.read_csv(
            "https://raw.githubusercontent.com/centraldedados/codigos_postais/master/data/codigos_postais.csv"
        )
        self.postal_codes_sheet.replace({np.nan: None}, inplace=True)

    @property
    def country_name(self) -> str:
        return "Portugal"

    @property
    def country_code(self) -> str:
        return "PT"

    def populate_districts(self) -> None:
        """
        Populates the `District` table for Portugal.
        """
        # Create districts
        districts = [
            District(
                name=district_name,
                country=self.country,
            )
            for district_name in self.caop_sheet["DISTRITO_ILHA_DSG"].dropna().unique()
        ]
        District.objects.all().delete()
        # Create in bulk for performance
        District.objects.bulk_create(districts)

    def populate_counties(self) -> None:
        """
        Populates the `County` table for Portugal.
        """
        # Create counties
        counties = [
            County(name=county_name, district=District.objects.get(name=district_name))
            for district_name, county_name in self.caop_sheet[
                ["DISTRITO_ILHA_DSG", "CONCELHO_DSG"]
            ]
            .drop_duplicates()
            .dropna()
            .values
        ]
        County.objects.bulk_create(counties)

    def populate_localities(self) -> None:
        """
        Populates the `Locality` table for Portugal.
        """
        # Create localities objects
        localities = [
            Locality(
                name=locality_name,
                county=County.objects.get(
                    name=county_name,
                    district__name=district_name,
                ),
                polygon=self.find_poly(dicofre=dicofre),
            )
            for district_name, locality_name, county_name, dicofre in self.caop_sheet[
                ["DISTRITO_ILHA_DSG", "FREGUESIA_DSG", "CONCELHO_DSG", "DICOFRE"]
            ]
            .drop_duplicates()
            .dropna()
            .values
        ]
        Locality.objects.bulk_create(localities)

    def create_postal_codes(self) -> None:
        """
        Populates the `PostalCode` with portuguese data.
        """

        iterator = reversed(list(self.postal_codes_sheet.itertuples()))

        queryset = PostalCode.objects.all()
        queryset._raw_delete(queryset.db)

        # Create parallel jobs using threads since the postal codes has a really high volume
        _ = Parallel(n_jobs=-1, prefer="threads", require="sharedmem")(
            delayed(self.process_postal_code_row)(row)
            for row in tqdm(iterator, total=self.postal_codes_sheet.shape[0])
        )

    def process_postal_code_row(self, row) -> None:
        """
        Processes a single row of a postal code and saves it in the `PostalCode` table.
        """
        # Find different postal codes with same designation,
        # same county, same district

        cols = [
            "num_cod_postal",
            "ext_cod_postal",
        ]
        options = self.postal_codes_sheet[
            (self.postal_codes_sheet["desig_postal"] == row.desig_postal)
            & (self.postal_codes_sheet["cod_distrito"] == row.cod_distrito)
            & (self.postal_codes_sheet["cod_concelho"] == row.cod_concelho)
        ][cols].values.tolist()

        # Options can have non-unique postalcode + extensions
        # To avoid wasting time on repeated combinations we make a set
        # to get unique pairs
        options = list(
            sorted(
                [
                    el
                    for el in set(tuple(row) for row in options)
                    if list(el) != [row.num_cod_postal, row.ext_cod_postal]
                ],
                key=lambda tuple: abs(row.ext_cod_postal - tuple[1]),
            )
        )

        locality = None
        for postal_code, postal_extension in [
            (row.num_cod_postal, row.ext_cod_postal),
        ] + options:
            point = self.coordinates_from_postal_code(postal_code, postal_extension)
            if not point:
                continue
            try:
                # Get locality which polygon contains the point
                locality = Locality.objects.get(polygon__intersects=point)
                break
            # Catch cases where the point is outside the country boarders (for instance,
            # at a beach. CAOP boundaries exclude beaches)
            except Locality.DoesNotExist:
                continue

        if not locality:
            logging.warning(
                "No found locality for ",
                row.nome_localidade,
                " Point is: ",
                point,
                " row: ",
                str(row),
            )
            return

        # Save the postal code to database
        PostalCode.objects.create(
            locality=locality,
            artery_type=row.tipo_arteria,
            prep1=row.prep1,
            artery_title=row.titulo_arteria,
            prep2=row.prep2,
            artery_name=row.nome_arteria,
            artery_local=row.local_arteria,
            postal_code=row.num_cod_postal,
            postal_code_extension=row.ext_cod_postal,
            postal_designation=row.desig_postal,
        )

    def find_poly(
        self,
        dicofre: str,
    ) -> MultiPolygon:
        """
        Returns a multipolygon of a portuguese region by "Dicofre" (value from CAOP database)
        """
        geometries = [
            feature.geom
            for feature in self.features
            if feature.get("Dicofre") == str(dicofre)
        ]

        if not geometries:
            raise RuntimeError(
                f"[{self.country_name.upper()}] Could not find geometries with dicofre {str(dicofre)}"
            )

        # Transform to normal lat/lon system
        for g in geometries:
            g.transform(4326)

        polygons = [shape(ast.literal_eval(g.json)) for g in geometries]
        poly = GEOSGeometry(unary_union(polygons).wkt, srid=4326)

        if poly.geom_type != "MultiPolygon":
            poly = MultiPolygon(
                fromstr(str(poly)),
            )

        assert poly.geom_type == "MultiPolygon", poly.geom_type

        return poly
