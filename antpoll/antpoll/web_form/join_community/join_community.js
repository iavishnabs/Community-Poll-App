// frappe.ready(function() {
// 	// existing bindings…
	
// 	// When the form is successfully submitted…
// 	frappe.web_form.on("success", () => {
// 		alert("yes")
// 	  // reload the parent page (where your iframe is embedded)
// 	  if (window.parent) {
// 		window.parent.location.reload();
// 	  }
// 	});
//   });
  
// frappe.ready(function() {
//     frappe.web_form.after_load = () => {
//         frappe.web_form.on('my_field_name', (field, value) => {
//             console.log(field, value)
//         })
//     }
// })