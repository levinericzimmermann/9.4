import setuptools

setuptools.setup(
    name="walkman_modules.c9p4",
    packages=[
        package
        for package in setuptools.find_namespace_packages(include=["walkman_modules.*"])
        if package[:5] != "tests"
    ],
    setup_requires=[],
    install_requires=[
        # core package
        "audiowalkman>=0.20.2, <0.21.0",
        # for audio
        "pyo>=1.0.4, <2.0.0",
    ],
)
