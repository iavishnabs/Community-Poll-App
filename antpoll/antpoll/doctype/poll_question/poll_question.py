# Copyright (c) 2025, anthertech and contributors
# For license information, please see license.txt

import frappe
import re

from frappe.model.document import Document


class PollQuestion(Document):

	def autoname(doc, method=None):
		name = doc.question or ""
		# Remove double quotes and special characters except letters, numbers, and spaces
		name = re.sub(r'[^\w\s]', '', name)
		doc.name = name
	
	def validate(self):
		# Validate options
		correct_options = [opt for opt in self.options if opt.is_correct]

		if not correct_options:
			frappe.throw("You must select at least one correct option.")
		if len(correct_options) > 1:
			frappe.throw("Only one option can be marked as correct.")

