# Copyright (c) 2025, anthertech and contributors
# For license information, please see license.txt


from datetime import timedelta
import frappe
from frappe.website.website_generator import WebsiteGenerator 
import qrcode  
import os
from frappe.utils.file_manager import save_file 
from frappe.utils import now_datetime
from datetime import datetime, date
from collections import defaultdict


import urllib.parse
from urllib.parse import quote

class CommunityPoll(WebsiteGenerator):

    website = frappe._dict(
        template="templates/generators/community_poll.html",
        # template="templates/generators/polls.html",
        condition_field = "is_published",
        page_title_field = "title",
    )

    def get_context(self, context):
        if frappe.session.user != "Guest":
            context.userr = "True"
        else:
            context.userr = "False"

        context.name = self.name
        context.poll_status = self.status
        context.title = self.name

        context.pollqr = self.quest_qr
        context.has_qr_shown = self.has_shown_qr

        # context.leaderboard = self.show_leaderboard

        settings = frappe.get_doc("Poll Settings", "Poll Settings") 
        if settings.default_leaderboard:
            context.show_leaderboard = "true"
            
        context.instructions = settings.instructions
        context.poll_start_duration = settings.poll_start_duration
        poll_start_duration = frappe.db.get_single_value("Poll Settings", "poll_start_duration")  # returns timedelta

        poll_start_seconds = int(poll_start_duration.total_seconds())
        context.poll_start_seconds = poll_start_seconds
            
        # questions = self.questions
        questions = self.questions or []
        if not questions:
            frappe.throw("No questions available for this poll.")
        quest_param = frappe.form_dict.get("quest")
        current_index = 0

        if quest_param:
            decoded_quest = urllib.parse.unquote(quest_param).strip()
            for i, q in enumerate(questions):
                if q.question.strip() == decoded_quest:
                    current_index = i
                    break
                
        current_question_text = questions[current_index].question.strip()
        current_question = frappe.get_doc("Poll Question", {"name": current_question_text})
        context.current_question = current_question       

        for qrs in self.questions:
            if qrs.question == quest_param:
                
                context.qrcodes = qrs.qr
                context.qstn_status = qrs.qst_status
                context.viewss = qrs.total_view
                context.workflow_phase = qrs.workflow_phase
                context.is_shown_leaderboard = int(qrs.is_shown_leaderboard)
        
                print("workflow phase")
                print(qrs.workflow_phase)

        context.options = current_question.options
        # context.show_result = self.show_voting_result

        # 1. Get vote logs for this question in this poll
        votes = frappe.get_all("Poll Vote", 
            filters={
                "poll": self.name,
                "quest_id": current_question.name
            },
            fields=["option"]
        )

        # 2. Count total votes
        total_votes = len(votes)

        # 3. Prepare a dictionary to count votes per option
        option_vote_counts = {}
        for vote in votes:
            opt = vote.option
            option_vote_counts[opt] = option_vote_counts.get(opt, 0) + 1

        # 4. Now get all options from the Poll Question
        options_list = []
        for opt in current_question.options:
            opt_name = opt.option
            vote_count = option_vote_counts.get(opt_name, 0)
            percent = (vote_count / total_votes * 100) if total_votes > 0 else 0

            options_list.append({
                "option": opt_name,
                "percent": round(percent, 2),
                "votes": vote_count
            })

        # 5. Send to frontend
        context.optionsss = options_list

        print(options_list)

        for op in current_question.options:
            if op.is_correct == 1:
                context.answer = op.option
        
        user_logged_in = frappe.session.user != "Guest"
        if user_logged_in:
            context.base_template = "templates/web.html"
        else:
            context.base_template = "templates/no_login.html"
            form_path = "/join-community/new"
            context.web_form_url = frappe.utils.get_url() + form_path \
                + "?redirect-to=" + urllib.parse.quote(f"/{self.name}?quest={current_question}")

        # For "Next" button logic
        if current_index + 1 < len(questions):
            next_question_text = urllib.parse.quote(questions[current_index + 1].question.strip())
            context.next_question_url = f"?quest={next_question_text}"
        else:
            context.next_question_url = None
            

        user = frappe.session.user  # Current logged-in user
        
        roles = frappe.get_roles(user)
        context.roles = roles  
        context.user = user
        if "Poll Admin" in roles:
            context.is_poll_admin = "True"
            print("yessss")

        #     # Get current user's vote
        user_vote = frappe.get_all("Poll Vote",
            filters={
                "poll": self.name,
                "quest_id": current_question.name,
                "user": frappe.session.user  # current logged-in user
            },
            fields=["option"]
        )

        # Get the correct answer
        correct_answer = None
        for op in current_question.options:
            if op.is_correct == 1:
                correct_answer = op.option
                context.answer = correct_answer  # already added by you

        # Add user-specific result context
        if user_vote:
            user_selected = user_vote[0].option
            context.user_selected = user_selected

            if user_selected == correct_answer:
                context.user_result_msg = "Correct answer!"
                context.user_result_status = "correct"
            else:
                context.user_result_msg = "Incorrect answer"
                context.user_result_status = "incorrect"
        else:
            context.user_result_msg = "You did not select any option."
            context.user_result_status = "no_vote"


        # Get today's date range
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())

        # Fetch all energy point logs from today
        logs = frappe.get_all(
            "Energy Point Log",
            filters={"creation": ["between", [today_start, today_end]],"reference_doctype":"Poll Vote"},
            fields=["user", "points"],
        )

        user_points = defaultdict(int)
        for log in logs:
            user_points[log.user] += log.points

        # Sort users by points descending
        sorted_leaderboard = sorted(user_points.items(), key=lambda x: x[1], reverse=True)

        # Get current session user
        session_user = user

        # Determine position
        position = next((idx + 1 for idx, (user, _) in enumerate(sorted_leaderboard) if user == session_user), None)
        user_total_points = user_points.get(session_user, 0)

        # Get poll status
        context.user_total_points = user_total_points
        context.position =  position
        context.sorted_leaderboard = sorted_leaderboard

        if current_index + 1 < len(questions):
            next_question_name = questions[current_index + 1].question.strip()
            context.next_question_name = next_question_name
        else:
            context.next_question_name = None

            
        context.no_cache = 1
        return context

    def after_insert(self):
        self.generate_qr_codes()
        route_path = self.name
        frappe.db.set_value(self.doctype, self.name, "route", route_path)

    def before_save(self):
        self.generate_qr_codes()

    def validate(self):
        if self.questions:
            question_texts = [] 
            for i, question in enumerate(self.questions):
                question_text = question.question.strip()
                if question_text in question_texts:
                    frappe.throw("This question has already been added")
                question_texts.append(question_text)

    
    def generate_qr_codes(self):
        if not self.get("questions"):
            return

        first_question_text = self.questions[0].question.strip()

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

    # def generate_qr_codes(self):
    #     if not self.get("questions"):
    #         return
        
    #     base_url = frappe.utils.get_url()
    #     tmp_dir  = frappe.get_site_path("private", "qr_temp")
    #     os.makedirs(tmp_dir, exist_ok=True)

    #     for idx, q in enumerate(self.questions):
    #         # Prepare the URL
    #         question_text = q.question.strip()
    #         slug          = urllib.parse.quote(question_text)
    #         url_path      = f"/{self.name}?quest={slug}"
    #         full_url      = base_url + url_path

    #         # Check QR image
    #         if q.get("qr"):
    #             continue

    #         # Gnerate QR
    #         qr_img    = qrcode.make(full_url)
    #         filename  = f"{self.name}_Q{idx+1}.png"
    #         file_path = os.path.join(tmp_dir, filename)
    #         qr_img.save(file_path)

    #         # Read and save via positional args
    #         with open(file_path, "rb") as f:
    #             filedata = f.read()
    #             saved = save_file(
    #                 filename,        # fname
    #                 filedata,        # content
    #                 self.doctype,    # dt
    #                 self.name,       # dn
    #                 None,            # folder
    #                 False            # is_private
    #             )

    #         # Store the QR code URL in the child row
    #         q.db_set("qr", saved.file_url, update_modified=False)

    #     # Update the parent’s modified timestamp so the parent doc registers a change
    #     frappe.db.set_value(self.doctype, self.name, "modified", frappe.utils.now())
        


