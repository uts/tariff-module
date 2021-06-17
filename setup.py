import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="ts_tariffs",
    version="1.0.2",
    description="Calculate bills from timeseries consumption"
                " data and different tariff structures",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/uts/tariff-module",
    author="Joe Wyndham",
    author_email="joseph.wyndham@uts.edu.au",
    license="GNU Lesser General Public License v2.1",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["ts_tariffs"],
    include_package_data=True,
    install_requires=[
        'boto3',
        'pandas',
        'numpy',
        'dataclasses',
        'odin',
    ]
)
