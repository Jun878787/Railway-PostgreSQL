"""
Keyboard layouts for the North Sea Financial Bot
Defines inline and reply keyboards for user interaction
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class BotKeyboards:
    @staticmethod
    def get_main_inline_keyboard():
        """Get main inline keyboard with updated layout"""
        keyboard = [
            [
                InlineKeyboardButton("💰金額異動", callback_data="money_actions"),
                InlineKeyboardButton("📊報表顯示", callback_data="report_display")
            ],
            [
                InlineKeyboardButton("🔣指令說明", callback_data="command_help"),
                InlineKeyboardButton("⚙️設置選單", callback_data="settings_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_currency_keyboard():
        """Get currency selection keyboard"""
        keyboard = [
            [
                KeyboardButton("💰TW"),
                KeyboardButton("💰CN")
            ],
            [
                KeyboardButton("💵公桶"),
                KeyboardButton("💵私人")
            ],
            [
                KeyboardButton("📝選單"),
                KeyboardButton("⚙️設置")
            ]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def get_personal_report_keyboard():
        """Get personal report keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊當月報表", callback_data="current_month"),
                InlineKeyboardButton("📚歷史報表", callback_data="history_personal")
            ],
            [
                InlineKeyboardButton("⬅️返回上一頁", callback_data="report_display")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_group_report_keyboard():
        """Get group report keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊當月報表", callback_data="group_current"),
                InlineKeyboardButton("📚歷史報表", callback_data="history_group")
            ],
            [
                InlineKeyboardButton("⬅️返回上一頁", callback_data="report_display")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_fleet_report_keyboard():
        """Get fleet report keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊當月報表", callback_data="fleet_current"),
                InlineKeyboardButton("📚歷史報表", callback_data="history_fleet")
            ],
            [
                InlineKeyboardButton("⬅️返回上一頁", callback_data="report_display")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_report_type_keyboard():
        """Get report type selection keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊當月報表", callback_data="current_month"),
                InlineKeyboardButton("📊上月報表", callback_data="previous_month")
            ],
            [
                InlineKeyboardButton("📊自訂月份", callback_data="custom_month"),
                InlineKeyboardButton("📊年度報表", callback_data="yearly_report")
            ],
            [
                InlineKeyboardButton("🔙返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_money_actions_keyboard():
        """Get money actions keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💰台幣", callback_data="currency_tw"),
                InlineKeyboardButton("💰人民幣", callback_data="currency_cn")
            ],
            [
                InlineKeyboardButton("💵公桶", callback_data="fund_public"),
                InlineKeyboardButton("💵私人", callback_data="fund_private")
            ],
            [
                InlineKeyboardButton("⬅️返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_report_display_keyboard():
        """Get report display keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊個人報表", callback_data="personal_report"),
                InlineKeyboardButton("📊組別報表", callback_data="group_report")
            ],
            [
                InlineKeyboardButton("📊車隊報表", callback_data="fleet_report"),
                InlineKeyboardButton("📚歷史報表", callback_data="history_report")
            ],
            [
                InlineKeyboardButton("💱匯率設定", callback_data="exchange_rate"),
                InlineKeyboardButton("⬅️返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_settings_menu_keyboard():
        """Get settings menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("👤使用者設定", callback_data="user_settings"),
                InlineKeyboardButton("💱匯率設定", callback_data="exchange_rate")
            ],
            [
                InlineKeyboardButton("👋歡迎詞設定", callback_data="welcome_settings"),
                InlineKeyboardButton("🚯清空報表", callback_data="clear_reports")
            ],
            [
                InlineKeyboardButton("⬅️返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_exchange_rate_keyboard():
        """Get exchange rate settings keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💱當前匯率資訊", callback_data="current_exchange_rates")
            ],
            [
                InlineKeyboardButton("💰設定台幣匯率", callback_data="set_tw_rate"),
                InlineKeyboardButton("💴設定人民幣匯率", callback_data="set_cn_rate")
            ],
            [
                InlineKeyboardButton("📅設定指定日期匯率", callback_data="set_date_rate")
            ],
            [
                InlineKeyboardButton("⬅️返回設置選單", callback_data="settings_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_command_help_keyboard():
        """Get command help keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("1️⃣群主", callback_data="help_owner"),
                InlineKeyboardButton("2️⃣管理員", callback_data="help_admin")
            ],
            [
                InlineKeyboardButton("3️⃣操作員", callback_data="help_operator")
            ],
            [
                InlineKeyboardButton("⬅️返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_clear_reports_keyboard():
        """Get clear reports keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("🚯清空個人報表", callback_data="clear_personal")
            ],
            [
                InlineKeyboardButton("🚯清空組別報表", callback_data="clear_group")
            ],
            [
                InlineKeyboardButton("🚯清空車隊總表", callback_data="clear_fleet")
            ],
            [
                InlineKeyboardButton("⬅️返回設置選單", callback_data="settings_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_user_settings_keyboard():
        """Get user settings keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("👤群主", callback_data="role_owner"),
                InlineKeyboardButton("👤管理員", callback_data="role_admin")
            ],
            [
                InlineKeyboardButton("👤操作員", callback_data="role_operator"),
                InlineKeyboardButton("⬅️返回設置選單", callback_data="settings_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_role_management_keyboard(role_type: str):
        """Get role management keyboard for specific role"""
        keyboard = [
            [
                InlineKeyboardButton(f"顯示目前{role_type}", callback_data=f"show_{role_type}"),
                InlineKeyboardButton(f"添加{role_type}", callback_data=f"add_{role_type}")
            ],
            [
                InlineKeyboardButton(f"取消{role_type}", callback_data=f"remove_{role_type}"),
                InlineKeyboardButton("⬅️返回用戶設定", callback_data="user_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_settings_keyboard():
        """Get legacy settings keyboard for compatibility"""
        return BotKeyboards.get_settings_menu_keyboard()
    
    @staticmethod
    def get_fund_management_keyboard():
        """Get fund management keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💵公桶餘額", callback_data="public_fund_balance"),
                InlineKeyboardButton("💰私人餘額", callback_data="private_fund_balance")
            ],
            [
                InlineKeyboardButton("➕增加公桶", callback_data="add_public_fund"),
                InlineKeyboardButton("➖減少公桶", callback_data="subtract_public_fund")
            ],
            [
                InlineKeyboardButton("➕增加私人", callback_data="add_private_fund"),
                InlineKeyboardButton("➖減少私人", callback_data="subtract_private_fund")
            ],
            [
                InlineKeyboardButton("🔙返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation_keyboard(action: str):
        """Get confirmation keyboard for dangerous operations"""
        keyboard = [
            [
                InlineKeyboardButton("✅確認", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌取消", callback_data="cancel_action")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_month_selection_keyboard():
        """Get month selection keyboard"""
        keyboard = []
        months = [
            ("1月", "01"), ("2月", "02"), ("3月", "03"), ("4月", "04"),
            ("5月", "05"), ("6月", "06"), ("7月", "07"), ("8月", "08"),
            ("9月", "09"), ("10月", "10"), ("11月", "11"), ("12月", "12")
        ]
        
        # Create rows of 3 months each
        for i in range(0, len(months), 3):
            row = []
            for j in range(3):
                if i + j < len(months):
                    month_name, month_num = months[i + j]
                    row.append(InlineKeyboardButton(month_name, callback_data=f"month_{month_num}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙返回", callback_data="report_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_keyboard():
        """Get admin-only keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("🔄重新啟動", callback_data="admin_restart"),
                InlineKeyboardButton("📊系統狀態", callback_data="admin_status")
            ],
            [
                InlineKeyboardButton("👥用戶管理", callback_data="admin_users"),
                InlineKeyboardButton("💾備份資料", callback_data="admin_backup")
            ],
            [
                InlineKeyboardButton("🔙返回主選單", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def remove_keyboard():
        """Remove reply keyboard"""
        from telegram import ReplyKeyboardRemove
        return ReplyKeyboardRemove()
