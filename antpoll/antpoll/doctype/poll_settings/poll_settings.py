# Copyright (c) 2025, anthertech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PollSettings(Document):

	def before_save(self):
		if self.default_leaderboard:
			energy_point_rules = frappe.get_all("Energy Point Rule", filters={"reference_doctype": "Poll Vote", "enabled": 0})
			if energy_point_rules:
				self.energy_Point_Enable()
		else:
			self.disable_energy_point_rules()
	
		
	def energy_Point_Enable(self):
		energy_point_rules = frappe.get_all("Energy Point Rule", filters={"reference_doctype": "Poll Vote", "enabled": 0})
		for rule in energy_point_rules:
			frappe.db.set_value("Energy Point Rule", rule.name, "enabled", 1)
		frappe.db.commit()
	
	def disable_energy_point_rules(self):
		energy_point_rules = frappe.get_all("Energy Point Rule", filters={"reference_doctype": "Poll Vote", "enabled": 1})
		for rule in energy_point_rules:
			frappe.db.set_value("Energy Point Rule", rule.name, "enabled", 0)
				

				

