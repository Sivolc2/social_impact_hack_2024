from setuptools import setup, find_packages

setup(
    name="the_green",
    version="0.1.0",
    packages=find_packages(include=['src', 'src.*']),
    install_requires=[
        "flask==3.0.2",
        "python-dotenv==1.0.1",
        "requests==2.31.0",
        "numpy==1.26.4",
        "pandas==2.2.1",
        "geopandas==0.14.3",
    ],
) 