import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="ts_tariffs",
    version="1.0.0",
    description="Calculate bills from timeseries consumption"
                " data and different tariff structures",
    long_description=README,
    long_description_content_type="text/markdown",
    url="",
    author="Joe Wyndham",
    author_email="joseph.wyndham@uts.edu.au",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["tariff_model"],
    include_package_data=True,
    install_requires=[
        'boto3',
        'pandas',
        'numpy',
        'dataclasses',
        'odin',
    ]
)
