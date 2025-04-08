import frappe
from frappe.website.website_generator import WebsiteGenerator 
import qrcode  
import os
from frappe.utils.file_manager import save_file 
import urllib.parse

class CommunityPoll(WebsiteGenerator):

    def is_published(self):
        frappe.throw("hrllo")
        return self.status in ["Open", "Reopen"]
    
    website = frappe._dict(
        template="templates/generators/community_poll.html",  
        page_title_field="title",
    )

    def get_context(self, context):
        context.name = self.name
        context.poll_status = self.status
        context.title = self.title or self.name

        questions = self.questions
        quest_param = frappe.form_dict.get("quest")
        current_index = 0

        if quest_param:
            decoded_quest = urllib.parse.unquote(quest_param).strip()
            for i, q in enumerate(questions):
                if q.question.strip() == decoded_quest:
                    current_index = i
                    break
                
        current_question_text = questions[current_index].question.strip()
        current_question = frappe.get_doc("Poll Question", {"question": current_question_text})
        context.current_question = current_question
        context.options = current_question.options
        context.is_optional = questions[current_index].optional

        if self.show_voting_result:
            context.show_result = True
        else:
            context.show_result = False

        context.show_result = self.show_voting_result

         # For "Next" button logic
        if current_index + 1 < len(questions):
            next_question_text = urllib.parse.quote(questions[current_index + 1].question.strip())
            context.next_question_url = f"?quest={next_question_text}"
        else:
            context.next_question_url = None

        return context

    def after_insert(self):
        self.generate_qr_code()
        route_path = self.name
        frappe.db.set_value(self.doctype, self.name, "route", route_path)
        
    def generate_qr_code(self):
        if not self.get("questions"):
            return

        first_question_text = self.questions[0].question.strip()
        print("\n\n\n")
        print(first_question_text)

        # URL encode the question text
        question_slug = urllib.parse.quote(first_question_text)
        url_path = f"/{self.name}?quest={question_slug}"

        # Generate QR code
        qr = qrcode.make(frappe.utils.get_url() + url_path) 
        file_path = f"/tmp/{self.name}_qr.png"
        qr.save(file_path)

        # Save to Attach field
        with open(file_path, "rb") as f:
            saved_file = save_file(f"{self.name}-QR.png", f.read(), self.doctype, self.name, is_private=False)
            self.qr_code = saved_file.file_url
            frappe.db.set_value(self.doctype, self.name, "quest_qr", saved_file.file_url)


@frappe.whitelist()
def cast_vote(poll_id, qst_id, option_name):
    print("\n\n\n")
    print(poll_id)
    print(qst_id,)
    print(option_name)

    user = frappe.session.user
    if user == "Guest":
        frappe.throw("You must be logged in to vote.")

    # Check if already voted
    existing_vote = frappe.get_value("Poll Vote", {
        "poll": poll_id,
        "quest_id": qst_id,
        "user": user
    }, "name")

    if existing_vote:
        frappe.throw("You have already voted in this poll question.")

    # Load the question document
    poll_question = frappe.get_doc("Poll Question", qst_id)
    print("qstn: get: ",poll_question)

    selected_option = None
    total_votes = 0

    # Update vote count
    for option in poll_question.options:
        if option.option == option_name:
            option.vote_count += 1
            option.modified = True  # Mark the option as changed
            selected_option = option

    total_votes = sum([opt.vote_count for opt in poll_question.options])

    for option in poll_question.options:
        option.percent = round((option.vote_count / total_votes) * 100, 2) if total_votes else 0

    # Save the updated poll question
    poll_question.total_vote_count = total_votes
    poll_question.save()

    # Create a vote record
    vote_doc = frappe.get_doc({
        "doctype": "Poll Vote",
        "poll": poll_id,
        "quest_id": qst_id,
        "option": option_name,
        "user": user
    })
    vote_doc.insert(ignore_permissions=True)


    poll = frappe.get_doc("Community Poll", poll_id)

    # Step 2: Loop through questions to find the index of the current one
    questions = poll.questions
    current_index = next((i for i, q in enumerate(questions) if q.question == qst_id), None)

    # Step 3: Get the next question, if exists
    next_question_name = None
    if current_index is not None and current_index + 1 < len(questions):
        next_question_name = questions[current_index + 1].question

    print("Next question:", next_question_name)

    return {
        "VoteMsg": "Thank you for voting!",
        "selected_option": {
            "option": selected_option.option,
            "vote_count": selected_option.vote_count,
            "percent": selected_option.percent
        },
        "total_votes": total_votes,
        "next_question": next_question_name  # None if no more questions
    }