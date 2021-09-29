import pathlib
from setuptools import find_packages, setup
HERE = pathlib.Path(__file__).parent
README = (HERE / 'README.md').read_text()
setup(
    name='ts_tariffs',
    version='1.1.13',
    description='Calculate bills from timeseries consumption data and different tariff structures',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/uts/tariff-module',
    author='Joe Wyndham',
    author_email='joseph.wyndham@uts.edu.au',
    license='GNU Lesser General Public License v2.1',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    install_requires=[
        'boto3 >= 1.18.44',
        'matplotlib >= 3.4.3',
        'numpy >= 1.21.2',
        'pandas >= 1.3.3',
        'scipy >= 1.7.1',
        'pyarrow >= 5.0.0',
        'pydantic >= 1.8.2',
   ]
)
