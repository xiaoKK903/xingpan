import io
import os
import tempfile
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.interpretations import generate_full_interpretation, get_house_interpretation


def find_chinese_font():
    font_paths = [
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\simsun.ttc",
        "C:\\Windows\\Fonts\\simkai.ttf",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        os.path.join(os.path.dirname(__file__), "fonts", "simhei.ttf"),
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_name = os.path.splitext(os.path.basename(font_path))[0]
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except Exception:
                continue
    
    return None


CHINESE_FONT = find_chinese_font()
DEFAULT_FONT = CHINESE_FONT if CHINESE_FONT else 'Helvetica'


class ReportTemplate:
    SIMPLE = "simple"
    DETAILED = "detailed"


COLORS = {
    "primary": colors.HexColor("#4B0082"),
    "secondary": colors.HexColor("#8B5CF6"),
    "accent": colors.HexColor("#A855F7"),
    "background": colors.HexColor("#FAF5FF"),
    "text": colors.HexColor("#1F2937"),
    "light_text": colors.HexColor("#6B7280"),
}


class CustomStyles:
    _instance = None
    _styles_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not CustomStyles._styles_initialized:
            self._init_styles()
            CustomStyles._styles_initialized = True
    
    def _init_styles(self):
        self.styles = {}
        
        self.styles['ReportTitle'] = ParagraphStyle(
            name='ReportTitle',
            fontName=DEFAULT_FONT,
            fontSize=24,
            textColor=COLORS["primary"],
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=30
        )
        
        self.styles['ReportSubtitle'] = ParagraphStyle(
            name='ReportSubtitle',
            fontName=DEFAULT_FONT,
            fontSize=14,
            textColor=COLORS["light_text"],
            alignment=TA_CENTER,
            spaceAfter=30,
            leading=20
        )
        
        self.styles['SectionTitle'] = ParagraphStyle(
            name='SectionTitle',
            fontName=DEFAULT_FONT,
            fontSize=18,
            textColor=COLORS["primary"],
            spaceBefore=20,
            spaceAfter=10,
            leading=24
        )
        
        self.styles['SectionTitle2'] = ParagraphStyle(
            name='SectionTitle2',
            fontName=DEFAULT_FONT,
            fontSize=14,
            textColor=COLORS["secondary"],
            spaceBefore=15,
            spaceAfter=8,
            leading=18
        )
        
        self.styles['BodyText'] = ParagraphStyle(
            name='BodyText',
            fontName=DEFAULT_FONT,
            fontSize=10,
            textColor=COLORS["text"],
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        )
        
        self.styles['PlanetName'] = ParagraphStyle(
            name='PlanetName',
            fontName=DEFAULT_FONT,
            fontSize=12,
            textColor=COLORS["primary"],
            spaceBefore=10,
            spaceAfter=5,
            leading=16,
            fontWeight='bold'
        )
        
        self.styles['PlanetInfo'] = ParagraphStyle(
            name='PlanetInfo',
            fontName=DEFAULT_FONT,
            fontSize=9,
            textColor=COLORS["light_text"],
            spaceAfter=5,
            leading=12
        )
        
        self.styles['AspectTitle'] = ParagraphStyle(
            name='AspectTitle',
            fontName=DEFAULT_FONT,
            fontSize=11,
            textColor=COLORS["text"],
            spaceBefore=8,
            spaceAfter=4,
            leading=14
        )
        
        self.styles['FooterText'] = ParagraphStyle(
            name='FooterText',
            fontName=DEFAULT_FONT,
            fontSize=8,
            textColor=COLORS["light_text"],
            alignment=TA_CENTER,
            leading=12
        )
        
        self.styles['TableHeader'] = ParagraphStyle(
            name='TableHeader',
            fontName=DEFAULT_FONT,
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=14
        )
        
        self.styles['TableCell'] = ParagraphStyle(
            name='TableCell',
            fontName=DEFAULT_FONT,
            fontSize=9,
            textColor=COLORS["text"],
            alignment=TA_CENTER,
            leading=12
        )
    
    def get(self, name, default=None):
        return self.styles.get(name, default)
    
    def __getitem__(self, name):
        return self.styles[name]


def get_custom_styles():
    return CustomStyles()


class ChartReportGenerator:
    def __init__(self):
        self.styles = get_custom_styles()
    
    def _create_header(self, canvas, doc, title: str = "星盘解读报告"):
        canvas.saveState()
        try:
            canvas.setFont(DEFAULT_FONT, 10)
        except:
            canvas.setFont('Helvetica', 10)
        canvas.setFillColor(COLORS["primary"])
        canvas.drawCentredString(doc.pagesize[0] / 2, doc.pagesize[1] - 2 * cm, title)
        canvas.setStrokeColor(COLORS["secondary"])
        canvas.setLineWidth(1)
        canvas.line(
            doc.leftMargin,
            doc.pagesize[1] - 2.5 * cm,
            doc.pagesize[0] - doc.rightMargin,
            doc.pagesize[1] - 2.5 * cm
        )
        canvas.restoreState()
    
    def _create_footer(self, canvas, doc):
        canvas.saveState()
        page_num = canvas.getPageNumber()
        try:
            canvas.setFont(DEFAULT_FONT, 8)
        except:
            canvas.setFont('Helvetica', 8)
        canvas.setFillColor(COLORS["light_text"])
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            1.5 * cm,
            f"第 {page_num} 页 - 星盘解读报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        canvas.restoreState()
    
    def _on_first_page(self, canvas, doc):
        canvas.saveState()
        self._create_header(canvas, doc, "星盘解读报告")
        self._create_footer(canvas, doc)
        canvas.restoreState()
    
    def _on_later_pages(self, canvas, doc):
        canvas.saveState()
        self._create_header(canvas, doc, "星盘解读报告")
        self._create_footer(canvas, doc)
        canvas.restoreState()
    
    def _generate_basic_info_table(self, interpretation: Dict[str, Any]) -> Table:
        basic_info = interpretation.get("basic_info", {})
        input_data = basic_info.get("input", {})
        
        data = [
            ["基本信息", ""],
            ["出生日期", input_data.get("date", "未知")],
            ["出生时间", input_data.get("time", "未知")],
            ["出生地点", f"{input_data.get('longitude', '未知')}°E, {input_data.get('latitude', '未知')}°N"],
            ["宫位系统", "普拉西度 (Placidus)" if input_data.get("house_system") == "placidus" else "整宫制"],
            ["", ""],
            ["核心配置", ""],
            ["太阳星座", f"{basic_info.get('sun_sign', '未知')} {basic_info.get('sun_sign_symbol', '')}"],
            ["月亮星座", f"{basic_info.get('moon_sign', '未知')} {basic_info.get('moon_sign_symbol', '')}"],
            ["上升星座", f"{basic_info.get('ascendant', '未知')} {basic_info.get('ascendant_symbol', '')}"],
            ["天顶星座", f"{basic_info.get('midheaven', '未知')} {basic_info.get('midheaven_symbol', '')}"]
        ]
        
        table = Table(data, colWidths=[4 * cm, 10 * cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('BACKGROUND', (0, 0), (1, 0), COLORS["primary"]),
            ('TEXTCOLOR', (0, 6), (1, 6), colors.white),
            ('BACKGROUND', (0, 6), (1, 6), COLORS["secondary"]),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (0, 6), (1, 6)),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('ALIGN', (0, 6), (1, 6), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        return table
    
    def _generate_elements_table(self, interpretation: Dict[str, Any]) -> Table:
        element_analysis = interpretation.get("element_analysis", {})
        counts = element_analysis.get("counts", {})
        dominant = element_analysis.get("dominant", "")
        
        data = [
            ["元素分布", "数量", "占比"],
            ["火 🔥", counts.get("火", 0), ""],
            ["土 🌍", counts.get("土", 0), ""],
            ["风 🌬️", counts.get("风", 0), ""],
            ["水 💧", counts.get("水", 0), ""],
            ["主导元素", dominant, ""]
        ]
        
        table = Table(data, colWidths=[4 * cm, 3 * cm, 7 * cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), COLORS["primary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        return table
    
    def _generate_quality_table(self, interpretation: Dict[str, Any]) -> Table:
        quality_analysis = interpretation.get("quality_analysis", {})
        counts = quality_analysis.get("counts", {})
        dominant = quality_analysis.get("dominant", "")
        
        data = [
            ["模式分布", "数量", "占比"],
            ["开创 (Cardinal)", counts.get("开创", 0), ""],
            ["固定 (Fixed)", counts.get("固定", 0), ""],
            ["变动 (Mutable)", counts.get("变动", 0), ""],
            ["主导模式", dominant, ""]
        ]
        
        table = Table(data, colWidths=[4 * cm, 3 * cm, 7 * cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), COLORS["secondary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        return table
    
    def _generate_planets_table(self, interpretation: Dict[str, Any], is_detailed: bool = False) -> Table:
        planets = interpretation.get("planet_interpretations", [])
        
        if is_detailed:
            data = [["行星", "星座", "宫位", "度数", "状态"]]
            for p in planets:
                retrograde = "逆行 (R)" if p.get("is_retrograde") else ""
                data.append([
                    f"{p.get('planet_symbol', '')} {p.get('planet', '')}",
                    f"{p.get('sign_symbol', '')} {p.get('sign', '')}",
                    f"第{p.get('house', 1)}宫",
                    p.get('degree', ''),
                    retrograde
                ])
            
            table = Table(data, colWidths=[2.8 * cm, 2.8 * cm, 2.2 * cm, 3 * cm, 3.2 * cm])
        else:
            data = [["行星", "星座", "宫位", "度数"]]
            for p in planets:
                data.append([
                    f"{p.get('planet_symbol', '')} {p.get('planet', '')}",
                    f"{p.get('sign_symbol', '')} {p.get('sign', '')}",
                    f"第{p.get('house', 1)}宫",
                    p.get('degree', '')
                ])
            
            table = Table(data, colWidths=[3 * cm, 3 * cm, 3 * cm, 5 * cm])
        
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), COLORS["primary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        return table
    
    def _generate_aspects_table(self, interpretation: Dict[str, Any]) -> Table:
        aspects = interpretation.get("aspect_interpretations", [])
        aspects = sorted(aspects, key=lambda x: x.get("orb", 10))[:15]
        
        data = [["行星1", "相位", "行星2", "容许度", "类型"]]
        for a in aspects:
            aspect_type = "和谐" if a.get("aspect") in ["三分相", "六分相", "合相"] else "紧张"
            data.append([
                f"{a.get('planet1_symbol', '')} {a.get('planet1', '')}",
                f"{a.get('aspect_symbol', '')} {a.get('aspect', '')}",
                f"{a.get('planet2_symbol', '')} {a.get('planet2', '')}",
                f"{a.get('orb', 0):.2f}°",
                aspect_type
            ])
        
        table = Table(data, colWidths=[2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), COLORS["secondary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        return table
    
    def _build_story(self, chart_data: Dict[str, Any], template: str) -> list:
        interpretation = generate_full_interpretation(chart_data)
        story = []
        
        story.append(Paragraph("星盘解读报告", self.styles['ReportTitle']))
        story.append(Paragraph(f"Astrological Chart Report - {'详细版' if template == ReportTemplate.DETAILED else '简洁版'}", self.styles['ReportSubtitle']))
        story.append(Spacer(1, 0.5 * cm))
        
        story.append(Paragraph("一、基本信息", self.styles['SectionTitle']))
        story.append(self._generate_basic_info_table(interpretation))
        story.append(Spacer(1, 0.5 * cm))
        
        story.append(Paragraph("二、元素与模式分析", self.styles['SectionTitle']))
        
        element_table = self._generate_elements_table(interpretation)
        quality_table = self._generate_quality_table(interpretation)
        
        element_quality_table = Table([[element_table, quality_table]], colWidths=[7 * cm, 7 * cm])
        story.append(element_quality_table)
        story.append(Spacer(1, 0.5 * cm))
        
        element_info = interpretation.get("element_analysis", {}).get("dominant_info", {})
        if element_info:
            story.append(Paragraph(f"主导元素说明：{element_info.get('name', '')}", self.styles['SectionTitle2']))
            story.append(Paragraph(element_info.get("description", ""), self.styles['BodyText']))
            story.append(Paragraph(f"<b>优势：</b>{element_info.get('strengths', '')}", self.styles['BodyText']))
            story.append(Paragraph(f"<b>挑战：</b>{element_info.get('challenges', '')}", self.styles['BodyText']))
        
        story.append(PageBreak())
        
        story.append(Paragraph("三、行星位置", self.styles['SectionTitle']))
        story.append(self._generate_planets_table(interpretation, is_detailed=(template == ReportTemplate.DETAILED)))
        story.append(Spacer(1, 0.5 * cm))
        
        if template == ReportTemplate.DETAILED:
            story.append(PageBreak())
            story.append(Paragraph("四、行星详细解读", self.styles['SectionTitle']))
            
            planets = interpretation.get("planet_interpretations", [])
            for planet in planets:
                planet_name = planet.get("planet", "")
                sign = planet.get("sign", "")
                house = planet.get("house", 1)
                retrograde = " (逆行)" if planet.get("is_retrograde") else ""
                
                story.append(Paragraph(
                    f"{planet.get('planet_symbol', '')} {planet_name}在{sign}第{house}宫{retrograde}",
                    self.styles['PlanetName']
                ))
                
                story.append(Paragraph(
                    planet.get("sign_interpretation", ""),
                    self.styles['BodyText']
                ))
                
                house_interp = planet.get("house_interpretation", {})
                story.append(Paragraph(
                    f"<b>{house_interp.get('name', '')}：</b>{house_interp.get('description', '')}",
                    self.styles['BodyText']
                ))
                
                story.append(Spacer(1, 0.2 * cm))
            
            story.append(PageBreak())
        
        story.append(Paragraph("五、相位分析", self.styles['SectionTitle']))
        story.append(self._generate_aspects_table(interpretation))
        story.append(Spacer(1, 0.5 * cm))
        
        if template == ReportTemplate.DETAILED:
            story.append(PageBreak())
            story.append(Paragraph("六、相位详细解读", self.styles['SectionTitle']))
            
            aspects = interpretation.get("aspect_interpretations", [])
            aspects = sorted(aspects, key=lambda x: x.get("orb", 10))[:10]
            
            for aspect in aspects:
                p1 = aspect.get("planet1", "")
                p1_sym = aspect.get("planet1_symbol", "")
                p2 = aspect.get("planet2", "")
                p2_sym = aspect.get("planet2_symbol", "")
                aspect_type = aspect.get("aspect", "")
                aspect_sym = aspect.get("aspect_symbol", "")
                orb = aspect.get("orb", 0)
                
                story.append(Paragraph(
                    f"{p1_sym} {p1} {aspect_sym} {p2_sym} {p2} ({aspect_type}，容许度 {orb:.2f}°)",
                    self.styles['AspectTitle']
                ))
                
                story.append(Paragraph(
                    aspect.get("interpretation", ""),
                    self.styles['BodyText']
                ))
                
                story.append(Spacer(1, 0.2 * cm))
            
            story.append(PageBreak())
            
            story.append(Paragraph("七、宫位概述", self.styles['SectionTitle']))
            
            for house_num in range(1, 13):
                house_interp = get_house_interpretation(house_num)
                story.append(Paragraph(
                    f"{house_interp.get('name', '')}",
                    self.styles['SectionTitle2']
                ))
                story.append(Paragraph(
                    f"<b>关键词：</b>{house_interp.get('keywords', '')}",
                    self.styles['PlanetInfo']
                ))
                story.append(Paragraph(
                    house_interp.get("description", ""),
                    self.styles['BodyText']
                ))
                story.append(Spacer(1, 0.2 * cm))
        
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph("报告说明", self.styles['SectionTitle2']))
        story.append(Paragraph(
            "本报告基于西方占星学原理生成，仅供参考和娱乐用途。占星学揭示的是潜在的趋势和可能性，而非命运的确定性。每个人都有自由意志去选择如何表达和发展自己的星盘能量。",
            self.styles['BodyText']
        ))
        story.append(Paragraph(
            f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            self.styles['FooterText']
        ))
        
        return story
    
    def generate_report(
        self,
        chart_data: Dict[str, Any],
        template: str = ReportTemplate.DETAILED,
        output_path: Optional[str] = None,
        use_temp_file: bool = True
    ) -> io.BytesIO:
        story = self._build_story(chart_data, template)
        
        if use_temp_file and output_path is None:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                doc = SimpleDocTemplate(
                    tmp_path,
                    pagesize=A4,
                    rightMargin=2 * cm,
                    leftMargin=2 * cm,
                    topMargin=3 * cm,
                    bottomMargin=2 * cm
                )
                
                doc.build(
                    story,
                    onFirstPage=self._on_first_page,
                    onLaterPages=self._on_later_pages
                )
                
                with open(tmp_path, 'rb') as f:
                    buffer = io.BytesIO(f.read())
                
                buffer.seek(0)
                
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(buffer.getvalue())
                    buffer.seek(0)
                
                return buffer
                
            finally:
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except:
                    pass
        else:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2 * cm,
                leftMargin=2 * cm,
                topMargin=3 * cm,
                bottomMargin=2 * cm
            )
            
            doc.build(
                story,
                onFirstPage=self._on_first_page,
                onLaterPages=self._on_later_pages
            )
            
            buffer.seek(0)
            
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                buffer.seek(0)
            
            return buffer


def create_pdf_report(
    chart_data: Dict[str, Any],
    template: str = "detailed",
    output_path: Optional[str] = None
) -> io.BytesIO:
    generator = ChartReportGenerator()
    return generator.generate_report(chart_data, template=template, output_path=output_path)


async def create_pdf_report_async(
    chart_data: Dict[str, Any],
    template: str = "detailed",
    output_path: Optional[str] = None
) -> io.BytesIO:
    def _sync_generate():
        return create_pdf_report(chart_data, template, output_path)
    
    result = await asyncio.to_thread(_sync_generate)
    return result
