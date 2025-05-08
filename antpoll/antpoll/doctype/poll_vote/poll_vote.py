# Copyright (c) 2025, anthertech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import time


class PollVote(Document):

	def after_insert(self):

		if not self.is_correct:
			return

		def time_to_seconds(t):
			"""Convert datetime.time or string 'HH:MM:SS' to total seconds."""
			if isinstance(t, time):
				return t.hour * 3600 + t.minute * 60 + t.second
			try:
				h, m, s = map(float, str(t).split(':'))
				return int(h) * 3600 + int(m) * 60 + int(s)
			except Exception as e:
				frappe.log_error(f"Invalid vote_time format: {t} ({e})")
				return float('inf')  # treat invalid times as latest

		current_vote_seconds = time_to_seconds(self.vote_time)

		# Get all other correct votes for the same poll and question
		all_votes = frappe.get_all("Poll Vote",
			filters={
				"poll": self.poll,
				"quest_id": self.quest_id,
				"is_correct": 1
			},
			fields=["name", "vote_time"]
		)

		is_first = True
		for vote in all_votes:
			if vote["name"] == self.name:
				continue

			existing_seconds = time_to_seconds(vote["vote_time"])
			if existing_seconds < current_vote_seconds:
				is_first = False
				break

		if is_first:
			frappe.db.set_value("Poll Vote", self.name, "is_first", 1)
