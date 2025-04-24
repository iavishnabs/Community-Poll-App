# Copyright (c) 2025, avishna and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.auth import LoginManager
import time

class CommunityPollUsers(Document):
	def validate(self):
		if frappe.db.exists("User", {"email": self.email}):
			frappe.throw("A user with this email already exists")

		if len(self.password) < 8:
			frappe.throw("Password must be at least 8 characters long")

	def after_insert(self):
		# user_doc.set_password(self.password)
		if not frappe.db.exists('User',self.email):
			doc=frappe.new_doc('User')
			doc.update({
				"email":self.email,
				# "time_zone":time_zone,
				"first_name":self.first_name,
				"mobile_no":self.mobile_number,
				"new_password":self.password,
				"send_welcome_email":1,
				"role_profile_name":"Poll User",
				"user_type":"System User"

			})
			roles = frappe.get_roles("Poll User")
			for role in roles:
				doc.append("roles", {"role": role})
			
			doc.save(ignore_permissions=True)

			login_manager = LoginManager()
			login_manager.authenticate(self.email, self.password)
			login_manager.post_login()


