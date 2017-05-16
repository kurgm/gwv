# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from setuptools.command.install import install
from setuptools import find_packages
from setuptools import setup


class my_install(install):

    def _pre_install(self):
        import bdat.build_mj
        bdat.build_mj.main()

        import bdat.build_cjksrc
        bdat.build_cjksrc.main()

    def run(self):
        self._pre_install()
        install.run(self)


setup(
    name="gwv",
    version="1.0",
    packages=find_packages(exclude=[
        "*.tests", "*.tests.*", "tests.*", "tests",
        "*.bdat", "*.bdat.*", "bdat.*", "bdat"
    ]),
    install_requires=[
        "xlrd"
    ],
    entry_points={
        "console_scripts": [
            "gwv = gwv.gwv:main"
        ]
    },
    cmdclass={'install': my_install},
    package_data={
        "gwv": ["data/*"],
    }
)
