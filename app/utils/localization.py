"""Localization strings and translation management."""

from typing import Any, Dict

STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "start_welcome": (
            "This bot helps you create and conduct multiple-choice quizzes.\n\n"
            "Supported Scoring:\n"
            "🎯 NEET: +4 Correct, -1 Wrong\n"
            "🏥 NORCET: +1 Correct, -0.33 Wrong\n"
            "✅ Simple: +1 Correct, 0 Wrong\n"
            "⌛ Unattempted: 0"
        ),
        "btn_create_quiz": "Create New Quiz",
        "btn_my_quizzes": "My Quizzes",
        "btn_help": "Help",
        "btn_create_question": "Create a question",
        "btn_start_quiz": "Start Quiz",
        "btn_try_again": "Try Again",
        "btn_share_quiz": "Share Quiz",
        "btn_share_group": "Start quiz in group",
        "btn_back": "Back",
        "btn_cancel": "Cancel",
        "newquiz_unfinished": (
            "You have an unfinished quiz.\n"
            "Please finish creating it or send /cancel."
        ),
        "newquiz_prompt_title": (
            "Let's create a new quiz.\n"
            "First, send me the title of your quiz."
        ),
        "newquiz_prompt_description": (
            "Good. Now send me a description of your quiz.\n"
            "This is optional, you can /skip this step."
        ),
        "newquiz_first_question_prompt": (
            "Now send your first question – or some text or media that will be shown before it.\n\n"
            "Use the 'Create a question' button below to create a native quiz poll."
        ),
        "media_attached": (
            "📷 Media received! It will be attached to the next question you create.\n"
            "Now click 'Create a question' below to add the quiz poll."
        ),
        "question_added": (
            "Good. Your quiz '{title}' now has {count} questions.\n\n"
            "If you made a mistake in the question, you can go back by sending /undo.\n\n"
            "Now send the next question – or some text or media that will be shown before it.\n\n"
            "When done, simply send /done to finish creating the quiz."
        ),
        "undo_success": "Last question removed.",
        "undo_empty": "There is no question to undo.",
        "cancel_success": "Quiz discarded.",
        "cancel_no_active": "There is no active quiz.",
        "stop_no_active": "🤔 There is no quiz to stop.",
        "stop_success": "Quiz stopped.",
        "done_need_questions": "Please add at least one question before finishing.",
        "timer_prompt": "Please set a time limit for questions.",
        "shuffle_prompt": "Shuffle questions and answer options?",
        "quiz_summary": (
            "Quiz:\n"
            "{title}\n\n"
            "Questions:\n"
            "{count}\n\n"
            "Timer:\n"
            "{timer}\n\n"
            "Shuffle Questions:\n"
            "{shuffle_questions}\n\n"
            "Shuffle Options:\n"
            "{shuffle_options}\n\n"
            "Marking:\n"
            "+{correct_marks} / {wrong_marks} / {unattempted_marks}\n\n"
            "🏁 Quiz created successfully!\n\n"
            "Share link:\n"
            "{share_url}"
        ),
        "quizzes_header": "Your quizzes:\n",
        "quizzes_empty": "You haven't created any quizzes yet. Use /newquiz to create one!",
        "quizzes_item": (
            "{index}. {title}\n"
            "   {count} questions\n"
            "   {timer}\n"
            "   +{correct}/{wrong}\n"
            "   {status}\n"
        ),
        "help_text": (
            "What can this bot do?\n\n"
            "Create quizzes with multiple-choice questions.\n"
            "Add media before questions.\n"
            "Set question timers.\n"
            "Shuffle questions and answer options.\n"
            "Conduct quizzes.\n"
            "Calculate NEET-style scores.\n\n"
            "Scoring:\n\n"
            "Correct +4\n"
            "Wrong -1\n"
            "Unattempted 0"
        ),
        "lang_prompt": "Select your preferred language / अपनी भाषा चुनें:",
        "lang_changed": "Language set to English.",
        "participant_quiz_intro": (
            "*{title}*\n\n"
            "{description}\n\n"
            "Questions: {count}\n\n"
            "Marking:\n"
            "+{correct} correct\n"
            "{wrong} wrong\n"
            "{unattempted} unattempted\n"
            "Time per question: {timer}"
        ),
        "quiz_completed": (
            "🏁 *QUIZ COMPLETE*\n\n"
            "*{title}*\n\n"
            "Total Questions: {total}\n\n"
            "✅ Correct: {correct}\n"
            "❌ Wrong: {wrong}\n"
            "⌛ Unattempted: {unattempted}\n\n"
            "Correct Marks: +{correct_marks_total}\n"
            "Negative Marks: {wrong_marks_total}\n\n"
            "Final Score:\n"
            "*{score} / {max_score}*\n\n"
            "Percentage:\n"
            "*{percentage}%*"
        ),
        "question_timeout": "⌛ Time's up! Moving to the next question...",
        "not_authorized": "You are not authorized to perform this action.",
        "quiz_not_found": "Sorry, this quiz could not be found or is no longer available.",
        "help_text": (
            "ℹ️ *Need Help with QuizBot?*\n\n"
            "• Create a new quiz: /newquiz\n"
            "• View your quizzes: /quizzes\n"
            "• Undo last question: /undo\n"
            "• Cancel active draft: /cancel\n"
            "• Stop active quiz: /stop\n\n"
            "💬 *Contact Admin for Support:* @zx_era\n"
            "📢 *Official Updates Channel:* [SuperQuizUpdates](https://t.me/SuperQuizUpdates)"
        ),
        "support_text": (
            "📢 *QuizBot Support & Community*\n\n"
            "Join our official channel for latest updates, guides, and feature releases:\n"
            "👉 [https://t.me/SuperQuizUpdates](https://t.me/SuperQuizUpdates)\n\n"
            "For personal help or queries, message @zx_era"
        )
    },
    "hi": {
        "start_welcome": (
            "यह बॉट आपको बहुविकल्पीय क्विज़ बनाने और आयोजित करने में मदद करता है।\n\n"
            "NEET स्कोरिंग:\n"
            "✅ सही: +4\n"
            "❌ गलत: -1\n"
            "⌛ अनुत्तरित: 0"
        ),
        "btn_create_quiz": "नया क्विज़ बनाएं",
        "btn_my_quizzes": "मेरे क्विज़",
        "btn_help": "मदद",
        "btn_create_question": "प्रश्न बनाएं",
        "btn_start_quiz": "क्विज़ शुरू करें",
        "btn_try_again": "पुनः प्रयास करें",
        "btn_share_quiz": "क्विज़ साझा करें",
        "btn_share_group": "ग्रुप में शुरू करें",
        "btn_back": "पीछे",
        "btn_cancel": "रद्द करें",
        "newquiz_unfinished": (
            "आपके पास एक अधूरा क्विज़ है।\n"
            "कृपया इसे पूरा करें या /cancel भेजें।"
        ),
        "newquiz_prompt_title": (
            "आइए एक नया क्विज़ बनाएं।\n"
            "पहले मुझे अपने क्विज़ का शीर्षक भेजें।"
        ),
        "newquiz_prompt_description": (
            "अच्छा। अब अपने क्विज़ का विवरण भेजें।\n"
            "यह वैकल्पिक है, आप /skip भेज सकते हैं।"
        ),
        "undo_success": "अंतिम प्रश्न हटा दिया गया।",
        "undo_empty": "पूर्ववत करने के लिए कोई प्रश्न नहीं है।",
        "cancel_success": "क्विज़ रद्द कर दिया गया।",
        "cancel_no_active": "कोई सक्रिय क्विज़ नहीं है।",
        "stop_no_active": "🤔 रोकने के लिए कोई क्विज़ नहीं है।",
        "stop_success": "क्विज़ रोक दिया गया।"
    }
}


def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Get localized string by key and format with kwargs."""
    lang_dict = STRINGS.get(lang, STRINGS["en"])
    template = lang_dict.get(key, STRINGS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
