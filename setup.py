from setuptools import setup, find_packages

setup(
    name="mock_engine",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "faker",
        "jinja2",
        "requests",
    ],
    author="Yasar",
    author_email="965573557@qq.com",
    description="A mock engine for API testing and development",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Yarsar-l/mock_engine",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 