@frappe.whitelist(allow_guest=True)
def get_total_views(q_name,poll_id):
    print("\n\n\nview count method called\n\n")
    poll_doc = frappe.get_doc("Community Poll", poll_id)
    for qrs in poll_doc.questions:
        if qrs.question == q_name:
            total_views = qrs.total_view
            print(":::::",total_views,"::::::::::")
            return total_views if total_views else 0

@frappe.whitelist()
def has_user_voted(poll_id, qst_id, user):
    print("\n\n\n, checking user is voted or not::\n")
    vote = frappe.get_value("Poll Vote", {
        "poll": poll_id,
        "quest_id": qst_id,
        "user": user
    }, "name")
    print(bool(vote),"\n\n")
    return {"has_voted": bool(vote)}


@frappe.whitelist()
def cast_vote(poll_id, qst_id, option_name):
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
    iscorrect = None

    for option in poll_question.options:
        if option.option == option_name:
            iscorrect = option.is_correct

    # update vote count in poll
    poll = frappe.get_doc("Community Poll", poll_id)
    for quest in poll.questions:
        if quest.question == qst_id:
            quest.total_vote_count = (quest.total_vote_count or 0) + 1
    poll.save()

    # poll vote log creation
    vote_doc = frappe.get_doc({
        "doctype": "Poll Vote",
        "poll": poll_id,
        "quest_id": qst_id,
        "option": option_name,
        "is_correct": iscorrect,
        "user": user
    })
    vote_doc.insert(ignore_permissions=True)

    questions = poll.questions
    current_index = next((i for i, q in enumerate(questions) if q.question == qst_id), None)

    # Step 3: Get the next question, if exists
    next_question_name = None
    if current_index is not None and current_index + 1 < len(questions):
        next_question_name = questions[current_index + 1].question

    return {
        "VoteMsg": "Thanks for participating!",
        "next_question": next_question_name  # None if no more questions
    }

