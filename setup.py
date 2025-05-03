"""
Setup script for traced package.
"""

from setuptools import setup, find_packages

setup(
    name="traced",
    version="0.1.0",
    description="A simple but powerful tracing library for Python applications",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/traced",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "mongodb": ["pymongo>=3.12.0"],
        "sqlite": [],  # No additional dependencies needed for SQLite
        "all": ["pymongo>=3.12.0"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
)