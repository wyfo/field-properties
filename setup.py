from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

setup(
    name="field-properties",
    version="0.1",
    url="https://github.com/wyfo/field-properties",
    author="Joseph Perez",
    author_email="joperez@hotmail.fr",
    license="MIT",
    packages=find_packages(include=["field_properties*"]),
    package_data={"field_properties": ["py.typed"]},
    description="Properties for dataclass fields",
    long_description=README,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    install_requires=["dataclasses==0.7;python_version<'3.7'"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
