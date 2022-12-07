# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools

    use_setuptools()
    from setuptools import setup, find_packages
setup(
    name="ocp4-mco-ci",
    version="0.1.0",
    description="OCP4 MCO CI that setup DR using AWS",
    author="OCS Eng",
    author_email="rhocs-eng@redhat.com",
    license="",
    install_requires=[
        "pyyaml>=4.2b1",
        "bs4==0.0.1",
        "jinja2==3.0.3",
        "pyyaml>=4.2b1",
        "openshift==0.11.2",
        "requests==2.23.0",
        "bs4==0.0.1",
        "semantic-version==2.8.5",
    ],
    entry_points={
        "console_scripts": [
            "deploy-ocp=src.framework.deploy_ocp.main:main",
            "cleanup-ocp=src.cleanup.ocp:cluster_cleanup",
        ],
    },
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=["ez_setup"]),
)