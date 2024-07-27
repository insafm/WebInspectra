from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

class SeleniumUtilities:

	def __init__(self, headless=True,  use_undetected=True, **kwargs):
		chrome_options = Options()
		chrome_options.add_argument("--no-sandbox")
		chrome_options.add_argument("--disable-gpu")
		chrome_options.add_argument('--disable-dev-shm-usage')
		chrome_options.add_argument("--disable-blink-features=AutomationControlled")
		if headless:
			chrome_options.add_argument('--headless')

		if use_undetected:
			self.driver = uc.Chrome(
				options=chrome_options,
				headless=headless,
				# use_subprocess=True,
				keep_alive=False
			)
		else:
			self.driver = webdriver.Chrome(
				options=chrome_options,
				keep_alive=False,
				**kwargs
			)

		user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
		self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
			"userAgent": user_agent
		})

	def load_url(self, url):
		self.driver.get(url)
		data = {
			"title": self.driver.title
		}
		return data

	def quit(self):
		self.driver.quit()
	
	def get_headers(self):
		response_headers = {}
		try:
			# Get the response headers
			headers = self.driver.execute_script(
				"var req = new XMLHttpRequest();req.open('GET', document.location, false);req.send(null);return req.getAllResponseHeaders()"
			).splitlines()

			if headers:
				for header in headers:
					# Split at the first occurrence of ': '
					parts = header.split(': ', 1)
					# Ensure it's a valid header line
					if len(parts) == 2:
						header_name, header_value = parts
						response_headers[header_name.lower()] = header_value
		except JavascriptException:
			pass
		
		return response_headers

	def get_cookies(self):
		# Get cookies
		cookies = self.driver.get_cookies()

		# Extract cookies as dictionary with key-value pairs
		cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
		return cookies_dict

	def get_css_rules(self):
		css_rules = []
		try:
			# Execute JavaScript to retrieve all CSS rules
			css_rules = self.driver.execute_script("""
				var styleSheets = document.styleSheets;
				var cssRules = [];
				for (var i = 0; i < styleSheets.length; i++) {
					var styleSheet = styleSheets[i];
					var rules = styleSheet.cssRules;
					for (var j = 0; j < rules.length; j++) {
						cssRules.push(rules[j].cssText);
					}
				}
				return cssRules;
			""")
		except JavascriptException:
			pass

		return css_rules

	def get_xhrs(self):
		xhr_data = []
		try:
			# Execute JavaScript to retrieve XHR URLs, method types, and data
			xhr_data = self.driver.execute_script("""
				var xhrData = [];
				var performanceEntries = performance.getEntriesByType("resource");
				performanceEntries.forEach(function(entry) {
					if (entry.initiatorType === "xmlhttprequest" || entry.initiatorType === "fetch") {
						xhrData.push({
							url: entry.name,
							method: 'GET', // Default method is GET, if method type is not available
						});
					}
				});

				var xhrs = window.XMLHttpRequest ? window.XMLHttpRequest.prototype : {};
				var originalOpen = xhrs.open;
				xhrs.open = function(method, url) {
					xhrData.push({
						url: url,
						method: method
					});
					return originalOpen.apply(this, arguments);
				};
				
				return xhrData;
			""")
		except JavascriptException:
			pass

		return xhr_data
