from setuptools import setup, find_packages
from pathlib import Path

# Leer README para long_description
long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="firstact",
    version="0.2.0",
    description="Librería de matemáticas actuariales básicas: tablas de mortalidad, seguros, anualidades y primas netas.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="firstact",
    python_requires=">=3.8",
    packages=find_packages(),
    package_data={
        "firstact": ["data/*.csv"],
    },
    include_package_data=True,
    install_requires=[
        "numpy>=1.21",
        "pandas>=1.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
