"""
ABUTAHUNT — Bilingual Strings (English + Amharic)
Prepared by Abuta (@abuta_art)
"""

STRINGS = {
    "en": {
        "welcome": (
            "🚀 <b>Welcome to ABUTAHUNT</b>\n\n"
            "Complete simple Telegram tasks and earn real ETB rewards.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "main_menu": "🏠 Main Menu",
        "earn_btn": "🎯 Earn 50 ETB",
        "balance_btn": "💰 My Balance",
        "tasks_btn": "📋 My Tasks",
        "invite_btn": "👥 Invite Friends",
        "withdraw_btn": "💳 Withdraw",
        "leaderboard_btn": "🏆 Leaderboard",
        "stats_btn": "📊 My Statistics",
        "help_btn": "❓ Help",
        "support_btn": "🆘 Support",
        "back_btn": "⬅️ Back",
        "verify_btn": "✅ Verify",
        "cancel_btn": "❌ Cancel",
        "confirm_btn": "✅ Confirm",
        "refresh_btn": "🔄 Refresh",

        "campaign_header": (
            "🎯 <b>50 ETB CAMPAIGN</b>\n\n"
            "Complete the required Telegram tasks below.\n\n"
        ),
        "task_incomplete": "🔴",
        "task_complete": "🟢",
        "task_join": "Join",
        "reward_label": "💰 Reward: <b>{amount} ETB</b>",
        "campaign_status_active": "🔥 Campaign Status: ACTIVE",
        "campaign_stats": (
            "👥 Participants: <b>{participants:,}</b>\n"
            "🎁 Reward Pool: <b>{pool:,.0f} ETB</b>\n"
            "⏳ Remaining Claims: <b>{remaining:,}</b>\n"
            "{status}"
        ),

        "verify_checking": "⏳ Verifying your tasks, please wait...",
        "verify_success": (
            "🎉 <b>Congratulations!</b>\n\n"
            "You successfully completed today's campaign.\n"
            "💰 Reward: <b>{amount} ETB</b>\n"
            "📌 Status: <b>Pending verification/payment</b>\n\n"
            "Your reward will be processed by the admin."
        ),
        "verify_failed_channel": (
            "❌ <b>Verification Failed</b>\n\n"
            "You have not joined the required channel(s):\n"
            "{missing}\n\n"
            "Please join and press ✅ Verify again."
        ),
        "already_completed": "✅ You have already completed this campaign.",
        "suspended": "🚫 Your account has been suspended. Contact support.",

        "balance_header": (
            "💰 <b>My Balance</b>\n\n"
            "✅ Available: <b>{balance} ETB</b>\n"
            "⏳ Pending: <b>{pending} ETB</b>\n"
            "📈 Total Earned: <b>{total_earned} ETB</b>\n"
            "💸 Total Withdrawn: <b>{total_withdrawn} ETB</b>"
        ),

        "referral_header": (
            "👥 <b>Invite Friends & Earn</b>\n\n"
            "Share your unique link. Earn <b>{bonus} ETB</b> for every friend "
            "who completes a campaign!\n\n"
            "🔗 Your Link:\n<code>{link}</code>\n\n"
            "📊 Total Referrals: <b>{total}</b>\n"
            "✅ Qualified: <b>{qualified}</b>\n"
            "⏳ Pending: <b>{pending}</b>\n"
            "💰 Referral Earnings: <b>{earnings} ETB</b>\n"
            "📈 Conversion: <b>{rate}%</b>"
        ),
        "copy_link_btn": "📋 Copy Link",
        "share_btn": "📤 Share",

        "withdraw_header": (
            "💳 <b>Withdraw Funds</b>\n\n"
            "Available Balance: <b>{balance} ETB</b>\n"
            "Minimum Withdrawal: <b>{min_amount} ETB</b>\n\n"
            "Select a payment method:"
        ),
        "withdraw_enter_amount": "Enter the amount you wish to withdraw (ETB):",
        "withdraw_enter_info": "Enter your {method} account number/phone:",
        "withdraw_confirm": (
            "💸 <b>Withdrawal Request</b>\n\n"
            "Amount: <b>{amount} ETB</b>\n"
            "Method: <b>{method}</b>\n"
            "Account: <b>{info}</b>\n\n"
            "Confirm this withdrawal?"
        ),
        "withdraw_submitted": (
            "💸 <b>Withdrawal Request Submitted</b>\n\n"
            "Amount: <b>{amount} ETB</b>\n"
            "Method: <b>{method}</b>\n"
            "Status: ⏳ Processing\n\n"
            "You'll be notified when it's completed."
        ),
        "withdraw_insufficient": "❌ Insufficient balance. Available: <b>{balance} ETB</b>",
        "withdraw_below_min": "❌ Minimum withdrawal is <b>{min} ETB</b>",
        "withdraw_invalid_amount": "❌ Please enter a valid amount.",
        "withdraw_daily_limit": "❌ Daily withdrawal limit reached. Try again tomorrow.",

        "leaderboard_header": "🏆 <b>Leaderboard</b>",
        "top_earners": "💰 Top Earners",
        "top_referrers": "👥 Top Referrers",
        "most_active": "🔥 Most Active",
        "lb_daily": "Daily",
        "lb_weekly": "Weekly",
        "lb_monthly": "Monthly",
        "lb_all_time": "All Time",
        "lb_hidden": "🕶 Hidden",

        "stats_header": (
            "📊 <b>My Statistics</b>\n\n"
            "📅 Member Since: <b>{since}</b>\n"
            "🎯 Campaigns Completed: <b>{campaigns}</b>\n"
            "💰 Total Earned: <b>{earned} ETB</b>\n"
            "💸 Total Withdrawn: <b>{withdrawn} ETB</b>\n"
            "👥 Referrals: <b>{referrals}</b>\n"
            "🔥 Current Streak: <b>{streak} days</b>\n"
            "🏅 Badges: <b>{badges}</b>\n"
            "📊 Risk Level: <b>{risk}</b>"
        ),

        "help_text": (
            "❓ <b>Help & Guide</b>\n\n"
            "1️⃣ Press <b>🎯 Earn 50 ETB</b>\n"
            "2️⃣ Join all required channels\n"
            "3️⃣ Press <b>✅ Verify</b>\n"
            "4️⃣ Your reward will be approved\n"
            "5️⃣ Withdraw to Telebirr or bank\n\n"
            "📌 Each campaign can only be completed once.\n"
            "👥 Earn extra by referring friends.\n\n"
            "Need help? Press 🆘 Support"
        ),

        "support_enter_message": "Describe your issue and we'll respond shortly:",
        "support_submitted": "✅ Support ticket #{ticket_id} submitted. We'll reply soon.",
        "support_ticket_list": "📋 <b>Your Support Tickets</b>",

        "notif_task_completed": "✅ Task completed! Reward <b>{amount} ETB</b> is pending.",
        "notif_reward_approved": "🎉 Reward of <b>{amount} ETB</b> approved!",
        "notif_reward_rejected": "❌ Reward rejected. Reason: {reason}",
        "notif_payment_done": "💸 Payment of <b>{amount} ETB</b> completed!",
        "notif_referral_qualified": "👥 Your referral <b>{name}</b> qualified! +{bonus} ETB",
        "notif_new_campaign": "🚀 New campaign available! Earn <b>{amount} ETB</b>",

        "admin_panel": "👑 <b>Admin Panel</b>",
        "admin_campaigns_btn": "📢 Campaigns",
        "admin_users_btn": "👤 Users",
        "admin_payments_btn": "💸 Payments",
        "admin_broadcast_btn": "📡 Broadcast",
        "admin_stats_btn": "📊 Analytics",
        "admin_fraud_btn": "🚨 Fraud",
        "admin_settings_btn": "⚙️ Settings",

        "error_generic": "❌ Something went wrong. Please try again.",
        "error_not_admin": "⛔ Access denied.",
        "rate_limited": "⏳ Too many requests. Please wait a moment.",
        "fraud_blocked": "🚫 Your action was flagged. Contact support.",
    },

    "am": {
        "welcome": (
            "🚀 <b>እንኳን ወደ ABUTAHUNT መጡ</b>\n\n"
            "ቀላል የቴሌግራም ተግባራትን ያጠናቅቁ እና 真ተ ETB ሽልማት ያግኙ።\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "main_menu": "🏠 ዋና ምናሌ",
        "earn_btn": "🎯 50 ብር አግኝ",
        "balance_btn": "💰 ቀሪ ሂሳቤ",
        "tasks_btn": "📋 ተግባሮቼ",
        "invite_btn": "👥 ጓደኞች ጋብዝ",
        "withdraw_btn": "💳 ገንዘብ ወሰድ",
        "leaderboard_btn": "🏆 ሰንጠረዥ",
        "stats_btn": "📊 ስታቲስቲካ",
        "help_btn": "❓ እርዳታ",
        "support_btn": "🆘 ድጋፍ",
        "back_btn": "⬅️ ተመለስ",
        "verify_btn": "✅ አረጋግጥ",
        "cancel_btn": "❌ ሰርዝ",
        "confirm_btn": "✅ አረጋግጥ",
        "refresh_btn": "🔄 አድስ",

        "campaign_header": (
            "🎯 <b>50 ብር ዘመቻ</b>\n\n"
            "ከታች ያሉትን የቴሌግራም ተግባራት ያጠናቅቁ።\n\n"
        ),
        "task_incomplete": "🔴",
        "task_complete": "🟢",
        "task_join": "ይቀላቀሉ",
        "reward_label": "💰 ሽልማት: <b>{amount} ብር</b>",
        "campaign_status_active": "🔥 ዘመቻ ሁኔታ: ንቁ",
        "campaign_stats": (
            "👥 ተሳታፊዎች: <b>{participants:,}</b>\n"
            "🎁 የሽልማት ፈንድ: <b>{pool:,.0f} ብር</b>\n"
            "⏳ ቀሪ ጥያቄዎች: <b>{remaining:,}</b>\n"
            "{status}"
        ),

        "verify_checking": "⏳ ተግባሮቹን በማረጋገጥ ላይ፣ እባክዎ ይጠብቁ...",
        "verify_success": (
            "🎉 <b>እንኳን ደስ አለዎት!</b>\n\n"
            "የዛሬውን ዘመቻ በሙሉ አጠናቀዋል።\n"
            "💰 ሽልማት: <b>{amount} ብር</b>\n"
            "📌 ሁኔታ: <b>ጥብቅ ምርመራ/ክፍያ በሂደት ላይ</b>\n\n"
            "ሽልማቱ በአስተዳዳሪ ይሰራል።"
        ),
        "verify_failed_channel": (
            "❌ <b>ማረጋገጫ አልተሳካም</b>\n\n"
            "እነዚህን ቻናሎች አልተቀላቀሉም:\n"
            "{missing}\n\n"
            "እባክዎ ይቀላቀሉ እና ✅ አረጋግጥ ይጫኑ።"
        ),
        "already_completed": "✅ ይህን ዘመቻ አስቀድሞ አጠናቀዋል።",
        "suspended": "🚫 መለያዎ ታግዷል። ድጋፍን ያነጋግሩ።",

        "balance_header": (
            "💰 <b>ቀሪ ሂሳቤ</b>\n\n"
            "✅ ዝግጁ: <b>{balance} ብር</b>\n"
            "⏳ በሂደት: <b>{pending} ብር</b>\n"
            "📈 ጠቅላላ ያገኘሁ: <b>{total_earned} ብር</b>\n"
            "💸 ጠቅላላ የወሰድኩ: <b>{total_withdrawn} ብር</b>"
        ),

        "referral_header": (
            "👥 <b>ጓደኞችን ጋብዝ እና አትርፍ</b>\n\n"
            "ልዩ ሊንክህን አጋራ። ዘመቻ ላጠናቀቀ ጓደኛ <b>{bonus} ብር</b> አትርፍ!\n\n"
            "🔗 ሊንክህ:\n<code>{link}</code>\n\n"
            "📊 ጠቅላላ ጥሪዎች: <b>{total}</b>\n"
            "✅ ብቁ: <b>{qualified}</b>\n"
            "⏳ በሂደት: <b>{pending}</b>\n"
            "💰 ከጥሪ ያገኘሁ: <b>{earnings} ብር</b>\n"
            "📈 ሪፈራል: <b>{rate}%</b>"
        ),
        "copy_link_btn": "📋 ሊንክ ቅዳ",
        "share_btn": "📤 አጋራ",

        "withdraw_header": (
            "💳 <b>ገንዘብ ወሰድ</b>\n\n"
            "ዝግጁ ቀሪ: <b>{balance} ብር</b>\n"
            "ዝቅተኛ ማውጫ: <b>{min_amount} ብር</b>\n\n"
            "የክፍያ ዘዴ ይምረጡ:"
        ),
        "withdraw_enter_amount": "ማውጣት የሚፈልጉትን መጠን ያስገቡ (ብር):",
        "withdraw_enter_info": "የ{method} መለያ ቁጥርዎን/ስልክዎን ያስገቡ:",
        "withdraw_confirm": (
            "💸 <b>የማውጫ ጥያቄ</b>\n\n"
            "መጠን: <b>{amount} ብር</b>\n"
            "ዘዴ: <b>{method}</b>\n"
            "መለያ: <b>{info}</b>\n\n"
            "ይህን ማውጫ ያረጋግጡ?"
        ),
        "withdraw_submitted": (
            "💸 <b>ጥያቄ ተልኳል</b>\n\n"
            "መጠን: <b>{amount} ብር</b>\n"
            "ዘዴ: <b>{method}</b>\n"
            "ሁኔታ: ⏳ በሂደት ላይ\n\n"
            "ሲጠናቀቅ ይነገርዎታል።"
        ),
        "withdraw_insufficient": "❌ በቂ ቀሪ የለም። ዝግጁ: <b>{balance} ብር</b>",
        "withdraw_below_min": "❌ ዝቅተኛ ማውጫ <b>{min} ብር</b> ነው",
        "withdraw_invalid_amount": "❌ ትክክለኛ መጠን ያስገቡ።",
        "withdraw_daily_limit": "❌ የዕለት ሊሚት ደርሷል። ነገ ይሞክሩ።",

        "leaderboard_header": "🏆 <b>ሰንጠረዥ</b>",
        "top_earners": "💰 ከፍተኛ አርቃቂዎች",
        "top_referrers": "👥 ከፍተኛ ሪፈሮች",
        "most_active": "🔥 በጣም ንቁ",
        "lb_daily": "ዕለታዊ",
        "lb_weekly": "ሳምንታዊ",
        "lb_monthly": "ወርሃዊ",
        "lb_all_time": "ሁሌም",
        "lb_hidden": "🕶 ተደብቋል",

        "stats_header": (
            "📊 <b>ስታቲስቲካዬ</b>\n\n"
            "📅 አባል ከሆንኩ: <b>{since}</b>\n"
            "🎯 ያጠናቀቅኳቸው ዘመቻዎች: <b>{campaigns}</b>\n"
            "💰 ጠቅላላ ያገኘሁ: <b>{earned} ብር</b>\n"
            "💸 ጠቅላላ የወሰድኩ: <b>{withdrawn} ብር</b>\n"
            "👥 ጥሪዎች: <b>{referrals}</b>\n"
            "🔥 ተከታታይ ቀናት: <b>{streak}</b>\n"
            "🏅 ባጆች: <b>{badges}</b>\n"
            "📊 የወንጀለኛ ደረጃ: <b>{risk}</b>"
        ),

        "help_text": (
            "❓ <b>እርዳታ እና መመሪያ</b>\n\n"
            "1️⃣ <b>🎯 50 ብር አግኝ</b> ይጫኑ\n"
            "2️⃣ ሁሉም ቻናሎች ይቀላቀሉ\n"
            "3️⃣ <b>✅ አረጋግጥ</b> ይጫኑ\n"
            "4️⃣ ሽልማቱ ይፈቀዳል\n"
            "5️⃣ ወደ ቴሌብር ወይም ባንክ ያውጡ\n\n"
            "📌 እያንዳንዱ ዘመቻ አንድ ጊዜ ብቻ ይፈቀዳል።\n"
            "👥 ጓደኞችን በመጋበዝ ተጨማሪ አትርፉ።\n\n"
            "እርዳታ ይፈልጋሉ? 🆘 ድጋፍ ይጫኑ"
        ),

        "support_enter_message": "ችግርዎን ይግለጹ፣ በቅርቡ እንመልሳለን:",
        "support_submitted": "✅ የድጋፍ ጥያቄ #{ticket_id} ተልኳል።",
        "support_ticket_list": "📋 <b>የድጋፍ ጥያቄዎቼ</b>",

        "notif_task_completed": "✅ ተግባር ተጠናቀቀ! ሽልማት <b>{amount} ብር</b> በሂደት።",
        "notif_reward_approved": "🎉 <b>{amount} ብር</b> ሽልማት ተፈቀደ!",
        "notif_reward_rejected": "❌ ሽልማት ተቀባይነት አላገኘም። ምክንያት: {reason}",
        "notif_payment_done": "💸 <b>{amount} ብር</b> ክፍያ ተጠናቀቀ!",
        "notif_referral_qualified": "👥 ጥሪዎ <b>{name}</b> ብቁ ሆነ! +{bonus} ብር",
        "notif_new_campaign": "🚀 አዲስ ዘመቻ አለ! <b>{amount} ብር</b> አትርፉ",

        "admin_panel": "👑 <b>አስተዳዳሪ ፓነል</b>",
        "admin_campaigns_btn": "📢 ዘመቻዎች",
        "admin_users_btn": "👤 ተጠቃሚዎች",
        "admin_payments_btn": "💸 ክፍያዎች",
        "admin_broadcast_btn": "📡 ሁሉ ላክ",
        "admin_stats_btn": "📊 ትንተና",
        "admin_fraud_btn": "🚨 ወንጀል",
        "admin_settings_btn": "⚙️ ቅንብሮች",

        "error_generic": "❌ ችግር ተፈጥሯል። እንደገና ይሞክሩ።",
        "error_not_admin": "⛔ ፍቃድ የለዎትም።",
        "rate_limited": "⏳ ብዙ ጥያቄ። ጥቂት ይጠብቁ።",
        "fraud_blocked": "🚫 እርምጃዎ ምርመራ ይፈልጋል። ድጋፍ ያነጋግሩ።",
    }
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated string, fallback to English."""
    lang = lang if lang in STRINGS else "en"
    text = STRINGS[lang].get(key) or STRINGS["en"].get(key, f"[{key}]")
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
