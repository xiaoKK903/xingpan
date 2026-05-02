"""
商业化系统数据库迁移脚本
- VIP会员系统
- 虚拟礼物系统
- 付费报告系统
- 支付订单系统
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def create_vip_plans_table(cursor):
    if table_exists(cursor, "vip_plans"):
        print("✓ vip_plans 表已存在")
        return
    
    print("创建 vip_plans 表...")
    cursor.execute("""
        CREATE TABLE vip_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_type VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            original_price INTEGER,
            duration_days INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX idx_vip_plans_plan_type ON vip_plans (plan_type)")
    cursor.execute("CREATE INDEX idx_vip_plans_is_active ON vip_plans (is_active)")
    
    print("  插入默认VIP套餐数据...")
    cursor.execute("""
        INSERT INTO vip_plans (plan_type, name, description, price, original_price, duration_days, is_active, sort_order)
        VALUES 
        ('monthly', '星钻会员月卡', '开通星钻会员月卡，享受全部VIP特权，有效期30天', 1900, 2900, 30, 1, 1),
        ('yearly', '星钻会员年卡', '开通星钻会员年卡，享受全部VIP特权，有效期365天，比月卡省60元', 16800, 22800, 365, 1, 2)
    """)
    
    print("✓ vip_plans 表创建成功")


