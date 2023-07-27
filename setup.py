from setuptools import find_packages, setup

with open("README.rst", mode="r", encoding="utf-8") as fh:
    readme = fh.read()

with open("CHANGELOG.rst", mode="r", encoding="utf-8") as fh:
    changes = fh.read()


def parse_requirements(filename):
    """Load requirements from a pip requirements file"""
    with open(filename, mode="r", encoding="utf-8") as fh:
        lines = []
        for line in fh:
            line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


requirements = parse_requirements("requirements.txt")


if __name__ == "__main__":
    setup(
        name="ctxcore",
        use_scm_version=False,
        setup_requires=["setuptools"],
        description="Core functions for pycisTarget and the SCENIC tool suite",
        long_description="\n\n".join([readme, changes]),
        license="GNU General Public License v3",
        url="https://github.com/aertslab/ctxcore",
        author="Bram Van de Sande, Gert Hulselmans",
        maintainer="Gert Hulselmans",
        maintainer_email="gert.hulselmans@kuleuven.be",
        install_requires=requirements,
        keywords=["ctxcore", "cisTarget", "pycisTarget", "SCENIC", "pySCENIC", "pycisTopic"],
        include_package_data=True,
        package_dir={"": "src"},
        packages=find_packages("src"),
        zip_safe=False,
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
        ],
    )
