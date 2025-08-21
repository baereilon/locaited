"""Setup configuration for LocAIted package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="locaited",
    version="0.4.0",
    author="LocAIted Team",
    description="AI-powered event discovery system for photojournalists",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/locaited",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "langchain>=0.1.0",
        "langgraph>=0.0.20",
        "python-dotenv>=1.0.0",
        "httpx>=0.24.0",
        "sqlalchemy>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "locaited-api=locaited.api:main",
        ],
    },
)