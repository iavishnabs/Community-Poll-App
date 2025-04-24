// Copyright (c) 2025, avishna and contributors
// For license information, please see license.txt

frappe.ui.form.on("Community Poll", {
    // ID assign to route  
  
    refresh: function(frm) {
        
        // QR Code View
        if (frm.image_preview) {
            frm.image_preview.remove();
        }
        if (frm.doc.quest_qr && frm.doc.quest_qr.startsWith("/")) {
            let image_url = frappe.urllib.get_full_url(frm.doc.quest_qr);
            frm.image_preview = $('<div style="text-align:center; margin-top: 20px;">\
                <img src="' + image_url + '" style="max-width: 100%; height: auto; border: 1px solid #ddd; padding: 10px; border-radius: 6px;" />\
            </div>').insertAfter(frm.fields_dict.quest_qr.$wrapper);
        }

        // Check if the user has the role "Poll User"
        if (!frappe.user.has_role('Administrator') && frappe.user.has_role("Poll User")) {

            console.log("yes")
            console.log(frappe.session.user)
            console.log(frappe.user_roles)

            frm.set_df_property("title", "read_only", 1);
            frm.set_df_property("description", "read_only", 1);
            frm.set_df_property("status", "read_only", 1);
            frm.set_df_property("published", "read_only", 1);
            frm.set_df_property("end_date", "read_only", 1);

            frm.fields_dict.options.grid.wrapper.find('.grid-add-row').hide();
            frm.fields_dict.options.grid.wrapper.find('.grid-remove-rows').hide();
            frm.fields_dict.options.grid.wrapper.find('.grid-row-check').hide();
            frm.fields_dict.options.grid.wrapper.find('.grid-footer').hide();        
            frm.fields_dict.options.grid.df.read_only = 1;
            frm.fields_dict.options.grid.refresh();
        }


        // Dropdown: Poll Actions
        frm.add_custom_button('Launch', () => {
            frm.set_value('status', 'Open').then(() => {
                frm.save();
                
            });
        }, 'Poll Actions');

        frm.add_custom_button('Re-Launch', () => {
            frm.set_value('status', 'Reopen').then(() => {
                frm.save();
               
            });
        }, 'Poll Actions');
        frm.add_custom_button('Share QR', () => {
            const qrUrl = frm.doc.quest_qr;
        
            if (qrUrl) {
                window.open(qrUrl, '_blank');
            } else {
                frappe.msgprint(__('QR Code not available.'));
            }
        }, 'Poll Actions');
        
        frm.add_custom_button('Share the Poll', () => {
            frm.set_value('show_voting_result',1).then(() => {
                frm.save();
                
            });
        }, 'Poll Actions');
        frm.add_custom_button('End', () => {
            frm.set_value('status', 'Closed').then(() => {
                frm.save();
                
            });
        }, 'Poll Actions');

        const btn = frm.add_custom_button(__('Share Leaderboard'), function() {
            frm.set_value('show_leaderboard',1).then(() => {
                frm.save();
                
            });
        });
        
        // Style the button
        btn.css({
            'background-color': 'black',
            'color': '#FFFFFF',
            'border-color': 'white'
        });
        
        
    }
});
