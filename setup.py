from setuptools import find_packages
from setuptools import setup

setup(
    name="gwv",
    version="1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            "gwv = gwv.gwv:main"
        ]
    },
)
