# WebInspectra

WebInspectra is a Python package designed for detecting web technologies used by a given URL. It provides a method to analyze the technologies powering a website, including frameworks, libraries, CDN usage, advertising platforms, and more. By using various detection patterns and algorithms, WebInspectra identifies and categorizes the technologies utilized in the frontend and backend of web applications.

## Features
- Detects various web technologies and frameworks.
- Analyzes CDN usage and advertising platforms.
- Categorizes frontend and backend technologies.

## Installation

### Prerequisites
- Python 3.6 or higher
- Google Chrome
- Chrome Driver

### Install Chrome
- **Ubuntu**:
```sh
sudo apt-get install google-chrome-stable
```
- **macOS**: Download from [Chrome website](https://www.google.com/chrome/)
- **Windows**: Download from [Chrome website](https://www.google.com/chrome/)
- **Other Linux Distributions**: 
```sh
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install --yes --quiet --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*
```

### Install Chrome Driver
Official Chrome driver URL: [Chrome driver website](https://developer.chrome.com/docs/chromedriver)
- **Linux**: 
```sh
LATEST_CHROMEDRIVER_VERSION=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE) && \
    wget -q https://storage.googleapis.com/chrome-for-testing-public/${LATEST_CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver-linux64.zip
```

### Install WebInspectra
```bash
pip install WebInspectra
```

## Usage
WebInspectra can be used either as a command-line tool or as a Python module. Below are the detailed instructions for both methods.

### Command-Line Interface (CLI) Usage

To inspect a website using the command-line interface, use the webinspectra command. This command allows you to specify the URL of the website you want to inspect and optionally group the results by category.

```bash
python -m webinspectra --url <your_website_url> --category
```
- `--url` or `-u`: The URL of the website you want to inspect.
- `--category` or `-c`: An optional flag to group the results by category.

This command will analyze the technologies used on your provided website and group the results by category.

### Python Module Usage

You can also use WebInspectra directly within your Python code. This method provides more flexibility and allows you to integrate WebInspectra into your existing Python projects.

First, import the WebInspectra class from the webinspectra module. Then, create an instance of WebInspectra and call the inspect method with the URL of the website you want to inspect.

```python
from webinspectra import WebInspectra

# Create an instance of WebInspectra
inspectra = WebInspectra()

# Specify the URL of the website you want to inspect
url = "<your_website_url>"

# Call the inspect method, by_category is optional
result = inspectra.inspect(url, by_category=False)

# Print the result
print(result)
```
- `url`: The URL of the website you want to inspect.
- `by_category`: A boolean flag to indicate whether to group the results by category. Set to False by default.


### Explanation of the Output

The inspect method returns a dictionary containing the technologies detected on the specified website. Here's a breakdown of the structure of the returned dictionary:

- technologies: A dictionary where the keys are the names of the detected technologies and the values are dictionaries containing details about each technology.
  - versions: A list of detected versions for the technology.
  - description: A brief description of the technology.
  - cpe: The Common Platform Enumeration (CPE) identifier for the technology, if available.
  - website: The official website of the technology.
  - pricing: Information about the pricing of the technology, if available.
  - oss: A boolean flag indicating whether the technology is open-source software.
  - saas: A boolean flag indicating whether the technology is a software-as-a-service.
  - cats: A list of categories the technology belongs to.
  - confidence: A dictionary where the keys are the detection patterns and the values are confidence scores for each pattern.

#### Example Output
```json
{
    "technologies": {
        "Bootstrap": {
            "versions": ["5.3.3"],
            "description": "Bootstrap is a free and open-source CSS framework directed at responsive, mobile-first front-end web development. It contains CSS and JavaScript-based design templates for typography, forms, buttons, navigation, and other interface components.",
            "cpe": "cpe:2.3:a:getbootstrap:bootstrap:*:*:*:*:*:*:*:*",
            "website": "https://getbootstrap.com",
            "pricing": null,
            "oss": false,
            "saas": false,
            "cats": ["UI frameworks"],
            "confidence": {
                "scriptSrc default_key bootstrap(?:[^>]*?([0-9a-fA-F]{7,40}|[\\d]+(?:.[\\d]+(?:.[\\d]+)?)?)|)[^>]*?(?:\\.min)?\\.js": 100,
                "html default_key <link[^>]* href=[^>]*?bootstrap(?:[^>]*?([0-9a-fA-F]{7,40}|[\\d]+(?:.[\\d]+(?:.[\\d]+)?)?)|)[^>-]*?(?:\\.min)?\\.css": 100,
                "js bootstrap.Alert.VERSION ^(.+)$": 100
            }
        },
        ...
    },
    "count": 3
}
```

In this example, the tool detected the "Bootstrap" technology on the specified website, along with its version, description, and other relevant details. The count key indicates the total number of detected technologies.

By using WebInspectra, you can quickly and easily gain insights into the technologies used by any website, helping you make informed decisions about web development and technology adoption.

## Contributions
We welcome contributions! Please check the repository for contribution guidelines and open issues.

## License
WebInspectra is released under the GNU General Public License v3.0 (GPL-3.0).

We hope WebInspectra becomes an invaluable tool in your web development and security. Stay tuned for more updates and features in future releases!
