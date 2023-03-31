from setuptools import setup

setup(
    name="daslic",
    version="1.0",
    packages=['daslic'],
    package_dir={'daslic': 'daslic'},
    package_data={
        # If any package contains *.so, include them:
        "daslic": ["aarch64/*.so", "x86_64/*.so", "mips64el/*.so"],
    },
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["daslic/daslic_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0"],
)