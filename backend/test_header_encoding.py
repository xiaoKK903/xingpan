import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Content-Disposition Header 编码测试")
print("=" * 60)

from app.services.chart_service import (
    encode_safe_filename,
    build_content_disposition_header
)

test_filenames = [
    "星盘解读报告_测试用户_19900115_1200_详细版.pdf",
    "张三_星盘报告.pdf",
    "李四_Beijing_20240101.pdf",
    "chart_report_2024.pdf",
    "带<危险:字符>的文件名.pdf",
]

print("\n测试文件名编码:")
print("-" * 60)

for filename in test_filenames:
    print(f"\n原始文件名: {filename}")
    
    safe = encode_safe_filename(filename)
    print(f"  安全文件名: {safe}")
    
    header = build_content_disposition_header(filename)
    print(f"  Content-Disposition: {header}")
    
    try:
        parts = header.split('; ')
        for part in parts:
            if part.startswith('filename='):
                value = part.split('=', 1)[1].strip('"')
                value.encode('latin-1')
                print(f"  ✅ filename= 部分可通过 latin-1 编码")
    except UnicodeEncodeError as e:
        print(f"  ❌ 编码失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
