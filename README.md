WebInspectra Documentation

Welcome to the documentation for WebInspectra, a Python package for inspecting websites and detecting technologies used in web development.
Installation

To install WebInspectra, simply use pip:

pip install WebInspectra

Usage

You can use WebInspectra to inspect a website and retrieve information about the technologies used. Here's a basic example:

python

from WebInspectra.webinspectra import WebInspectra

# Initialize WebInspectra
inspectra = WebInspectra()

# Inspect a website
result = inspectra.inspect("https://example.com")

# Display the result
print(result)

Output

The inspect method returns a dictionary containing information about the detected technologies. Here's an example of the output format:

json

{
  "count": 3,
  "technologies": {
    "Technology 1": {
      "version": "1.0",
      "description": "Description of Technology 1"
    },
    "Technology 2": {
      "version": null,
      "description": "Description of Technology 2"
    },
    "Technology 3": {
      "version": "2.3.1",
      "description": "Description of Technology 3"
    }
  }
}

License

This project is licensed under the MIT License - see the LICENSE file for details.