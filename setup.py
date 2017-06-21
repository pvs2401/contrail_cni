#
# Copyright (c) 2015 Juniper Networks, Inc.
#

import setuptools


def requirements(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    return lines

setuptools.setup(
    name='contrail-cni-direct',
    version='1.0',
    packages=setuptools.find_packages(),

    # metadata
    author="OpenContrail",
    author_email="dev@lists.opencontrail.org",
    license="Apache Software License",
    url="http://www.opencontrail.org/",
    description="Contrail CNI plugin",
    long_description="Contrail CNI plugin to connect the docker containers",
    install_requires=requirements('requirements.txt'),
    test_suite='opencontrail_anycast_vip.tests',
    tests_require=requirements('test-requirements.txt'),
    entry_points = {
        'console_scripts': [
            'contrail-cni-direct = contrail_cni_direct.topo_manager:main',
        ],
    },
)
