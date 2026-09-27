from setuptools import setup, find_packages

setup(
    name="alice_quant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.23.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "lightgbm>=3.3.0",
        "scikit-learn>=1.2.0",
        "scipy>=1.9.0",
        "tqdm>=4.64.0",
        "matplotlib>=3.6.0",
        "akshare>=1.10.0",
        "efinance>=2.0.0",
        "joblib>=1.2.0",
    ],
    python_requires=">=3.9",
)