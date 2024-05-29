from setuptools import setup, find_packages
import pathlib

setup(
    name="WebInspectra",
    version="1.0.0",
    description="WebInspectra is a Python package designed for inspecting web technologies used by a given URL. It provides a method to analyze the technologies powering a website, including frameworks, libraries, CDN usage, advertising platforms, and more. By leveraging various detection patterns and algorithms, WebInspectra identifies and categorizes the technologies utilized in the frontend and backend of web applications.",
    long_description=(pathlib.Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Mohammed Insaf M (insafm)",
    url="https://github.com/insafm/WebInspectra",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
    ],
    packages=find_packages(exclude=['tests']),
    package_data={'WebInspectra': ['data/*']},
    license="GPLv3",
    install_requires=[
        'beautifulsoup4',
        'lxml',
        'requests',
        'selenium',
        'undetected-chromedriver',
    ],
    extras_require={
        'dev': ["pytest"],
        'logging': ["logging"],
    },
    python_requires='>=3.6'
)