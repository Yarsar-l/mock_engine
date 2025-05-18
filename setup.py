from setuptools import setup, find_packages

setup(
    name="mock_engine",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "faker",
        "jinja2",
        "requests",
        "jsonpath-ng"
    ],
    author="Yasar",
    author_email="liang965573557@qq.com",
    description="A powerful Python mock engine for API testing, template rendering, and code execution with debugging and assertion support.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Yarsar-l/mock_engine",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    python_requires=">=3.6",
    include_package_data=True,
) 