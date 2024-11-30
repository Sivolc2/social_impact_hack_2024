from setuptools import setup, find_packages

setup(
    name="environmental-data-service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "anthropic",
        "python-dotenv",
        "h3",
        "geopandas",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-mock",
            "black",
            "isort",
            "mypy",
        ]
    },
    python_requires=">=3.8",
) 