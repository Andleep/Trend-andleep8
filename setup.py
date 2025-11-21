from setuptools import setup, find_packages

setup(
    name="aion-quantum-ultra-max",
    version="1.0.0",
    description="Advanced AI Trading Bot with Quantum Learning",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.3",
        "numpy>=1.24.3",
        "plotly>=5.15.0",
        "scikit-learn>=1.3.0",
        "tensorflow>=2.13.0",
        "python-binance>=1.0.19",
        "matplotlib>=3.7.2",
        "scipy>=1.11.1",
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
)
