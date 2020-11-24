import setuptools

with open("readme.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name='minerva-cli',
    version='1.0.1',
    author="Juha Ruokonen",
    description='Minerva Command Line Interface',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/labsyspharm/minerva-cli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "boto3",
        "requests",
        "tabulate",
        "minerva-lib"
    ],
    dependency_links=[
        'git+https://github.com/labsyspharm/minerva-lib-python@master#egg=minerva-lib'
    ],
    entry_points={
        "console_scripts": [
            "minerva=cli.minerva:main"
        ]
    }
)

