import re

class Pattern:
	def __init__(self, string, regex=None, version=None, confidence=None):
		"""
		Initialize a Pattern object with string, regex, version, and confidence.

		Args:
			string (str): The pattern string.
			regex (re.Pattern, optional): The compiled regular expression pattern. Defaults to None.
			version (str, optional): The version associated with the pattern. Defaults to None.
			confidence (int, optional): The confidence level of the pattern. Defaults to None.
		"""
		self.string = string
		# Use re.compile to create an empty regex object if regex is not provided
		self.regex = regex or re.compile('', 0)
		self.version = version
		# Convert confidence to int if provided, otherwise default to 100
		self.confidence = int(confidence) if confidence else 100

class Signature:
	def __init__(self, name, data):
		"""
		Initialize a Signature object with patterns data.

		Args:
			name (str): The name of the signature.
			data (dict): Dictionary containing patterns data.
		"""
		self.name = name
		self.data = data
		# Initialize patterns dictionaries using helper methods
		self.patterns = {
			'scriptSrc': self.set_list_patterns('scriptSrc'),
			'scripts': self.set_list_patterns('scripts'),
			'url': self.set_list_patterns('url'),
			'xhr': self.set_list_patterns('xhr'),
			'html': self.set_list_patterns('html'),
			'robots': self.set_list_patterns('robots'),
			'css': self.set_list_patterns('css'),
			'headers': self.set_dict_patterns('headers'),
			'dns': self.set_dict_patterns('dns'),
			'meta': self.set_dict_patterns('meta'),
			'cookies': self.set_dict_patterns('cookies'),
		}
		# Initialize JavaScript patterns dictionary
		self.js_patterns = self.set_dict_patterns('js')
		# Initialize DOM patterns list
		self.dom_patterns = self.set_dom_patterns('dom')

	def set_patterns(self, patterns_list):
		"""
		Convert a list of pattern strings into Pattern objects.

		Args:
			patterns_list (list or str): List of pattern strings or a single pattern string.

		Returns:
			list: List of Pattern objects representing the patterns.
		"""
		# Initialize an empty list to store pattern objects
		pattern_objects = []

		# Ensure patterns_list is a list
		if isinstance(patterns_list, str):
			patterns_list = [patterns_list]

		# Iterate over each pattern string and create a Pattern object
		for pattern_str in patterns_list:
			# Split the pattern string into individual expressions
			patterns = pattern_str.split('\\;')
			pattern_attrs = {}

			# Process each expression in the pattern string
			for index, expression in enumerate(patterns):
				if index == 0:
					# First expression is the main pattern string
					pattern_attrs['string'] = expression
					try:
						# Compile the regex pattern with case-insensitive matching
						pattern_attrs['regex'] = re.compile(expression, re.IGNORECASE)
					except re.error:
						# If regex compilation fails, use a pattern that never matches
						pattern_attrs['regex'] = re.compile(r'(?!x)x')
				else:
					# Subsequent expressions are additional attributes
					attr = expression.split(':')
					if len(attr) > 1:
						key = attr.pop(0)
						pattern_attrs[str(key)] = ':'.join(attr)
			
			# Create a Pattern object using the collected attributes
			pattern_objects.append(Pattern(**pattern_attrs))
		
		return pattern_objects

	def set_list_patterns(self, pattern_key):
		"""
		Convert a list of pattern strings into Pattern objects and organize them in a dictionary.

		Args:
			pattern_key (str): The key in the data dictionary.

		Returns:
			dict: Dictionary containing Pattern objects.
		"""
		# Initialize an empty dictionary to store pattern objects
		pattern_objects = {}

		# Retrieve patterns list from the data dictionary
		patterns = self.data.get(pattern_key)
		if patterns:
			# Convert patterns into Pattern objects
			pattern_objects["default_key"] = self.set_patterns(patterns)

		return pattern_objects

	def set_dict_patterns(self, pattern_key):
		"""
		Convert a dictionary of pattern strings into Pattern objects and organize them in a dictionary.

		Args:
			pattern_key (str): The key in the data dictionary.

		Returns:
			dict: Dictionary containing Pattern objects.
		"""
		# Initialize an empty dictionary to store pattern objects
		pattern_objects = {}

		# Retrieve patterns dictionary from the data dictionary
		patterns = self.data.get(pattern_key, {})

		# Iterate over the patterns dictionary
		for key, value in patterns.items():
			# Determine the key for the pattern_objects dictionary
			target_key = key if pattern_key == "js" else key.lower()
			# Convert patterns into Pattern objects and store them in the dictionary
			pattern_objects[target_key] = self.set_patterns(value)

		return pattern_objects

	def set_dom_patterns(self, pattern_key):
		"""
		Convert DOM-related pattern data into Pattern objects and organize them into a list of dictionaries.

		Args:
			pattern_key (str): The key in the data dictionary.

		Returns:
			list: List of dictionaries containing DOM-related Pattern objects.
		"""
		# Initialize an empty list to store pattern dictionaries
		pattern_object_list = []

		# Retrieve DOM-related patterns from data
		patterns = self.data.get(pattern_key)

		# If there are no patterns, return an empty list
		if not patterns:
			return pattern_object_list

		# If patterns is not a dictionary, convert it into a single pattern dictionary
		if not isinstance(patterns, dict):
			pattern_object = {}
			pattern_object["exists"] = []
			pattern_object["exists"].append(self.set_patterns(patterns))
			pattern_object_list.append(pattern_object)
		else:
			# Iterate over each CSS selector and its corresponding clauses in the patterns dictionary
			for cssselect, clause in patterns.items():
				pattern_object = {}
				pattern_object["exists"] = []
				pattern_object["text"] = []

				# Add patterns for existence checking
				if clause.get('exists') is not None:
					pattern_object["exists"].append(self.set_patterns(cssselect))

				# Add patterns for text matching
				if clause.get('text'):
					pattern_object["text"].append(self.set_patterns(clause['text']))

				# Add patterns for attribute matching
				if clause.get('attributes'):
					pattern_object["attribute"] = {}
					attributes = {}
					for _key, pattern in clause['attributes'].items():
						if _key not in attributes:
							attributes[_key] = []
						attributes[_key].append(self.set_patterns(pattern))

					pattern_object["attribute"]["exists"] = self.set_patterns(cssselect)
					pattern_object["attribute"]["attributes"] = attributes
				
				# Append the pattern dictionary to the list
				pattern_object_list.append(pattern_object)

		return pattern_object_list
