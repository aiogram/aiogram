# simplify-ephemeral-message-parameters

Replace the inlined ephemeral_message_parameters fill in Message reply_* shortcuts with an as_ephemeral_message_parameters() helper, and stop the fill leaking onto send methods that lack the field
