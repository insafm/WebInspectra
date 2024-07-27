import json
import os
import re
import pkg_resources
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.common.exceptions import JavascriptException

from .webpage import WebPage
from .utils.signature_utils import Signature

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class WebInspectra:
	"""
	WebInspectra is a tool for detecting web pages to detect technologies used.
	
	Attributes:
		webpage (WebPage): The web page to be inspected.
		technologies (dict): A dictionary of technologies to detect.
		categories (list): A list of categories for the technologies.
		detected_technologies (dict): A dictionary of detected technologies.
	"""

	def __init__(self):
		"""
		Initializes a new instance of the WebInspectra class.
		"""
		self.webpage = None
		self.technologies = {}
		self.categories = None
		self.detected_technologies = {}

	def inspect(self, url, **options):
		"""
		Inspects a web page to detect technologies used.
		
		Args:
			url (str): The URL of the web page to inspect.
			**options: Additional options for the inspection.
				- by_category (bool): If True, format technologies by category.
		
		Returns:
			dict: A dictionary containing the detected technologies and their count.
		"""
		# Load the web page
		self.webpage = WebPage(url).load()
		# Get the technologies and categories to inspect
		self.technologies = self.get_technologies()
		self.categories = self.get_categories()

		# Use a thread pool to detect technologies concurrently
		with ThreadPoolExecutor(max_workers=10) as executor:
			futures = [
				executor.submit(
					self._detect_technology,
					Signature(name, signature_data)
				)
				for name, signature_data in self.technologies.items()
			]
			# Ensure all detection tasks have completed
			for future in futures:
				future.result()

		self.webpage.driver.quit()

		# Exclude incompatible technologies from the detected list
		self._exclude_incompatible_technologies()
		# Update the details of the detected technologies
		self._update_detected_technology_details()

		# Format the detected technologies based on the provided options
		if options.get("by_category", False):
			formatted_technologies = self._format_detected_technology_by_category()
		else:
			formatted_technologies = self._format_detected_technology()

		# Return the result
		return {
			'technologies': formatted_technologies,
			'count': len(self.detected_technologies),
		}
	
	def get_technologies(self):
		"""
		Retrieves the technologies to be detected from JSON files in the data folder.

		Returns:
			dict: A dictionary of technologies and their signatures.
		"""
		# Get the path to the data folder inside the package
		data_folder_path = pkg_resources.resource_filename(
			__name__, "data/technologies")

		technologies = {}
		try:
			# Loop through all files in the data folder
			for filename in os.listdir(data_folder_path):
				if filename.endswith(".json"):
					# Construct the full file path
					file_path = os.path.join(data_folder_path, filename)
					# Read the content of each JSON file
					with open(file_path, "r", encoding="utf-8") as file:
						json_data = json.load(file)
					# Merge the content into the combined technologies dictionary
					technologies.update(json_data)
		except Exception as e:
			# Log exceptions (e.g., file not found, JSON decoding errors)
			logger.error(f"Error loading technologies: {e}")

		return technologies

	def get_categories(self):
		"""
		Retrieves the categories for the detected technologies from a JSON file.

		Returns:
			dict: A dictionary of categories.
		"""
		try:
			# Load the category content from the categories.json file
			category_data = pkg_resources.resource_string(
				__name__, "data/categories.json")
			# Parse the JSON data
			categories = json.loads(category_data)
			return categories
		except Exception as e:
			# Log exceptions (e.g., file not found, JSON decoding errors)
			logger.error(f"Error loading categories: {e}")
			return {}
	
	def _detect_technology(self, signature):
		"""
		Determine whether the web page matches the technology signature.

		Args:
			signature (Signature): The signature of the technology to detect.
		"""
		# Main detection loop with parallel processing
		with ThreadPoolExecutor(max_workers=10) as executor:
			futures = []
			
			# Base detection
			for type, patterns in signature.patterns.items():
				compare_value = getattr(self.webpage, type, None)
				futures.append(executor.submit(self._base_detect, signature, type, patterns, compare_value))

			# DOM detection
			for pattern_object in signature.dom_patterns:
				futures.append(executor.submit(self._dom_detect, signature, pattern_object))

			# JS detection
			for js, patterns in signature.js_patterns.items():
				futures.append(executor.submit(self._js_detect, signature, js, patterns))

			# Wait for detection tasks to complete
			for future in as_completed(futures):
				# If a technology is detected, break the loop
				if future.result():
					break
	
	def _base_detect(self, signature, type, patterns, compare_value):
		"""
		Detects a technology based on basic patterns.

		Args:
			signature (Signature): The signature of the technology.
			type (str): The type of pattern (e.g., "headers", "html").
			patterns (dict): Patterns to match against.
			compare_value (str/dict/list): Value(s) to compare against the patterns.

		Returns:
			bool: True if a technology is detected, False otherwise.
		"""
		for key, pattern_list in patterns.items():
			# Handle string comparison
			if isinstance(compare_value, str):
				for pattern in pattern_list:
					if pattern.regex.search(compare_value):
						self._detected(
							signature.name, type, pattern, key, compare_value)
						return True

			# Handle dictionary comparison
			elif isinstance(compare_value, dict):
				compare_key_values = compare_value.get(key, [])
				if isinstance(compare_key_values, str):
					compare_key_values = [compare_key_values]

				for pattern in pattern_list:
					matched_value = next(
						(val for val in compare_key_values if pattern.regex.search(val)), None)
					if matched_value:
						self._detected(
							signature.name, type, pattern, key, matched_value)
						return True

			# Handle list comparison
			elif isinstance(compare_value, list):
				for pattern in pattern_list:
					matched_value = next(
						(val for val in compare_value if val and pattern.regex.search(val)), None)
					if matched_value:
						self._detected(
							signature.name, type, pattern, key, matched_value)
						return True

		return False
	
	def _dom_detect(self, signature, pattern_object):
		"""
		Detects a technology based on DOM patterns.

		Args:
			signature (Signature): The signature of the technology.
			pattern_object (dict): The DOM pattern object.

		Returns:
			bool: True if a technology is detected, False otherwise.
		"""
		# Check if DOM element exists
		if "exists" in pattern_object and pattern_object["exists"]:
			for patterns in pattern_object["exists"]:
				for pattern in patterns:
					if self.webpage.select(pattern.string):
						self._detected(signature.name, "dom", pattern, "exists")
						return True

		# Check if text matches within DOM elements
		if "text" in pattern_object and pattern_object["text"]:
			for patterns in pattern_object["text"]:
				for pattern in patterns:
					for item in self.webpage.select(pattern.string):
						if pattern.regex.search(item.inner_html):
							self._detected(signature.name, "dom", pattern, "text")
							return True

		# Check if specified attributes exist and match patterns within DOM elements
		if "attribute" in pattern_object and pattern_object["attribute"]:
			for pattern in pattern_object["attribute"]["exists"]:
				for attrname, attr_patterns in pattern_object["attribute"]["attributes"].items():
					for attr_patterns_items in attr_patterns:
						for attr_pattern in attr_patterns_items:
							for item in self.webpage.select(pattern.string):
								compare_key_values = item.get("attrs").get(attrname, [])
								compare_key_values = [compare_key_values] if isinstance(compare_key_values, str) else compare_key_values
								for compare_key_value in compare_key_values:
									if compare_key_value and attr_pattern.regex.search(compare_key_value):
										self._detected(signature.name, "dom", attr_pattern, "attribute")
										return True
		return False
	
	def _js_detect(self, signature, js, patterns):
		"""
		Detects a technology based on JavaScript patterns.

		Args:
			signature (Signature): The signature of the technology.
			js (str): The JavaScript code to execute.
			patterns (list): List of patterns to match against.

		Returns:
			bool: True if a technology is detected, False otherwise.
		"""
		# Initialize content
		_content = ""
		try:
			# Execute JavaScript code
			if "-" in js:
				js = f"(window||global)['{js}']"
			_content = str(self.webpage.driver.execute_script(f"return {js}"))
		except JavascriptException as e:
			# Handle JavaScript exception (e.g., circular reference)
			if "circular reference" in str(e):
				_content = "Error occurred, but success."

		# Iterate over patterns and check if content matches
		for pattern in patterns:
			if _content and _content != "None":
				self._detected(signature.name, "js", pattern, js, _content)
				return True
		return False

	def _detected(self, name, type, pattern, key=None, compare_value=None):
		"""
		Handles the detection of a technology.

		Args:
			name (str): The name of the detected technology.
			type (str): The type of detection (e.g., "dom", "js").
			pattern (Pattern): The pattern that triggered the detection.
			key (str): The key related to the detection (optional).
			compare_value (str): The value compared against the pattern (optional).

		Returns:
			bool: Always returns True.
		"""
		# Initialize detected technologies if not present
		if name not in self.detected_technologies:
			self.detected_technologies[name] = {}
			self.detected_technologies[name]["confidence"] = {}
			self.detected_technologies[name]["versions"] = []

		# Update confidence level
		confidence_key = f"{type} {key} {pattern.string}"
		self.detected_technologies[name]["confidence"][confidence_key] = pattern.confidence

		# Detect version number
		self._detect_version(name, pattern, compare_value)

		# Detect implied technologies
		self._detect_depended_technologies(name, "implies")

		# Detect required technologies
		self._detect_depended_technologies(name, "requires")

		return True

	def _detect_version(self, name, pattern, compare_value):
		"""
		Detects the version number of a detected technology.

		Args:
			name (str): The name of the detected technology.
			pattern (Pattern): The pattern used for version detection.
			compare_value (str): The value compared against the pattern.

		Returns:
			None
		"""
		# Check if the pattern has a version
		if pattern.version:
			# Find all matches of the pattern in the compare value
			all_matches = re.findall(pattern.regex, compare_value)
			# Iterate over each match
			for matches in all_matches:
				# Get the version pattern
				version = pattern.version
				# Ensure matches is a tuple
				matches = (matches,) if isinstance(matches, str) else matches

				# Iterate over each match and replace back references in the version pattern
				for index, match in enumerate(matches, start=1):
					back_ref = f'\\{index}'
					ternary_pattern = re.compile(f'\\\\{index}\\?([^:]+):(.*)$', re.I)
					ternary_match = ternary_pattern.search(version)

					# Handle ternary expressions in the version pattern
					if ternary_match:
						true_part, false_part = ternary_match.groups()
						replacement = true_part if match else false_part
						version = version.replace(ternary_match.group(0), replacement)

					# Replace back references with their respective matches
					version = version.replace(back_ref, match)

				# Check if the version is valid and add it to the detected technology's versions list
				if version and version not in self.detected_technologies[name]["versions"] and self.is_valid_version(version):
					self.detected_technologies[name]["versions"].append(version)

	def is_valid_version(self, version):
		"""
		Checks if a version string is valid.

		Args:
			version (str): The version string to validate.

		Returns:
			bool: True if the version string is valid, False otherwise.
		"""
		# Define a regular expression pattern for valid version strings
		pattern = re.compile(r'^\d+(\.\d+)*$')
		# Check if the version string matches the pattern
		return bool(pattern.match(version))

	def _detect_depended_technologies(self, tech_name, type="implies"):
		"""
		Detects implied or required technologies based on the provided type.

		Args:
			tech_name (str): The name of the technology.
			type (str): The type of dependency (e.g., "implies", "requires"). Defaults to "implies".

		Returns:
			None
		"""
		# Get implied or required technologies
		implied_techs = self.technologies[tech_name].get(type)
		implied_techs = [implied_techs] if isinstance(implied_techs, str) else implied_techs
		
		# Regular expression pattern to extract confidence information
		confidence_regexp = re.compile(r"(.+)\\;confidence:(\d+)")

		# Iterate over each implied or required technology
		for implied in implied_techs or []:
			# Extract technology name and confidence level
			confidence = 100
			confidence_check = confidence_regexp.search(implied)
			if confidence_check:
				implied, confidence = confidence_check.groups()

			# Set confidence key
			confidence_key = f"{type} {tech_name}"

			# If no doubts exist, add the technology with full confidence
			if 'confidence' not in implied:
				self.detected_technologies[implied] = {}
				self.detected_technologies[implied]["versions"] = []
				self.detected_technologies[implied]["confidence"] = {}
				self.detected_technologies[implied]["confidence"][confidence_key] = confidence
			# If some doubts exist (confidence level >= 50), add the technology with the given confidence level
			else:
				if int(confidence) >= 50:
					self.detected_technologies[implied] = {}
					self.detected_technologies[implied]["versions"] = []
					self.detected_technologies[implied]["confidence"] = {}
					self.detected_technologies[implied]["confidence"][confidence_key] = int(confidence)
	
	def _exclude_incompatible_technologies(self):
		"""
		Exclude incompatible technologies from `detected_technologies`.
		"""
		# Create a set to store technologies to exclude
		exclusions = set()

		# Collect all exclusions from the detected technologies
		for tech in self.detected_technologies:
			excludes = self.technologies.get(tech, {}).get("excludes")
			if excludes:
				# Convert single exclusion string to list
				if isinstance(excludes, str):
					excludes = [excludes]
				# Check if any confidence level for the exclusion technology is 100 in detected technologies
				for exclude in excludes:
					if not any(conf == 100 for conf in self.detected_technologies.get(exclude, {}).get('confidence', {}).values()):
						exclusions.add(exclude)

		# Remove the excluded technologies from detected_technologies
		self.detected_technologies = {
			tech: values for tech, values in self.detected_technologies.items()
			if tech not in exclusions
		}

	def _update_detected_technology_details(self):
		"""
		Update details of detected technologies based on attributes.

		Updates attributes like category, description, etc. for each detected technology.
		"""
		# Define attributes to update for each detected technology
		attributes = [
			"cats", "description", "cpe", "website", "pricing",
			("oss", False), ("saas", False),
			# TODO: Implement icon as data
			# ("icon", False)
		]

		# Iterate over each detected technology
		for tech in self.detected_technologies:
			# Update attributes for the detected technology
			for attr in attributes:
				# Check if the attribute is a tuple with a default value
				if isinstance(attr, tuple):
					key, default = attr
				else:
					key, default = attr, None
				# Update the attribute with the corresponding value from the technologies data
				self.detected_technologies[tech][key] = self.technologies.get(tech, {}).get(key, default)

	def _format_detected_technology_by_category(self):
		"""
		Format detected technologies by category.

		Categorizes detected technologies based on their category IDs and creates a dictionary
		where each category contains a list of technologies with their details.

		Returns:
			dict: Dictionary containing categorized technologies.
		"""
		# Create a dictionary to hold categorized technologies
		categorized_technologies = {}

		# Iterate over each detected technology
		for tech_name, tech_info in self.detected_technologies.items():
			# Iterate over each category ID of the technology
			for cat_id in tech_info.get("cats", []):
				# Get category information
				category = self.categories.get(str(cat_id))
				if category:
					cat_name = category["name"]
					# If category does not exist in the categorized technologies dictionary, add it
					if cat_name not in categorized_technologies:
						categorized_technologies[cat_name] = {
							"priority": category["priority"],
							"technologies": []
						}
					# Append technology details to the list of technologies in the category
					categorized_technologies[cat_name]["technologies"].append({
						"name": tech_name,
						"description": tech_info.get("description"),
						"versions": tech_info.get("versions"),
						"cpe": tech_info.get("cpe"),
						"website": tech_info.get("website"),
						"pricing": tech_info.get("pricing"),
						"oss": tech_info.get("oss"),
						"saas": tech_info.get("saas"),
						"icon": tech_info.get("icon"),
						"confidence": tech_info.get("confidence"),
					})

		# Sort categories by priority
		sorted_categories = dict(sorted(categorized_technologies.items(), key=lambda item: item[1]["priority"]))

		# Remove priority and flatten the list
		final_result = {}
		for cat_name, cat_info in sorted_categories.items():
			final_result[cat_name] = cat_info["technologies"]

		return final_result


	def _format_detected_technology(self):
		"""
		Format detected technologies.

		Formats the detected technologies dictionary by removing unnecessary keys,
		converting category IDs to category names, and ensuring the 'confidence' key
		is the last key in the dictionary.

		Returns:
			dict: Formatted dictionary containing detected technologies.
		"""
		# Iterate over each detected technology
		for tech_info in self.detected_technologies.values():
			# Remove the 'cats' key and convert category IDs to category names
			categories = tech_info.pop("cats", [])
			category_names = [
				self.categories[cat_id]["name"]
				for cat_id in map(str, categories) if cat_id in self.categories
			]
			tech_info["cats"] = category_names

			# Ensure the 'confidence' key is the last key in the dictionary
			tech_info["confidence"] = tech_info.pop("confidence")

		return self.detected_technologies