@frappe.whitelist()
def question_result_show(poll_id,qst_id):
   
    poll = frappe.get_doc("Community Poll", poll_id)
    print(poll)
    for i in poll.questions:
        if i.question == qst_id:
            print(qst_id)
            i.qst_status = "Closed"
            i.save()

    frappe.publish_realtime('result_publish_event', poll_id)
    return {"message": "success"}

@frappe.whitelist()
def track_poll_question_view(question_name,poll_id):
    user = frappe.session.user
    poll_doc = frappe.get_doc("Community Poll",poll_id)
    if poll_doc and user:
        if user != "Guest" and poll_doc.owner != user:
            if not frappe.db.exists("View Log", {"reference_doctype":"Poll Question","reference_name": question_name,"custom_poll_id":poll_id,"viewed_by": user}):
                doc = frappe.new_doc("View Log")
                doc.reference_doctype = "Poll Question"
                doc.reference_name = question_name
                doc.custom_poll_id = poll_id
                doc.viewed_by = user
                doc.save(ignore_permissions=True)
                frappe.db.commit()

                for question in poll_doc.questions:
                    if question.question == question_name:
                        new_view = (question.total_view or 0) + 1
                        break
                    
                frappe.db.set_value("Question Items",question.name,"total_view",new_view)
                frappe.publish_realtime("view_count_updated",message={"question": question_name, "poll_id": poll_id})
                print("called")
                return {"question": question_name, "poll_id": poll_id}


@frappe.whitelist()
def get_option_vote_data(poll_id, question_name):
    # Get total votes for this poll and question
    total_votes = frappe.db.count('Poll Vote', {
        'poll': poll_id,
        'quest_id': question_name
    })

    if total_votes == 0:
        return []

    # Get each option's vote count
    vote_data = frappe.db.get_all('Poll Vote',
        fields=['option', 'count(*) as count'],
        filters={
            'poll': poll_id,
            'quest_id': question_name
        },
        group_by='option'
    )

    # Calculate percentages
    result = []
    for opt in vote_data:
        percent = round((opt['count'] / total_votes) * 100, 2)
        result.append({
            'option': opt['option'],
            'count': opt['count'],
            'percent': percent
        })

    return result




@frappe.whitelist()
def send_custom_notification(message):
    
    # Broadcast message to all connected clients
    frappe.publish_realtime('my_custom_event', message)
    return {"status": "success"}

@frappe.whitelist()
def send_next_question_url(next_url):
    # Broadcast the next URL to all connected clients
    frappe.publish_realtime('goto_next_question_event', next_url)
    return {"status": "success", "url": next_url}

@frappe.whitelist()
def  send_cur_question_url(cur_url,poll_id):
    frappe.publish_realtime('goto_cur_question_event', cur_url)
    frappe.db.set_value("Community Poll", poll_id, "has_shown_qr", True)
    return {"status": "success", "url": cur_url}


########## for qstn timer ###########
@frappe.whitelist()
def update_question_workflow(qst_id, poll_id):
    qst_id = qst_id
    print("\n\nmethod called!!")
    poll = frappe.get_doc("Community Poll", poll_id)
    print(qst_id)
    # Find the specific child row
    for q in poll.questions:
        print("\n\n\n\n",q.question, "==" ,qst_id,"\n\n\n\n")
        if q.question == qst_id:

            print("qstn find!!!\n\n")
            if q.workflow_phase == "Pending":
                q.workflow_phase = "Has Started"
                
    poll.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.publish_realtime('start_qstn_timer', qst_id)
    return {"status": "updated", "question": q.question}


           
########### qstn status updated after qstn timeout ###########
@frappe.whitelist()
def qstn_timeout_update(poll_id,qst_id):
    print("\n\n uuuu")
    poll = frappe.get_doc("Community Poll", poll_id)
    for i in poll.questions:
        if i.question == qst_id:
            if i.workflow_phase == "Has Started":
                i.workflow_phase = "Time Out"
                i.qst_status = "Closed"
    poll.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "successfully updated time out"}
    
########## qstn leaderboard status update ##############

@frappe.whitelist()
def leaderboard_status_update(poll_id,qst_id):
    poll = frappe.get_doc("Community Poll", poll_id)
    for i in poll.questions:
        if i.question == qst_id:
            i.is_shown_leaderboard = 1
    poll.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.publish_realtime('update_qstn_leaderboard', qst_id)
    return {"status": "successfully updated leaderboard status"}