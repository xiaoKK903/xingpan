import sys
import os
import json
import io
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("PDF 导出 API 测试")
print("=" * 70)

BASE_URL = "http://localhost:8000/api"
TEST_USERNAME = "aaawhz3"
TEST_PASSWORD = "test123456"

test_output_dir = os.path.join(os.path.dirname(__file__), "api_test_output")
os.makedirs(test_output_dir, exist_ok=True)
print(f"\n📁 测试输出目录: {test_output_dir}")

session = requests.Session()

def print_response(resp, label="响应"):
    print(f"\n--- {label} ---")
    print(f"状态码: {resp.status_code}")
    print(f"响应头: {dict(resp.headers)}")
    try:
        data = resp.json()
        print(f"响应体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return data
    except:
        print(f"响应体大小: {len(resp.content)} 字节")
        return None

print("\n" + "-" * 70)
print("步骤 1: 测试公开接口（无需登录）")
print("-" * 70)

print("\n1.1 测试 /reports/templates 接口:")
try:
    resp = session.get(f"{BASE_URL}/reports/templates", timeout=10)
    data = print_response(resp, "获取报告模板列表")
    if resp.status_code == 200:
        print("✅ 报告模板接口正常")
    else:
        print(f"❌ 接口异常: {resp.status_code}")
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n" + "-" * 70)
print("步骤 2: 登录测试")
print("-" * 70)

print(f"\n2.1 登录用户: {TEST_USERNAME}")
login_data = {
    "username": TEST_USERNAME,
    "password": TEST_PASSWORD
}

try:
    resp = session.post(f"{BASE_URL}/users/login", data=login_data, timeout=10)
    data = print_response(resp, "登录响应")
    
    if resp.status_code == 200:
        print("✅ 登录成功")
    elif resp.status_code == 401:
        print("❌ 登录失败: 401 Unauthorized - 用户名或密码错误")
    elif resp.status_code == 404:
        print("❌ 登录接口不存在: 404 Not Found")
    else:
        print(f"❌ 登录失败: {resp.status_code}")
except Exception as e:
    print(f"❌ 登录请求失败: {e}")

print("\n" + "-" * 70)
print("步骤 3: 检查数据库中的星盘")
print("-" * 70)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Chart, User

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == TEST_USERNAME).first()
    if user:
        print(f"✅ 找到用户: {user.username} (ID: {user.id})")
        
        charts = db.query(Chart).filter(
            Chart.user_id == user.id,
            Chart.is_deleted == False
        ).all()
        
        print(f"\n用户星盘列表 ({len(charts)} 个):")
        for chart in charts:
            print(f"  - ID: {chart.id}, 名称: {chart.name}, 日期: {chart.birth_date}")
            
        if charts:
            test_chart = charts[0]
            print(f"\n✅ 使用测试星盘: ID={test_chart.id}, 名称={test_chart.name}")
        else:
            print("\n⚠️  用户没有保存的星盘，需要先创建一个")
    else:
        print(f"❌ 未找到用户: {TEST_USERNAME}")
finally:
    db.close()

print("\n" + "-" * 70)
print("步骤 4: 使用本地代码测试 PDF 生成（绕过登录）")
print("-" * 70)

from app.astro import calculate_chart, parse_birth_datetime
from app.report_generator import create_pdf_report, ReportTemplate
from app.services.chart_service import build_content_disposition_header
from app.interpretations import generate_full_interpretation

test_birth_data = {
    'name': '测试用户',
    'birth_date': '1990-01-15',
    'birth_time': '12:00',
    'latitude': 39.9042,
    'longitude': 116.4074,
    'birth_place': '北京',
    'house_system': 'placidus'
}

print(f"\n4.1 计算星盘...")
dt = parse_birth_datetime(test_birth_data['birth_date'], test_birth_data['birth_time'])
chart_data = calculate_chart(
    year=dt["year"],
    month=dt["month"],
    day=dt["day"],
    hour=dt["hour"],
    minute=dt["minute"],
    latitude=test_birth_data['latitude'],
    longitude=test_birth_data['longitude'],
    house_system=test_birth_data['house_system']
)
print(f"✅ 星盘计算完成，行星数: {len(chart_data.get('planets', []))}")

print(f"\n4.2 生成解读数据...")
interpretation = generate_full_interpretation(chart_data)
print(f"✅ 解读生成完成")
print(f"    - 太阳星座: {interpretation.get('basic_info', {}).get('sun_sign', '未知')}")
print(f"    - 月亮星座: {interpretation.get('basic_info', {}).get('moon_sign', '未知')}")

if 'basic_info' not in chart_data:
    chart_data['basic_info'] = {
        'input': {
            'name': test_birth_data['name'],
            'date': test_birth_data['birth_date'],
            'time': test_birth_data['birth_time'],
            'place': test_birth_data['birth_place'],
            'latitude': test_birth_data['latitude'],
            'longitude': test_birth_data['longitude']
        }
    }

print(f"\n4.3 生成简洁版 PDF...")
simple_pdf_path = os.path.join(test_output_dir, "api_test_simple.pdf")
pdf_buffer = create_pdf_report(chart_data, template=ReportTemplate.SIMPLE, output_path=simple_pdf_path)
simple_size = len(pdf_buffer.getvalue())
print(f"✅ 简洁版 PDF 生成成功")
print(f"    - 大小: {simple_size} 字节")
print(f"    - 路径: {simple_pdf_path}")
print(f"    - 文件存在: {os.path.exists(simple_pdf_path)}")

print(f"\n4.4 生成详细版 PDF...")
detailed_pdf_path = os.path.join(test_output_dir, "api_test_detailed.pdf")
pdf_buffer = create_pdf_report(chart_data, template=ReportTemplate.DETAILED, output_path=detailed_pdf_path)
detailed_size = len(pdf_buffer.getvalue())
print(f"✅ 详细版 PDF 生成成功")
print(f"    - 大小: {detailed_size} 字节")
print(f"    - 路径: {detailed_pdf_path}")
print(f"    - 文件存在: {os.path.exists(detailed_pdf_path)}")

print(f"\n4.5 测试 Content-Disposition 头部编码...")
test_filename = f"星盘解读报告_{test_birth_data['name']}_{test_birth_data['birth_date'].replace('-','')}_详细版.pdf"
header = build_content_disposition_header(test_filename)
print(f"    原始文件名: {test_filename}")
print(f"    响应头: {header}")

try:
    parts = header.split('; ')
    for part in parts:
        if part.startswith('filename='):
            value = part.split('=', 1)[1].strip('"')
            value.encode('latin-1')
            print("    ✅ filename= 部分可通过 latin-1 编码")
except UnicodeEncodeError as e:
    print(f"    ❌ 编码失败: {e}")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)

print(f"\n📊 测试输出文件:")
print("-" * 70)
for f in os.listdir(test_output_dir):
    filepath = os.path.join(test_output_dir, f)
    size = os.path.getsize(filepath)
    print(f"  📄 {f} ({size} 字节)")
    print(f"     路径: {filepath}")

print("\n" + "-" * 70)
print("下一步操作建议:")
print("-" * 70)
print("1. 打开浏览器访问: http://localhost:3000/login")
print("2. 使用账号 aaawhz3 登录")
print("3. 检查登录是否成功")
print("4. 如果登录成功，计算一个星盘并保存")
print("5. 然后测试 导出 -> 导出 PDF 报告")
print("=" * 70)
