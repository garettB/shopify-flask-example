from setuptools import setup, find_packages

setup(
    name="shopify_flask",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=open("requirements.txt").read().splitlines(),
    python_requires=">=3.8",
    author="adedaemon",
    description="A Flask-based Shopify example app.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ade-daemon/shopify-flask-example.git",
)
