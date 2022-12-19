from rest_framework import routers
from django_postal_codes.api.views import (
    CountryViewset,
    DistrictViewset,
    PostalCodesViewSet,
    LocalityViewset,
    CountyViewset,
)

router = routers.SimpleRouter()
router.register(
    "postal-codes/countries",
    CountryViewset,
    basename="country",
)
router.register(
    "postal-codes/districts",
    DistrictViewset,
    basename="district",
)
router.register(
    "postal-codes/counties",
    CountyViewset,
    basename="county",
)
router.register(
    "postal-codes/localities",
    LocalityViewset,
    basename="locality",
)
router.register(
    "postal-codes",
    PostalCodesViewSet,
    basename="postalcode",
)
urlpatterns = router.urls
