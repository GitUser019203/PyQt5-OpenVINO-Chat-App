#!/usr/bin/env python
"""Setup script for openvino-genai-chat package."""

from setuptools import setup, find_packages

setup(
    name="openvino-genai-chat",
    version="0.1.0",
    description="A professional PyQt5-based chat interface for local OpenVINO model inference",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/pyqt5-openvino-chat-app",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "openvino-genai>=0.2.0",
        "markdown>=3.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "build": [
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "openvino-chat=openvino_genai_chat.gui.main_window:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
