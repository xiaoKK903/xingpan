import sys
import os
import io
import json
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("PDF 导出端到端测试")
print("=" * 70)

test_output_dir = os.path.join(os.path.dirname(__file__), "test_output")
os.makedirs(test_output_dir, exist_ok=True)
print(f"\n📁 测试输出目录: {test_output_dir}")

print("\n" + "-" * 70)
print("步骤 1: 测试后端模块导入")
print("-" * 70)

try:
    from app.astro import calculate_chart, parse_birth_datetime
    print("✅ app.astro 导入成功")
except Exception as e:
    print(f"❌ app.astro 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.report_generator import create_pdf_report, ReportTemplate, ChartReportGenerator, CustomStyles
    print("✅ app.report_generator 导入成功")
    print(f"   - ReportTemplate.SIMPLE = {ReportTemplate.SIMPLE}")
    print(f"   - ReportTemplate.DETAILED = {ReportTemplate.DETAILED}")
except Exception as e:
    print(f"❌ app.report_generator 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.interpretations import generate_full_interpretation
    print("✅ app.interpretations 导入成功")
except Exception as e:
    print(f"❌ app.interpretations 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 70)
print("步骤 2: 测试星盘计算")
print("-" * 70)

test_birth_data = {
    'name': '测试用户',
    'birth_date': '1990-01-15',
    'birth_time': '12:00',
    'latitude': 39.9042,
    'longitude': 116.4074,
    'birth_place': '北京',
    'house_system': 'placidus'
}

print(f"测试数据:")
print(f"  - 姓名: {test_birth_data['name']}")
print(f"  - 出生日期: {test_birth_data['birth_date']}")
print(f"  - 出生时间: {test_birth_data['birth_time']}")
print(f"  - 出生地点: {test_birth_data['birth_place']}")
print(f"  - 经度: {test_birth_data['longitude']}")
print(f"  - 纬度: {test_birth_data['latitude']}")

try:
    dt = parse_birth_datetime(test_birth_data['birth_date'], test_birth_data['birth_time'])
    print(f"\n✅ 日期解析成功: {dt}")
    
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
    
    print(f"✅ 星盘计算成功")
    print(f"   - 行星数量: {len(chart_data.get('planets', []))}")
    
    planets = chart_data.get('planets', [])
    for p in planets[:3]:
        print(f"     * {p.get('planet', '未知')}: {p.get('sign', '未知')} 第{p.get('house', 1)}宫")
        
except Exception as e:
    print(f"❌ 星盘计算失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 70)
print("步骤 3: 测试解读生成")
print("-" * 70)

try:
    interpretation = generate_full_interpretation(chart_data)
    basic_info = interpretation.get('basic_info', {})
    
    print("✅ 解读生成成功")
    print(f"   - 太阳星座: {basic_info.get('sun_sign', '未知')}")
    print(f"   - 月亮星座: {basic_info.get('moon_sign', '未知')}")
    print(f"   - 上升星座: {basic_info.get('ascendant', '未知')}")
    
    planet_interps = interpretation.get('planet_interpretations', [])
    print(f"   - 行星解读数量: {len(planet_interps)}")
    
    element_analysis = interpretation.get('element_analysis', {})
    print(f"   - 元素分布: {element_analysis.get('counts', {})}")
    print(f"   - 主导元素: {element_analysis.get('dominant', '未知')}")
    
except Exception as e:
    print(f"❌ 解读生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 70)
print("步骤 4: 测试 CustomStyles 单例模式")
print("-" * 70)

try:
    styles1 = CustomStyles()
    print(f"✅ 创建第一个 CustomStyles 实例")
    print(f"   - 样式数量: {len(styles1.styles)}")
    print(f"   - 样式列表: {list(styles1.styles.keys())}")
    
    styles2 = CustomStyles()
    print(f"\n✅ 创建第二个 CustomStyles 实例")
    print(f"   - 是否同一个实例: {styles1 is styles2}")
    
    if styles1 is styles2:
        print("   ✅ 单例模式工作正常")
    else:
        print("   ⚠️  单例模式可能有问题")
        
except Exception as e:
    print(f"❌ CustomStyles 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 70)
print("步骤 5: 测试 ChartReportGenerator 创建")
print("-" * 70)

try:
    generator1 = ChartReportGenerator()
    print(f"✅ 创建第一个 ChartReportGenerator")
    
    generator2 = ChartReportGenerator()
    print(f"✅ 创建第二个 ChartReportGenerator")
    
except Exception as e:
    print(f"❌ ChartReportGenerator 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 70)
print("步骤 6: 测试 create_pdf_report 函数")
print("-" * 70)

print("\n测试简洁版报告:")
try:
    simple_output = os.path.join(test_output_dir, "test_simple_report.pdf")
    
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
    
    pdf_buffer = create_pdf_report(chart_data, template=ReportTemplate.SIMPLE, output_path=simple_output)
    pdf_size = len(pdf_buffer.getvalue())
    
    print(f"✅ 简洁版报告生成成功")
    print(f"   - 文件大小: {pdf_size} 字节")
    print(f"   - 保存路径: {simple_output}")
    print(f"   - 文件存在: {os.path.exists(simple_output)}")
    
except Exception as e:
    print(f"❌ 简洁版报告生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n测试详细版报告:")
try:
    detailed_output = os.path.join(test_output_dir, "test_detailed_report.pdf")
    
    pdf_buffer = create_pdf_report(chart_data, template=ReportTemplate.DETAILED, output_path=detailed_output)
    pdf_size = len(pdf_buffer.getvalue())
    
    print(f"✅ 详细版报告生成成功")
    print(f"   - 文件大小: {pdf_size} 字节")
    print(f"   - 保存路径: {detailed_output}")
    print(f"   - 文件存在: {os.path.exists(detailed_output)}")
    
except Exception as e:
    print(f"❌ 详细版报告生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 70)
print("步骤 7: 测试多次调用（关键测试）")
print("-" * 70)

print("连续创建 3 个报告测试稳定性:")

for i in range(3):
    try:
        output_file = os.path.join(test_output_dir, f"test_loop_{i+1}.pdf")
        buffer = create_pdf_report(chart_data, template=ReportTemplate.SIMPLE, output_path=output_file)
        size = len(buffer.getvalue())
        print(f"  ✅ 第 {i+1} 次: {size} 字节 -> {output_file}")
    except Exception as e:
        print(f"  ❌ 第 {i+1} 次失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "-" * 70)
print("步骤 8: 测试 services/chart_service.py 中的报告生成")
print("-" * 70)

try:
    from app.services.chart_service import generate_chart_report, ChartService
    
    print("✅ services 模块导入成功")
    
    service_output = os.path.join(test_output_dir, "test_service_report.pdf")
    
    buffer, filename = generate_chart_report(
        chart_data=chart_data,
        name=test_birth_data['name'],
        birth_date=test_birth_data['birth_date'],
        birth_time=test_birth_data['birth_time'],
        birth_place=test_birth_data['birth_place'],
        latitude=test_birth_data['latitude'],
        longitude=test_birth_data['longitude'],
        template=ReportTemplate.DETAILED
    )
    
    with open(service_output, "wb") as f:
        f.write(buffer.getvalue())
    
    size = os.path.getsize(service_output)
    print(f"✅ 服务层报告生成成功")
    print(f"   - 文件名: {filename}")
    print(f"   - 文件大小: {size} 字节")
    print(f"   - 保存路径: {service_output}")
    
except Exception as e:
    print(f"❌ 服务层报告生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有测试通过！")
print("=" * 70)

print(f"\n📊 测试输出文件汇总:")
print("-" * 70)
for f in os.listdir(test_output_dir):
    filepath = os.path.join(test_output_dir, f)
    size = os.path.getsize(filepath)
    print(f"  📄 {f} ({size} 字节)")
    print(f"     路径: {filepath}")

print("\n" + "-" * 70)
print("接下来请按以下步骤验证接口:")
print("-" * 70)
print("1. 打开浏览器访问: http://localhost:3000")
print("2. 使用账号 aaawhz3 登录")
print("3. 计算一个星盘")
print("4. 保存星盘（获取 chart_id）")
print("5. 点击 导出 -> 导出 PDF 报告（详细版）")
print("\n或者使用 curl 测试 API:")
print(f"curl -X GET 'http://localhost:8000/api/reports/templates'")
print("=" * 70)
