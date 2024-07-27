import logging
import time
from bs4 import BeautifulSoup
import requests
import dns.resolver
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils.selenium_utils import SeleniumUtilities

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class WebPage:
	"""
	Represents a web page object with various attributes and methods
	for loading and retrieving information about a web page.
	"""

	def __init__(self, url):
		"""
		Initializes a WebPage object with a given URL.

		Args:
			url (str): The URL of the web page.
		"""
		self.url = url
		self.domain = ""
		self.html = ""
		self.common_data = {}
		self.headers = {}
		self.scripts = []
		self.meta = {}
		self.driver = None
		self.robots_txt = ""
		self.dns = {}
		self.css_rules = []
		self.xhrs = []

	def load(self):
		"""
		Loads the web page and retrieves various information about it.

		Returns:
			WebPage: The updated WebPage object.
		"""
		# Set the domain of the web page
		self.set_domain()

		# Initialize SeleniumUtilities
		sele_utils = SeleniumUtilities()

		# Load the URL
		self.common_data = sele_utils.load_url(self.url)
		self.driver = sele_utils.driver
		self.url = self.driver.current_url

		# Fetch and parse HTML
		self.html = sele_utils.driver.page_source
		self.parsed_html = BeautifulSoup(self.html, 'lxml')

		# Fetch various information using ThreadPoolExecutor
		with ThreadPoolExecutor(max_workers=10) as executor:
			futures = {
				"headers": executor.submit(sele_utils.get_headers),
				"css": executor.submit(sele_utils.get_css_rules),
				"xhr": executor.submit(lambda: [item.get("url") for item in sele_utils.get_xhrs()]),
				"robots": executor.submit(self.get_robots_txt),
				"dns": executor.submit(self.get_dns_records),
				"scriptSrc": executor.submit(self.get_scripts),
				"meta": executor.submit(self.get_meta),
				"cookies": executor.submit(self.get_cookies),
			}

			# Retrieve and assign the results
			for key, future in futures.items():
				try:
					setattr(self, key, future.result())
				except Exception as e:
					print(f"Failed to fetch {key}: {e}")

		# Process scripts loading after retrieving scriptSrc
		self.scripts = self.load_scripts(self.scriptSrc)

		return self

	def get_robots_txt(self):
		"""
		Retrieve the content of the robots.txt file of the web page's domain.

		Returns:
			str or None: The content of the robots.txt file if available, None otherwise.
		"""
		# Initialize robots_content to None
		robots_content = None

		# Construct the URL for robots.txt using the base URL of the web page
		robots_txt_url = urljoin(self.url, "robots.txt")

		try:
			# Send a GET request to fetch the content of robots.txt with a timeout
			response = requests.get(robots_txt_url, timeout=5)

			# Check if the response status code is 200 (OK)
			if response.status_code == 200:
				# If the request was successful, assign the content of robots.txt to robots_content
				robots_content = response.text
		except requests.RequestException as e:
			# Handle any request exceptions (e.g., timeout, connection error)
			print(f"Failed to fetch robots.txt: {e}")

		return robots_content

	def get_dns_records(self):
		"""
		Retrieve DNS records of the web page's domain.

		Returns:
			dict: A dictionary containing DNS record types as keys and
			their corresponding answers as values.
		"""
		# Initialize a dictionary to store DNS records
		answers = {}
		
		# Check if the domain exists
		if self.domain:
			# Define the types of DNS records to fetch
			record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'TXT', 'SRV', 'DS', 'DNSKEY']
			
			# Use ThreadPoolExecutor to concurrently resolve DNS records
			with ThreadPoolExecutor(max_workers=10) as executor:
				# Submit DNS resolution tasks for each record type
				futures = {
					executor.submit(
						self.resolve_with_retry, record_type): record_type
						for record_type in record_types
					}
				
				# Iterate through completed futures
				for future in as_completed(futures):
					record_type = futures[future]
					try:
						# Store the resolved DNS records in the answers dictionary
						answers[record_type.lower()] = future.result()
					except Exception as e:
						# Print error message if DNS resolution fails for a record type
						logger.error(f"Failed to resolve {record_type} records: {e}")
						answers[record_type.lower()] = []

		return answers

	def resolve_with_retry(self, record_type, retries=3, delay=1):
		"""
		Resolve DNS records with retry mechanism.

		Args:
			record_type (str): The type of DNS record to resolve.
			retries (int): The number of times to retry DNS resolution in case of failure. Default is 3.
			delay (int): The delay (in seconds) between retries. Default is 1.

		Returns:
			list: A list of resolved DNS records.
		"""
		# Attempt DNS resolution with retry mechanism
		for _ in range(retries):
			try:
				# Resolve DNS records for the given record type
				dns_records = dns.resolver.resolve(self.domain, record_type)

				# Convert resolved DNS records to text format and return
				return [record.to_text() for record in dns_records]

			except dns.resolver.NoAnswer:
				# If no answer is found, return an empty list
				return []

			except dns.resolver.NXDOMAIN:
				# If no DNS record is found, return an empty list
				return []

			except dns.resolver.LifetimeTimeout:
				# If DNS query times out, wait for a delay and retry
				time.sleep(delay)

		# If all retries fail, return an empty list
		return []

	def set_domain(self):
		"""
		Extract and set the domain from the URL.

		Raises:
			ValueError: If the URL format is invalid.
		"""
		# Parse the URL to extract the network location (netloc)
		parsed_url = urlparse(self.url)
		# Check if the netloc is present in the parsed URL
		if parsed_url.netloc:
			# Set the domain using the netloc
			self.domain = parsed_url.netloc

			# Remove "www." prefix if it exists
			if self.domain.startswith("www."):
				self.domain = self.domain[4:]
		else:
			# Raise a ValueError if the URL format is invalid
			raise ValueError("Invalid URL format")

	def get_scripts(self):
		"""
		Extract script URLs from the parsed HTML of the web page.

		Returns:
			list: A list of script URLs.
		"""
		return [
			script['src']
			for script in self.parsed_html.findAll('script', src=True)
		]

	def fetch_script(self, url):
		"""
		Fetch the content of a script from the given URL.

		Args:
			url (str): The URL of the script.

		Returns:
			list: A list of script content chunks.
		"""
		# Adjust the script URL if it's a relative path
		script_url = url if url.startswith(
			('http://', 'https://')
		) else urljoin(self.url, url)

		try:
			# Send a GET request to fetch the script content
			response = requests.get(script_url)
			response.raise_for_status()  # Check for request errors
			# Split the content into chunks of 3000 characters for performance.
			content = response.text
			return [content[i:i + 3000] for i in range(0, len(content), 3000)]

		except requests.RequestException as e:
			# Log the error if fetching the script fails
			logger.error(f"Failed to fetch {url}: {e}")
			return []

	def load_scripts(self, script_urls):
		"""
		Load the content of multiple scripts concurrently.

		Args:
			script_urls (list): A list of script URLs.

		Returns:
			list: A list containing the content of all scripts.
		"""
		scripts_content = []
		with ThreadPoolExecutor(max_workers=10) as executor:
			# Submit script fetching tasks to the ThreadPoolExecutor
			futures = {
				executor.submit(self.fetch_script, url): url
				for url in script_urls
			}
			# Iterate through completed futures
			for future in as_completed(futures):
				result = future.result()
				if result:
					scripts_content.extend(result)

		return scripts_content

	def get_cookies(self):
		"""
		Extract cookies from the current session.

		Returns:
			dict: A dictionary containing cookie name-value pairs.
		"""
		# Extract cookies as a dictionary with lowercase keys
		return {
			cookie['name'].lower(): cookie['value']
			for cookie in self.driver.get_cookies()
		}

	def get_meta(self):
		"""
		Extract meta tags from the parsed HTML of the web page.

		Returns:
			dict: A dictionary containing meta tag name-content pairs.
		"""
		# Extract meta tags as a dictionary with lowercase names
		return {
			meta['name'].lower(): meta['content']
			for meta in self.parsed_html.findAll(
				'meta', attrs=dict(name=True, content=True))
		}
	
	def select(self, selector):
		"""
		Execute a CSS select and return results as dictionaries.

		Args:
			selector (str): CSS selector string.

		Returns:
			list: A list of dictionaries representing selected elements.
		"""
		try:
			# Execute CSS select and retrieve selected elements
			selected_elements = self.parsed_html.select(selector)
			# Iterate through selected elements and construct dictionaries
			return [{
				"name": item.name,                   # Element tag name
				"attrs": dict(item.attrs),           # Element attributes as dictionary
				"inner_html": item.decode_contents() # Inner HTML content
			} for item in selected_elements]

		except Exception:
			# Return an empty list if an error occurs during selection
			return []
