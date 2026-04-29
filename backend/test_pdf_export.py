import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("PDF 导出诊断测试")
print("=" * 60)

print("\n1. 测试依赖安装...")
try:
    import reportlab
    print(f"   ✅ ReportLab: {reportlab.__version__}")
except ImportError as e:
    print(f"   ❌ ReportLab 未安装: {e}")

try:
    import swisseph as swe
    print(f"   ✅ Swiss Ephemeris (pyswisseph)")
except ImportError as e:
    print(f"   ❌ pyswisseph 未安装: {e}")

print("\n2. 测试字体支持...")
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

print("   检查 ReportLab 可用字体:")
for font_name in pdfmetrics.getRegisteredFontNames():
    print(f"      - {font_name}")

WIN_FONT_PATHS = [
    "C:\\Windows\\Fonts\\simhei.ttf",
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simsun.ttc",
    "C:\\Windows\\Fonts\\simkai.ttf",
    os.path.join(os.path.dirname(__file__), "app", "fonts", "simhei.ttf"),
    os.path.join(os.path.dirname(__file__), "fonts", "simhei.ttf"),
]

FOUND_FONT = None
for font_path in WIN_FONT_PATHS:
    if os.path.exists(font_path):
        print(f"\n   找到字体: {font_path}")
        try:
            font_name = os.path.basename(font_path).replace('.ttf', '').replace('.ttc', '')
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            FOUND_FONT = font_name
            print(f"   ✅ 字体注册成功: {font_name}")
            break
        except Exception as e:
            print(f"   ⚠️ 字体注册失败: {e}")

if not FOUND_FONT:
    print("\n   ⚠️ 未找到中文字体，中文可能无法正常显示")
    FOUND_FONT = 'Helvetica'

print(f"\n   使用字体: {FOUND_FONT}")

print("\n3. 测试生成简单 PDF...")
try:
    import io
    from datetime import datetime
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        parent=styles['Title'],
        fontName=FOUND_FONT,
        fontSize=24,
        textColor=colors.HexColor("#4B0082"),
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseBody',
        parent=styles['BodyText'],
        fontName=FOUND_FONT,
        fontSize=12,
        textColor=colors.HexColor("#1F2937"),
        leading=18
    ))
    
    story = []
    story.append(Paragraph("星盘测试报告", styles['ChineseTitle']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("这是一份测试报告，用于验证中文显示是否正常。", styles['ChineseBody']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"测试时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}", styles['ChineseBody']))
    story.append(Spacer(1, 20))
    
    table_data = [
        ["行星", "星座", "宫位"],
        ["太阳", "白羊座", "第一宫"],
        ["月亮", "金牛座", "第二宫"],
        ["水星", "双子座", "第三宫"],
    ]
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FOUND_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4B0082")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    
    pdf_size = len(buffer.getvalue())
    print(f"   ✅ PDF 生成成功，大小: {pdf_size} 字节")
    
    test_output = os.path.join(os.path.dirname(__file__), "test_output.pdf")
    with open(test_output, "wb") as f:
        f.write(buffer.getvalue())
    print(f"   ✅ PDF 已保存到: {test_output}")
    
except Exception as e:
    import traceback
    print(f"   ❌ PDF 生成失败: {e}")
    print(f"   堆栈: {traceback.format_exc()}")

print("\n4. 测试星盘计算...")
try:
    from app.astro import calculate_chart, parse_birth_datetime
    
    dt = parse_birth_datetime("1990-01-15", "12:00")
    print(f"   ✅ 日期解析成功: {dt}")
    
    chart_data = calculate_chart(
        year=1990,
        month=1,
        day=15,
        hour=12,
        minute=0,
        latitude=39.9042,
        longitude=116.4074,
        house_system="placidus"
    )
    
    planets = chart_data.get("planets", [])
    print(f"   ✅ 星盘计算成功，行星数量: {len(planets)}")
    
    for p in planets[:3]:
        print(f"      - {p.get('planet', '')}: {p.get('sign', '')}")
        
except Exception as e:
    import traceback
    print(f"   ❌ 星盘计算失败: {e}")
    print(f"   堆栈: {traceback.format_exc()}")

print("\n5. 测试解读生成...")
try:
    from app.interpretations import generate_full_interpretation
    
    interpretation = generate_full_interpretation(chart_data)
    basic_info = interpretation.get("basic_info", {})
    print(f"   ✅ 解读生成成功")
    print(f"      - 太阳星座: {basic_info.get('sun_sign', '未知')}")
    print(f"      - 月亮星座: {basic_info.get('moon_sign', '未知')}")
    print(f"      - 上升星座: {basic_info.get('ascendant', '未知')}")
    
except Exception as e:
    import traceback
    print(f"   ❌ 解读生成失败: {e}")
    print(f"   堆栈: {traceback.format_exc()}")

print("\n6. 测试完整报告生成...")
try:
    from app.report_generator import create_pdf_report, ReportTemplate
    
    report_buffer = create_pdf_report(chart_data, template=ReportTemplate.SIMPLE)
    report_size = len(report_buffer.getvalue())
    print(f"   ✅ 完整报告生成成功，大小: {report_size} 字节")
    
    report_output = os.path.join(os.path.dirname(__file__), "test_report.pdf")
    with open(report_output, "wb") as f:
        f.write(report_buffer.getvalue())
    print(f"   ✅ 报告已保存到: {report_output}")
    
except Exception as e:
    import traceback
    print(f"   ❌ 完整报告生成失败: {e}")
    print(f"   堆栈: {traceback.format_exc()}")

print("\n" + "=" * 60)
print("诊断测试完成")
print("=" * 60)
