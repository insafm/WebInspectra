import argparse
from webinspectra import WebInspectra

def main():
    parser = argparse.ArgumentParser(
        description='WebInspectra is a Python package designed for detecting web technologies used by a given URL. It provides a method to analyze the technologies powering a website, including frameworks, libraries, CDN usage, advertising platforms, and more. By leveraging various detection patterns and algorithms, WebInspectra identifies and categorizes the technologies utilized in the frontend and backend of web applications.')

    parser.add_argument('--url', '-u', type=str, required=True,
                        help='The URL of the website to inspect')
    parser.add_argument('--category', '-c', action='store_true',
                        help='Group results by category')

    args = parser.parse_args()

    inspectra = WebInspectra()
    result = inspectra.inspect(args.url, by_category=args.category)

    print(result)

if __name__ == '__main__':
    main()
