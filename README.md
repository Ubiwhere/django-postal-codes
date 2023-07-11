# Django Postal Codes

[![Build Status](https://travis-ci.org/Ubiwhere/django-postal-codes.svg?branch=main)](https://travis-ci.org/Ubiwhere/django-postal-codes)
[![Coverage Status](https://coveralls.io/repos/github/Ubiwhere/django-postal-codes/badge.svg?branch=main)](https://coveralls.io/github/Ubiwhere/django-postal-codes?branch=main)

Django Postal Codes is a Django application that provides models and utilities for working with postal codes and their associated locations. It allows you to store and retrieve postal code information, such as cities, states, and countries, and perform operations like searching for nearby postal codes or validating postal codes. It is currently prepared for the Portuguese landscape (Portugal + Azores + Madeira), but other regions can be easily added and managed.

## Features

- Store and manage postal code data in your Django project.
- Retrieve postal code details such as city, state, country, and coordinates.
- Perform proximity searches to find nearby postal codes based on distance.
- Validate postal codes for various countries.
- Geocode addresses and retrieve postal codes based on location.

## Installation

To install Django Postal Codes, follow these steps:

1. Install the package using pip:

   ```shell
   pip install django-postal-codes
   ```

2. Add `'django_postal_codes'` to your Django project's `INSTALLED_APPS` setting:

   ```python
   INSTALLED_APPS = [
       # ...
       'django_postal_codes',
       # ...
   ]
   ```

3. Run database migrations to create the necessary tables:

   ```shell
   python manage.py migrate django_postal_codes
   ```

4. (Optional) Load initial postal code data. This step is necessary if you want to populate the database with postal code information. 🚨 It is currently and only prepared for Portugal data.

   ```shell
   python manage.py import_postal_codes
   ```

   > Note: Loading initial postal code data is an optional step and depends on your project's requirements. You can choose to load data from specific countries or regions if needed by retrieving the data from reliable sources and adapting it to the data importation format.

5. Start using Django Postal Codes in your project!

## Usage

Django Postal Codes provides models and utility functions to work with postal codes. Here are some examples of how you can use it:

- Add a postal code to your model:

  ```python
  # Use a foreign key to `PostalCode` from
  # `django_postal_codes`
  postal_code = models.ForeignKey(
    "django_postal_codes.PostalCode",
    null=False,
    blank=False,
    on_delete=models.PROTECT,
    verbose_name=_("Postal code of the house"),
  )
  ```

- Retrieve postal code information:

  ```python
  from django_postal_codes.models import PostalCode

  # Get details of a specific postal code
  postal_code = PostalCode.objects.get(postal_code='3030')
  print(postal_code.locality)  # Output: 'Santo António dos Olivais'
  print(postal_code.county)  # Output: 'Coimbra'
  print(postal_code.district)  # Output: 'Coimbra'
  print(postal_code.country)  # Output: 'Portugal'
  ```

- Add its API to your project's URLs

  ```python
  # Your urls.py file should include the following lines
  from django.urls import include, path
  
  urlpatterns += [
    path("api/", include("django_postal_codes.api.urls")),
  ]
  ```

  So you can access the OpenAPI docs specification at `/api/docs/`:

<img width="1436" alt="Screenshot of API resources in OpenAPI format" src="https://github.com/Ubiwhere/django-postal-codes/assets/115562920/67f909d0-8ae9-4995-afd7-03be2f4d0760">

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT  License](LICENSE).

