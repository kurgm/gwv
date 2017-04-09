# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from setuptools.command.install import install
from setuptools import find_packages
from setuptools import setup


class my_install(install):

    def _pre_install(self):
        pass

    def run(self):
        self._pre_install()
        install.run(self)


setup(
    name="gwv",
    version="1.0",
    packages=find_packages(),
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
