from setuptools import setup, find_packages

setup(
    name="the_green",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "pydeck",
        "pandas",
        "geopandas",
        "numpy",
        "h3",
        "flask-cors",
        "python-dotenv",
        "requests",
        "beautifulsoup4",
        "openai",
        "aiohttp",
        "uagents",
        "pydantic",
    ]
) 