def create_vip_privileges_table(cursor):
    if table_exists(cursor, "vip_privileges"):
        print("✓ vip_privileges 表已存在")
        return
    
    print("创建 vip_privileges 表...")
    cursor.execute("""
        CREATE TABLE vip_privileges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            privilege_key VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            privilege_type VARCHAR(50) NOT NULL,
            value_data TEXT,
            icon VARCHAR(200),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX idx_vip_privileges_privilege_key ON vip_privileges (privilege_key)")
    cursor.execute("CREATE INDEX idx_vip_privileges_privilege_type ON vip_privileges (privilege_type)")
    
    print("  插入默认VIP特权数据...")
    privileges = [
        ('no_ads', '全站免广告', '全站所有页面无广告打扰，享受纯净体验', 'no_ads', '{"enabled": true}', '🛡️'),
        ('blind_box_extra', '盲盒额外抽取', '每日盲盒匹配次数+3，VIP用户每日可额外抽取3次', 'blind_box_extra', '{"extra_count": 3}', '🎁'),
        ('blind_box_discount', '盲盒折扣', '盲盒相关消费享受8折优惠', 'blind_box_discount', '{"discount_rate": 0.8}', '💰'),
        ('unlimited_synastry', '合盘无限制', '双人合盘计算无次数限制，普通用户每日限5次', 'unlimited_synastry', '{"unlimited": true}', '💕'),
        ('advanced_horoscope', '7天星运超前看', '可查看未来7天的详细运势预测，普通用户仅能查看当日', 'advanced_horoscope', '{"days_ahead": 7}', '🔮'),
        ('exclusive_skin', '专属皮肤挂件', '解锁VIP专属头像框、聊天气泡和个人主页皮肤', 'exclusive_skin', '{"skins": ["vip_frame", "vip_bubble", "vip_theme"]}', '✨'),
        ('social_weight', '社交加权推荐', '在社交匹配和推荐中获得更高权重，更容易被匹配到', 'social_weight', '{"weight_multiplier": 2.0}', '⭐'),
        ('free_reports', '每月免费报告', '每月可免费获取3份付费星盘报告', 'free_reports', '{"monthly_limit": 3}', '📄'),
    ]
    
    for p in privileges:
        cursor.execute("""
            INSERT INTO vip_privileges (privilege_key, name, description, privilege_type, value_data, icon)
            VALUES (?, ?, ?, ?, ?, ?)
        """, p)
    
    print("✓ vip_privileges 表创建成功")


def create_user_vips_table(cursor):
    if table_exists(cursor, "user_vips"):
        print("✓ user_vips 表已存在")
        return
    
    print("创建 user_vips 表...")
    cursor.execute("""
        CREATE TABLE user_vips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            is_vip BOOLEAN DEFAULT 0,
            plan_type VARCHAR(20),
            started_at TIMESTAMP,
            expires_at TIMESTAMP,
            total_subscriptions INTEGER DEFAULT 0,
            total_paid INTEGER DEFAULT 0,
            auto_renew_enabled BOOLEAN DEFAULT 0,
            last_renewed_at TIMESTAMP,
            monthly_free_reports_used INTEGER DEFAULT 0,
            monthly_free_reports_reset_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute("CREATE UNIQUE INDEX idx_user_vips_user_id ON user_vips (user_id)")
    cursor.execute("CREATE INDEX idx_user_vips_is_vip ON user_vips (is_vip)")
    cursor.execute("CREATE INDEX idx_user_vips_expires_at ON user_vips (expires_at)")
    
    print("✓ user_vips 表创建成功")


def create_vip_subscriptions_table(cursor):
    if table_exists(cursor, "vip_subscriptions"):
        print("✓ vip_subscriptions 表已存在")
        return
    
    print("创建 vip_subscriptions 表...")
    cursor.execute("""
        CREATE TABLE vip_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subscription_no VARCHAR(50) UNIQUE NOT NULL,
            plan_type VARCHAR(20) NOT NULL,
            price INTEGER NOT NULL,
            discount_amount INTEGER DEFAULT 0,
            duration_days INTEGER NOT NULL,
            started_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            payment_order_id INTEGER,
            status VARCHAR(20) DEFAULT 'active',
            is_auto_renew BOOLEAN DEFAULT 0,
            cancelled_at TIMESTAMP,
            cancel_reason VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (payment_order_id) REFERENCES payment_orders (id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_vip_subscriptions_user_id ON vip_subscriptions (user_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_vip_subscriptions_subscription_no ON vip_subscriptions (subscription_no)")
    cursor.execute("CREATE INDEX idx_vip_subscriptions_status ON vip_subscriptions (status)")
    cursor.execute("CREATE INDEX idx_vip_subscriptions_expires_at ON vip_subscriptions (expires_at)")
    cursor.execute("CREATE INDEX idx_vip_subscriptions_created_at ON vip_subscriptions (created_at)")
    
    print("✓ vip_subscriptions 表创建成功")


def create_gifts_table(cursor):
    if table_exists(cursor, "gifts"):
        print("✓ gifts 表已存在")
        return
    
    print("创建 gifts 表...")
    cursor.execute("""
        CREATE TABLE gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_key VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            gift_type VARCHAR(50) NOT NULL,
            price INTEGER NOT NULL,
            currency_type VARCHAR(20) DEFAULT 'stardust_point',
            rarity VARCHAR(20) DEFAULT 'common',
            animation_effect VARCHAR(200),
            icon_url VARCHAR(500),
            is_active BOOLEAN DEFAULT 1,
            is_limited BOOLEAN DEFAULT 0,
            stock_remaining INTEGER,
            available_from TIMESTAMP,
            available_until TIMESTAMP,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX idx_gifts_gift_key ON gifts (gift_key)")
    cursor.execute("CREATE INDEX idx_gifts_gift_type ON gifts (gift_type)")
    cursor.execute("CREATE INDEX idx_gifts_is_active ON gifts (is_active)")
    
    print("  插入默认礼物数据...")
    gifts = [
        ('stardust_bouquet', '星尘花束', '一束由星尘凝聚而成的美丽花束，散发着柔和的光芒，适合表达心意', 'stardust_bouquet', 50, 'stardust_point', 'common', 'flower_bloom', None, 1, 0, None, None, None, 1),
        ('energy_crystal', '能量水晶', '蕴含强大能量的神秘水晶，能够提升接收者的运势和能量', 'energy_crystal', 100, 'stardust_point', 'rare', 'crystal_glow', None, 1, 0, None, None, None, 2),
        ('limited_card_frame', '限定合盘卡牌框', '限时上架的珍稀合盘卡牌框，赠送后接收者可永久使用此卡牌框', 'limited_card_frame', 200, 'stardust_point', 'legendary', 'card_frame_shine', None, 1, 1, 1000, None, None, 3),
    ]
    
    for g in gifts:
        cursor.execute("""
            INSERT INTO gifts (gift_key, name, description, gift_type, price, currency_type, rarity, animation_effect, icon_url, is_active, is_limited, stock_remaining, available_from, available_until, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, g)
    
    print("✓ gifts 表创建成功")


def create_gift_transactions_table(cursor):
    if table_exists(cursor, "gift_transactions"):
        print("✓ gift_transactions 表已存在")
        return
    
    print("创建 gift_transactions 表...")
    cursor.execute("""
        CREATE TABLE gift_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_no VARCHAR(50) UNIQUE NOT NULL,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            gift_id INTEGER NOT NULL,
            gift_name VARCHAR(100) NOT NULL,
            gift_key VARCHAR(50) NOT NULL,
            quantity INTEGER DEFAULT 1,
            price_per_unit INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            currency_type VARCHAR(20) DEFAULT 'stardust_point',
            message VARCHAR(500),
            is_anonymous BOOLEAN DEFAULT 0,
            is_displayed BOOLEAN DEFAULT 0,
            displayed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id),
            FOREIGN KEY (gift_id) REFERENCES gifts (id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_gift_transactions_sender_id ON gift_transactions (sender_id)")
    cursor.execute("CREATE INDEX idx_gift_transactions_receiver_id ON gift_transactions (receiver_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_gift_transactions_transaction_no ON gift_transactions (transaction_no)")
    cursor.execute("CREATE INDEX idx_gift_transactions_created_at ON gift_transactions (created_at)")
    
    print("✓ gift_transactions 表创建成功")


def create_user_gift_displays_table(cursor):
    if table_exists(cursor, "user_gift_displays"):
        print("✓ user_gift_displays 表已存在")
        return
    
    print("创建 user_gift_displays 表...")
    cursor.execute("""
        CREATE TABLE user_gift_displays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gift_transaction_id INTEGER NOT NULL,
            gift_key VARCHAR(50) NOT NULL,
            gift_name VARCHAR(100) NOT NULL,
            sender_name VARCHAR(100),
            is_featured BOOLEAN DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (gift_transaction_id) REFERENCES gift_transactions (id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_user_gift_displays_user_id ON user_gift_displays (user_id)")
    cursor.execute("CREATE INDEX idx_user_gift_displays_gift_transaction_id ON user_gift_displays (gift_transaction_id)")
    
    print("✓ user_gift_displays 表创建成功")


def create_report_products_table(cursor):
    if table_exists(cursor, "report_products"):
        print("✓ report_products 表已存在")
        return
    
    print("创建 report_products 表...")
    cursor.execute("""
        CREATE TABLE report_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_key VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            product_type VARCHAR(50) NOT NULL,
            price INTEGER NOT NULL,
            original_price INTEGER,
            currency_type VARCHAR(20) DEFAULT 'stardust_point',
            report_template VARCHAR(100),
            sections_included TEXT,
            is_active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            icon_url VARCHAR(500),
            preview_image_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX idx_report_products_product_key ON report_products (product_key)")
    cursor.execute("CREATE INDEX idx_report_products_product_type ON report_products (product_type)")
    cursor.execute("CREATE INDEX idx_report_products_is_active ON report_products (is_active)")
    
    print("  插入默认报告产品数据...")
    products = [
        ('deep_single', '深度单人星盘解读', '包含完整的行星解读、相位分析、宫位详解、元素能量分析等深度内容，由AI进行专业解读', 'deep_single', 100, 150, 'stardust_point', 'deep_single', '["行星详细解读","相位深度分析","宫位完整解析","元素能量报告","人生主题解读","运势趋势预测"]', 1, 1, None, None),
        ('synastry_interpretation', '双人合盘深度解读', '深度分析两人的缘分指数、吸引点、挑战点、相处建议，包含详细的相位解读和关系动态', 'synastry_interpretation', 150, 200, 'stardust_point', 'synastry_deep', '["缘分指数分析","吸引点解读","挑战点分析","相位关系详解","相处建议指南","关系发展预测"]', 1, 2, None, None),
        ('yearly_prediction', '人生年度预测报告', '基于行运天象，预测未来一年的重要运势走向、关键时刻、机遇与挑战', 'yearly_prediction', 200, 300, 'stardust_point', 'yearly_prediction', '["年度整体运势","各领域详细预测","重要天象提醒","关键时刻日历","机遇与挑战分析","行动建议指南"]', 1, 3, None, None),
        ('group_energy', '群组能量分析报告', '分析团队、家庭、朋友圈等群组的能量互动模式、优势互补、潜在冲突和协作建议', 'group_energy', 250, 350, 'stardust_point', 'group_energy', '["群组整体能量","成员互动模式","优势互补分析","潜在冲突预警","协作效率评估","团队建设建议"]', 1, 4, None, None),
    ]
    
    for p in products:
        cursor.execute("""
            INSERT INTO report_products (product_key, name, description, product_type, price, original_price, currency_type, report_template, sections_included, is_active, sort_order, icon_url, preview_image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, p)
    
    print("✓ report_products 表创建成功")


def create_user_report_purchases_table(cursor):
    if table_exists(cursor, "user_report_purchases"):
        print("✓ user_report_purchases 表已存在")
        return
    
    print("创建 user_report_purchases 表...")
    cursor.execute("""
        CREATE TABLE user_report_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_no VARCHAR(50) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_key VARCHAR(50) NOT NULL,
            product_name VARCHAR(200) NOT NULL,
            price_paid INTEGER NOT NULL,
            currency_type VARCHAR(20) DEFAULT 'stardust_point',
            is_free_vip BOOLEAN DEFAULT 0,
            chart_id INTEGER,
            synastry_record_id INTEGER,
            group_matrix_id INTEGER,
            report_data TEXT,
            report_pdf_url VARCHAR(500),
            view_count INTEGER DEFAULT 0,
            last_viewed_at TIMESTAMP,
            payment_order_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES report_products (id),
            FOREIGN KEY (chart_id) REFERENCES charts (id),
            FOREIGN KEY (synastry_record_id) REFERENCES synastry_records (id),
            FOREIGN KEY (group_matrix_id) REFERENCES group_matrices (id),
            FOREIGN KEY (payment_order_id) REFERENCES payment_orders (id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_user_report_purchases_user_id ON user_report_purchases (user_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_user_report_purchases_purchase_no ON user_report_purchases (purchase_no)")
    cursor.execute("CREATE INDEX idx_user_report_purchases_product_key ON user_report_purchases (product_key)")
    cursor.execute("CREATE INDEX idx_user_report_purchases_created_at ON user_report_purchases (created_at)")
    
    print("✓ user_report_purchases 表创建成功")


def create_payment_orders_table(cursor):
    if table_exists(cursor, "payment_orders"):
        print("✓ payment_orders 表已存在")
        return
    
    print("创建 payment_orders 表...")
    cursor.execute("""
        CREATE TABLE payment_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no VARCHAR(50) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            payment_type VARCHAR(50) NOT NULL,
            related_type VARCHAR(50),
            related_id INTEGER,
            amount INTEGER NOT NULL,
            currency VARCHAR(10) DEFAULT 'CNY',
            discount_amount INTEGER DEFAULT 0,
            final_amount INTEGER NOT NULL,
            payment_method VARCHAR(20),
            payment_platform VARCHAR(20),
            platform_order_no VARCHAR(100),
            status VARCHAR(20) DEFAULT 'pending',
            paid_at TIMESTAMP,
            expired_at TIMESTAMP,
            callback_data TEXT,
            error_message VARCHAR(500),
            is_sandbox BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_payment_orders_user_id ON payment_orders (user_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_payment_orders_order_no ON payment_orders (order_no)")
    cursor.execute("CREATE INDEX idx_payment_orders_payment_type ON payment_orders (payment_type)")
    cursor.execute("CREATE INDEX idx_payment_orders_status ON payment_orders (status)")
    cursor.execute("CREATE INDEX idx_payment_orders_expired_at ON payment_orders (expired_at)")
    cursor.execute("CREATE INDEX idx_payment_orders_created_at ON payment_orders (created_at)")
    
    print("✓ payment_orders 表创建成功")


def create_payment_transactions_table(cursor):
    if table_exists(cursor, "payment_transactions"):
        print("✓ payment_transactions 表已存在")
        return
    
    print("创建 payment_transactions 表...")
    cursor.execute("""
        CREATE TABLE payment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_no VARCHAR(50) UNIQUE NOT NULL,
            order_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,
            amount INTEGER NOT NULL,
            currency VARCHAR(10) DEFAULT 'CNY',
            platform_transaction_no VARCHAR(100),
            status VARCHAR(20) DEFAULT 'pending',
            transaction_data TEXT,
            error_message VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES payment_orders (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_payment_transactions_order_id ON payment_transactions (order_id)")
    cursor.execute("CREATE INDEX idx_payment_transactions_user_id ON payment_transactions (user_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_payment_transactions_transaction_no ON payment_transactions (transaction_no)")
    cursor.execute("CREATE INDEX idx_payment_transactions_created_at ON payment_transactions (created_at)")
    
    print("✓ payment_transactions 表创建成功")


def main():
    print("=" * 60)
    print("商业化系统数据库迁移脚本")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    if not DB_PATH.exists():
        print(f"警告: 数据库文件不存在，将创建新数据库: {DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        print("-" * 40)
        print("VIP会员系统表")
        print("-" * 40)
        create_vip_plans_table(cursor)
        create_vip_privileges_table(cursor)
        create_user_vips_table(cursor)
        create_vip_subscriptions_table(cursor)
        print()
        
        print("-" * 40)
        print("虚拟礼物系统表")
        print("-" * 40)
        create_gifts_table(cursor)
        create_gift_transactions_table(cursor)
        create_user_gift_displays_table(cursor)
        print()
        
        print("-" * 40)
        print("付费报告系统表")
        print("-" * 40)
        create_report_products_table(cursor)
        create_user_report_purchases_table(cursor)
        print()
        
        print("-" * 40)
        print("支付订单系统表")
        print("-" * 40)
        create_payment_orders_table(cursor)
        create_payment_transactions_table(cursor)
        print()
        
        conn.commit()
        
        print("=" * 60)
        print("商业化系统数据库迁移完成！")
        print("=" * 60)
        print()
        print("已创建/更新的表:")
        print("  - vip_plans (VIP套餐)")
        print("  - vip_privileges (VIP特权)")
        print("  - user_vips (用户VIP状态)")
        print("  - vip_subscriptions (VIP订阅记录)")
        print("  - gifts (虚拟礼物)")
        print("  - gift_transactions (礼物赠送记录)")
        print("  - user_gift_displays (用户礼物展示)")
        print("  - report_products (报告产品)")
        print("  - user_report_purchases (用户报告购买)")
        print("  - payment_orders (支付订单)")
        print("  - payment_transactions (支付交易记录)")
        
    except Exception as e:
        conn.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
