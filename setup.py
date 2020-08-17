from distutils.command.build import build
from setuptools import find_packages
from setuptools import setup

from gwv import __version__


class my_build(build):

    def _pre_build(self):
        import bdat
        bdat.main()

    def run(self):
        self._pre_build()
        build.run(self)


setup(
    name="gwv",
    version=__version__,
    packages=find_packages(exclude=[
        "*.tests", "*.tests.*", "tests.*", "tests",
        "*.bdat", "*.bdat.*", "bdat.*", "bdat"
    ]),
    entry_points={
        "console_scripts": [
            "gwv = gwv.gwv:main"
        ]
    },
    cmdclass={'build': my_build},
    package_data={
        "gwv": ["data/*"],
    },
    test_suite="tests",
)
