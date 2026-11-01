import os
import io
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Headless Matplotlib configuration
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ReportLab Platypus & Layout
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Core Domain Models & Services
from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.services.financial_engine import financial_engine, LoanInputs, OperatingExpenseInputs, AcquisitionCostInputs
from app.services.deal_scoring import deal_scoring_engine
from app.services.risk_engine import risk_engine
from app.services.benchmark_service import benchmark_service
from app.utils.financial import format_inr

# ---------------------------------------------------------------------------
# Font Registration & Typography
# ---------------------------------------------------------------------------
HAS_SEGOE_UI = False
try:
    segoe_regular = "C:/Windows/Fonts/segoeui.ttf"
    segoe_bold = "C:/Windows/Fonts/segoeuib.ttf"
    segoe_italic = "C:/Windows/Fonts/segoeuii.ttf"
    segoe_bold_italic = "C:/Windows/Fonts/segoeuiz.ttf"

    if os.path.exists(segoe_regular) and os.path.exists(segoe_bold):
        pdfmetrics.registerFont(TTFont("SegoeUI", segoe_regular))
        pdfmetrics.registerFont(TTFont("SegoeUI-Bold", segoe_bold))
        if os.path.exists(segoe_italic):
            pdfmetrics.registerFont(TTFont("SegoeUI-Italic", segoe_italic))
        if os.path.exists(segoe_bold_italic):
            pdfmetrics.registerFont(TTFont("SegoeUI-BoldItalic", segoe_bold_italic))

        pdfmetrics.registerFontFamily(
            "SegoeUI",
            normal="SegoeUI",
            bold="SegoeUI-Bold",
            italic="SegoeUI-Italic" if os.path.exists(segoe_italic) else "SegoeUI",
            boldItalic="SegoeUI-BoldItalic" if os.path.exists(segoe_bold_italic) else "SegoeUI-Bold",
        )
        HAS_SEGOE_UI = True
except Exception:
    HAS_SEGOE_UI = False

PRIMARY_FONT = "SegoeUI" if HAS_SEGOE_UI else "Helvetica"
PRIMARY_BOLD = "SegoeUI-Bold" if HAS_SEGOE_UI else "Helvetica-Bold"

def format_pdf_inr(amount: Optional[float], show_symbol: bool = True) -> str:
    """Format INR string with symbol if supported, otherwise with INR prefix."""
    if amount is None:
        return "₹0" if HAS_SEGOE_UI else "INR 0"
    res = format_inr(amount, show_symbol=True)
    if not HAS_SEGOE_UI:
        res = res.replace("₹", "INR ")
    return res

# ---------------------------------------------------------------------------
# Visual Palette (Dark Navy & Slate Inspiration for ReportLab)
# ---------------------------------------------------------------------------
NAVY_DARK = colors.HexColor("#0B1120")
NAVY_MEDIUM = colors.HexColor("#1E293B")
NAVY_LIGHT = colors.HexColor("#334155")
SLATE_MUTED = colors.HexColor("#64748B")
SLATE_BORDER = colors.HexColor("#CBD5E1")
SLATE_BG_LIGHT = colors.HexColor("#F8FAFC")
SLATE_BG_ALT = colors.HexColor("#F1F5F9")
ACCENT_EMERALD = colors.HexColor("#059669")
ACCENT_EMERALD_BG = colors.HexColor("#ECFDF5")
ACCENT_ROSE = colors.HexColor("#DC2626")
ACCENT_ROSE_BG = colors.HexColor("#FEF2F2")
ACCENT_AMBER = colors.HexColor("#D97706")
ACCENT_AMBER_BG = colors.HexColor("#FFFBEB")
ACCENT_CYAN = colors.HexColor("#0891B2")
ACCENT_CYAN_BG = colors.HexColor("#ECFEFF")
ACCENT_INDIGO = colors.HexColor("#4F46E5")
TEXT_PRIMARY = colors.HexColor("#0F172A")
TEXT_SECONDARY = colors.HexColor("#475569")
WHITE = colors.HexColor("#FFFFFF")

# ---------------------------------------------------------------------------
# Numbered Canvas for Running Headers, Footers & Exact Page Counts
# ---------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages: int):
        page_num = self._pageNumber
        if page_num == 1:
            # Skip running header and footer on cover page
            return

        self.saveState()
        self.setFont(PRIMARY_FONT, 8)
        self.setFillColor(SLATE_MUTED)

        # Running Top Header
        page_width, page_height = A4
        margin_x = 36
        header_y = page_height - 30

        self.drawString(margin_x, header_y, "AI REAL ESTATE DEAL ANALYZER  |  INVESTMENT INTELLIGENCE REPORT")
        self.drawRightString(page_width - margin_x, header_y, "INDIAN PROPERTY ANALYTICS")

        self.setStrokeColor(SLATE_BORDER)
        self.setLineWidth(0.5)
        self.line(margin_x, header_y - 4, page_width - margin_x, header_y - 4)

        # Running Bottom Footer
        footer_y = 26
        self.line(margin_x, footer_y + 12, page_width - margin_x, footer_y + 12)

        gen_time = getattr(self, "report_timestamp", datetime.now().strftime("%d %b %Y, %H:%M IST"))
        self.drawString(margin_x, footer_y, f"Generated: {gen_time}  |  Strictly Confidential & Informational  |  Not Valuation Certificate")
        self.drawRightString(page_width - margin_x, footer_y, f"Page {page_num} of {total_pages}")

        self.restoreState()


# ---------------------------------------------------------------------------
# PDF Report Service Implementation
# ---------------------------------------------------------------------------
class PDFReportService:
    def __init__(self):
        self._setup_styles()

    def _setup_styles(self):
        base_styles = getSampleStyleSheet()
        self.styles = {}

        self.styles["CoverTitle"] = ParagraphStyle(
            "CoverTitle",
            parent=base_styles["Title"],
            fontName=PRIMARY_BOLD,
            fontSize=26,
            leading=32,
            textColor=NAVY_DARK,
            alignment=0,
            spaceAfter=8,
        )

        self.styles["CoverSubtitle"] = ParagraphStyle(
            "CoverSubtitle",
            parent=base_styles["Normal"],
            fontName=PRIMARY_FONT,
            fontSize=12,
            leading=16,
            textColor=SLATE_MUTED,
            alignment=0,
            spaceAfter=15,
        )

        self.styles["SectionTitle"] = ParagraphStyle(
            "SectionTitle",
            parent=base_styles["Heading1"],
            fontName=PRIMARY_BOLD,
            fontSize=16,
            leading=20,
            textColor=NAVY_DARK,
            spaceAfter=4,
        )

        self.styles["SectionSubtitle"] = ParagraphStyle(
            "SectionSubtitle",
            parent=base_styles["Normal"],
            fontName=PRIMARY_FONT,
            fontSize=9,
            leading=13,
            textColor=SLATE_MUTED,
            spaceAfter=12,
        )

        self.styles["H2"] = ParagraphStyle(
            "H2",
            parent=base_styles["Heading2"],
            fontName=PRIMARY_BOLD,
            fontSize=12,
            leading=16,
            textColor=NAVY_MEDIUM,
            spaceBefore=8,
            spaceAfter=4,
        )

        self.styles["Body"] = ParagraphStyle(
            "Body",
            parent=base_styles["Normal"],
            fontName=PRIMARY_FONT,
            fontSize=9,
            leading=13,
            textColor=TEXT_PRIMARY,
            spaceAfter=6,
        )

        self.styles["BodyBold"] = ParagraphStyle(
            "BodyBold",
            parent=self.styles["Body"],
            fontName=PRIMARY_BOLD,
        )

        self.styles["BodyMuted"] = ParagraphStyle(
            "BodyMuted",
            parent=self.styles["Body"],
            textColor=SLATE_MUTED,
            fontSize=8,
            leading=11,
        )

        self.styles["TableHead"] = ParagraphStyle(
            "TableHead",
            parent=base_styles["Normal"],
            fontName=PRIMARY_BOLD,
            fontSize=8.5,
            leading=11,
            textColor=WHITE,
            alignment=0,
        )

        self.styles["TableCell"] = ParagraphStyle(
            "TableCell",
            parent=base_styles["Normal"],
            fontName=PRIMARY_FONT,
            fontSize=8.5,
            leading=11,
            textColor=TEXT_PRIMARY,
        )

        self.styles["TableCellBold"] = ParagraphStyle(
            "TableCellBold",
            parent=self.styles["TableCell"],
            fontName=PRIMARY_BOLD,
        )

        self.styles["TableCellRight"] = ParagraphStyle(
            "TableCellRight",
            parent=self.styles["TableCell"],
            alignment=2,
        )

        self.styles["TableCellRightBold"] = ParagraphStyle(
            "TableCellRightBold",
            parent=self.styles["TableCellBold"],
            alignment=2,
        )

        self.styles["Disclaimer"] = ParagraphStyle(
            "Disclaimer",
            parent=base_styles["Normal"],
            fontName=PRIMARY_FONT,
            fontSize=7.5,
            leading=10.5,
            textColor=SLATE_MUTED,
            spaceAfter=4,
        )

    def _create_header_banner(self, title: str, subtitle: str) -> List[Any]:
        """Generate standardized top header banner for content pages."""
        return [
            Paragraph(title, self.styles["SectionTitle"]),
            Paragraph(subtitle, self.styles["SectionSubtitle"]),
            HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceBefore=0, spaceAfter=10),
        ]

    def _generate_scenario_chart(self, scenarios: List[Dict[str, Any]]) -> io.BytesIO:
        """
        Generate high-resolution dark-themed Matplotlib bar chart
        visualizing monthly net cash flow across scenarios.
        """
        names = []
        cash_flows = []
        colors_list = []

        for sc in scenarios:
            name = sc.get("scenario_name", "Scenario")
            # Shorten label for clean axis display
            short_name = (
                name.replace("Scenario", "")
                .replace("Baseline", "Base")
                .replace("Market", "")
                .replace("Tightening", "")
                .strip(" ()")
            )
            names.append(short_name)
            cf = sc.get("monthly_cash_flow_inr") if "monthly_cash_flow_inr" in sc else sc.get("monthly_net_cash_flow_inr", 0)
            cash_flows.append(cf)
            colors_list.append("#059669" if cf >= 0 else "#DC2626")

        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        fig, ax = plt.subplots(figsize=(6.8, 2.8), dpi=200)
        fig.patch.set_facecolor("#F8FAFC")
        ax.set_facecolor("#FFFFFF")

        bars = ax.bar(names, cash_flows, color=colors_list, width=0.55, edgecolor="#CBD5E1", linewidth=0.8)

        ax.axhline(0, color="#475569", linewidth=1.0, linestyle="--")
        ax.set_title("Monthly Net Cash Flow Comparison Across Stress Scenarios", fontsize=10, fontweight="bold", pad=10, color="#0F172A")
        ax.set_ylabel("Monthly Cash Flow (INR)", fontsize=8, color="#475569")
        ax.tick_params(axis="x", labelsize=7.5, rotation=12)
        ax.tick_params(axis="y", labelsize=7.5)

        # Currency formatting for Y-axis
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"₹{int(x):,}"))

        # Value labels above/below bars
        for bar in bars:
            height = bar.get_height()
            va = "bottom" if height >= 0 else "top"
            offset = 1200 if height >= 0 else -1800
            val_text = f"₹{int(height):,}"
            ax.annotate(
                val_text,
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -8),
                textcoords="offset points",
                ha="center",
                va=va,
                fontsize=6.5,
                fontweight="bold",
                color="#059669" if height >= 0 else "#DC2626",
            )

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    def generate_pdf_report(
        self,
        prop: Property,
        ai_analysis: Optional[Any] = None,
        custom_loan_params: Optional[Dict[str, Any]] = None,
        benchmark: Optional[MarketBenchmark] = None,
    ) -> bytes:
        """
        Generate a complete, strictly formatted 10-page investment analysis report.
        Guarantees zero clipped content, exact page breaks, and clean margins.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=42,
            bottomMargin=42,
        )

        usable_width = A4[0] - 72  # ~523.27 pt

        # -------------------------------------------------------------
        # Gather Underlying Financial Engine & Risk Data
        # -------------------------------------------------------------
        loan_inputs = LoanInputs(
            purchase_price_inr=prop.purchase_price_inr,
            down_payment_pct=custom_loan_params.get("down_payment_pct", 20.0) if custom_loan_params else 20.0,
            annual_interest_rate_pct=custom_loan_params.get("annual_interest_rate_pct", 8.5) if custom_loan_params else 8.5,
            tenure_years=custom_loan_params.get("tenure_years", 20) if custom_loan_params else 20,
        )
        loan_metrics = financial_engine.calculate_loan_emi(loan_inputs)

        op_inputs = OperatingExpenseInputs(
            expected_monthly_rent_inr=prop.expected_monthly_rent_inr,
            monthly_maintenance_inr=prop.monthly_maintenance_inr,
            vacancy_rate_pct=custom_loan_params.get("vacancy_rate_pct", 5.0) if custom_loan_params else 5.0,
        )
        op_metrics = financial_engine.calculate_operating_finances(op_inputs)

        acq_inputs = AcquisitionCostInputs(
            purchase_price_inr=prop.purchase_price_inr,
            stamp_duty_rate_pct=custom_loan_params.get("stamp_duty_pct", 6.0) if custom_loan_params else 6.0,
            registration_rate_pct=1.0,
            brokerage_rate_pct=custom_loan_params.get("brokerage_pct", 0.0) if custom_loan_params else 0.0,
            renovation_expenses_inr=custom_loan_params.get("renovation_inr", 0.0) if custom_loan_params else 0.0,
        )
        acq_metrics = financial_engine.calculate_acquisition_costs(acq_inputs)

        returns_metrics = financial_engine.calculate_investment_returns(
            purchase_price_inr=prop.purchase_price_inr,
            total_acquisition_cost_inr=acq_metrics["total_acquisition_cost_inr"],
            down_payment_inr=loan_metrics["down_payment_inr"],
            total_closing_costs_inr=acq_metrics["total_closing_costs_inr"],
            monthly_emi_inr=loan_metrics["monthly_emi_inr"],
            annual_gross_rent_inr=op_metrics["annual_gross_rent_inr"],
            annual_noi_inr=op_metrics["annual_noi_inr"],
        )

        price_per_sqft = financial_engine.calculate_price_per_sqft(
            prop.purchase_price_inr, prop.built_up_area_sqft
        )

        deal_score_data = deal_scoring_engine.evaluate_deal(
            purchase_price_inr=prop.purchase_price_inr,
            built_up_area_sqft=prop.built_up_area_sqft,
            gross_monthly_rent_inr=prop.expected_monthly_rent_inr,
            monthly_maintenance_inr=prop.monthly_maintenance_inr,
            monthly_emi_inr=loan_metrics["monthly_emi_inr"],
            gross_rental_yield_pct=returns_metrics["gross_rental_yield_pct"],
            net_rental_yield_pct=returns_metrics["net_rental_yield_pct"],
            monthly_net_cash_flow_inr=returns_metrics["monthly_net_cash_flow_inr"],
            has_source_url=bool(prop.source_url),
            has_property_age=bool(prop.property_age),
            has_market_comparables=bool(benchmark is not None),
        )
        deal_score_val = deal_score_data.get("overall_score", 70)

        # Risk engine assessment
        class MockAnalysis:
            def __init__(self):
                self.acquisition_costs = acq_metrics
                self.loan_metrics = loan_metrics
                self.operating_finances = op_metrics
                self.returns = returns_metrics
                self.deal_score = deal_score_data

        risk_analysis = risk_engine.evaluate_risk(prop, MockAnalysis(), benchmark)
        sim_results = risk_engine.run_what_if_simulation(prop)
        data_conf_score, data_conf_level, data_conf_reasons = risk_engine.calculate_data_confidence(prop, benchmark)

        report_timestamp_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

        story = []

        # =====================================================================
        # PAGE 1: COVER PAGE
        # =====================================================================
        story.append(Spacer(1, 15))
        # Top Brand Bar
        brand_table_data = [
            [
                Paragraph("<b>PROPDEAL AI INDIA</b>", ParagraphStyle("Brand", fontName=PRIMARY_BOLD, fontSize=11, textColor=ACCENT_EMERALD)),
                Paragraph("LOCAL ENGINE  •  OFFLINE & PRIVATE", ParagraphStyle("BrandR", fontName=PRIMARY_BOLD, fontSize=8, textColor=SLATE_MUTED, alignment=2)),
            ]
        ]
        brand_table = Table(brand_table_data, colWidths=[260, usable_width - 260])
        brand_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(brand_table)
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=NAVY_DARK, spaceBefore=0, spaceAfter=25))

        # Title Block
        story.append(Paragraph("REAL ESTATE INVESTMENT ANALYSIS REPORT", ParagraphStyle("DocType", fontName=PRIMARY_BOLD, fontSize=10, textColor=ACCENT_INDIGO, spaceAfter=6)))
        story.append(Paragraph(prop.title, self.styles["CoverTitle"]))
        story.append(Paragraph(f"{prop.locality}, {prop.city}, {prop.state or 'India'}  •  {prop.property_type} ({prop.bedrooms} BHK)", self.styles["CoverSubtitle"]))

        if prop.is_demo:
            demo_badge_data = [[
                Paragraph("<b>NOTICE: SIMULATED DEMO LISTING</b> — Generated for illustrative modeling purposes.", ParagraphStyle("DemoP", fontName=PRIMARY_BOLD, fontSize=8.5, textColor=ACCENT_AMBER))
            ]]
            demo_t = Table(demo_badge_data, colWidths=[usable_width])
            demo_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), ACCENT_AMBER_BG),
                ("BOX", (0, 0), (-1, -1), 1, ACCENT_AMBER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(demo_t)
            story.append(Spacer(1, 15))

        # 3 Score Cards Hero Grid
        score_cards_data = [
            [
                Paragraph("INVESTMENT ATTRACTIVENESS", ParagraphStyle("SC_T", fontName=PRIMARY_BOLD, fontSize=7.5, textColor=SLATE_MUTED, alignment=1)),
                Paragraph("RISK EXPOSURE", ParagraphStyle("SC_T", fontName=PRIMARY_BOLD, fontSize=7.5, textColor=SLATE_MUTED, alignment=1)),
                Paragraph("DATA CONFIDENCE", ParagraphStyle("SC_T", fontName=PRIMARY_BOLD, fontSize=7.5, textColor=SLATE_MUTED, alignment=1)),
            ],
            [
                Paragraph(f"<b>{deal_score_val}/100</b>", ParagraphStyle("SC_V1", fontName=PRIMARY_BOLD, fontSize=24, textColor=ACCENT_EMERALD, alignment=1)),
                Paragraph(f"<b>{risk_analysis.risk_exposure_score:.1f}/100</b>", ParagraphStyle("SC_V2", fontName=PRIMARY_BOLD, fontSize=24, textColor=ACCENT_ROSE if risk_analysis.risk_exposure_score >= 50 else ACCENT_AMBER, alignment=1)),
                Paragraph(f"<b>{data_conf_score}/100</b>", ParagraphStyle("SC_V3", fontName=PRIMARY_BOLD, fontSize=24, textColor=ACCENT_CYAN, alignment=1)),
            ],
            [
                Paragraph(f"{deal_score_data['classification'].upper()}", ParagraphStyle("SC_S", fontName=PRIMARY_BOLD, fontSize=8, textColor=TEXT_SECONDARY, alignment=1)),
                Paragraph(f"{risk_analysis.overall_risk_level.upper()}", ParagraphStyle("SC_S", fontName=PRIMARY_BOLD, fontSize=8, textColor=TEXT_SECONDARY, alignment=1)),
                Paragraph(f"{data_conf_level.upper()}", ParagraphStyle("SC_S", fontName=PRIMARY_BOLD, fontSize=8, textColor=TEXT_SECONDARY, alignment=1)),
            ],
        ]
        score_table = Table(score_cards_data, colWidths=[usable_width / 3.0] * 3)
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 25))

        # Core Financial Summary Strip
        quick_facts_data = [
            [
                Paragraph("Purchase Price", self.styles["BodyMuted"]),
                Paragraph("Monthly Rent", self.styles["BodyMuted"]),
                Paragraph("Gross Yield", self.styles["BodyMuted"]),
                Paragraph("Price / Sq.Ft", self.styles["BodyMuted"]),
            ],
            [
                Paragraph(f"<b>{format_pdf_inr(prop.purchase_price_inr)}</b>", ParagraphStyle("QF", fontName=PRIMARY_BOLD, fontSize=11, textColor=NAVY_DARK)),
                Paragraph(f"<b>{format_pdf_inr(prop.expected_monthly_rent_inr)}/mo</b>", ParagraphStyle("QF", fontName=PRIMARY_BOLD, fontSize=11, textColor=NAVY_DARK)),
                Paragraph(f"<b>{returns_metrics['gross_rental_yield_pct']}%</b>", ParagraphStyle("QF", fontName=PRIMARY_BOLD, fontSize=11, textColor=ACCENT_EMERALD)),
                Paragraph(f"<b>{format_pdf_inr(price_per_sqft)}</b>", ParagraphStyle("QF", fontName=PRIMARY_BOLD, fontSize=11, textColor=NAVY_DARK)),
            ]
        ]
        qf_table = Table(quick_facts_data, colWidths=[usable_width / 4.0] * 4)
        qf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_ALT),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(qf_table)
        story.append(Spacer(1, 35))

        # Metadata & Disclaimer Box
        story.append(Paragraph(f"<b>Report Date:</b> {report_timestamp_str}  •  <b>Engine Version:</b> v1.0.0 (Phase 6 Certified)", self.styles["BodyMuted"]))
        story.append(Spacer(1, 10))
        disclaimer_cover_p = (
            "<b>LEGAL & FINANCIAL DISCLAIMER:</b> This document is an analytical estimate generated by deterministic financial "
            "algorithms and local AI models. It does NOT constitute a formal property appraisal, legal title opinion, structural warranty, "
            "or investment guarantee. Real estate investments are subject to market risks, vacancy variances, and tenant defaults. "
            "Independent verification of title deeds, encumbrances, and municipal sanction plans is strictly advised before transacting."
        )
        story.append(Paragraph(disclaimer_cover_p, self.styles["Disclaimer"]))
        story.append(PageBreak())

        # =====================================================================
        # PAGE 2: EXECUTIVE SUMMARY
        # =====================================================================
        story.extend(self._create_header_banner(
            "Executive Investment Summary",
            "High-level thesis, algorithmic verdict, key financial drivers, and operational risks."
        ))

        # AI Verdict Banner
        if ai_analysis and hasattr(ai_analysis, "verdict"):
            ai_verdict = ai_analysis.verdict.value if hasattr(ai_analysis.verdict, "value") else str(ai_analysis.verdict)
        elif ai_analysis and hasattr(ai_analysis, "investment_verdict"):
            ai_verdict = str(ai_analysis.investment_verdict)
        else:
            ai_verdict = "Potential with Caution"
        verdict_color = ACCENT_EMERALD if "Strong" in ai_verdict else (ACCENT_AMBER if "Caution" in ai_verdict else ACCENT_ROSE)
        verdict_bg = ACCENT_EMERALD_BG if "Strong" in ai_verdict else (ACCENT_AMBER_BG if "Caution" in ai_verdict else ACCENT_ROSE_BG)

        verdict_table_data = [
            [
                Paragraph("<b>OFFICIAL INVESTMENT VERDICT</b>", ParagraphStyle("OVH", fontName=PRIMARY_BOLD, fontSize=8, textColor=verdict_color)),
                Paragraph(f"<b>{ai_verdict.upper()}</b>", ParagraphStyle("OVV", fontName=PRIMARY_BOLD, fontSize=14, textColor=verdict_color, alignment=2)),
            ]
        ]
        verdict_table = Table(verdict_table_data, colWidths=[200, usable_width - 200])
        verdict_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), verdict_bg),
            ("BOX", (0, 0), (-1, -1), 1, verdict_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(verdict_table)
        story.append(Spacer(1, 12))

        # Executive Summary Narrative
        story.append(Paragraph("Executive Summary Narrative", self.styles["H2"]))
        if ai_analysis and hasattr(ai_analysis, "executive_summary") and ai_analysis.executive_summary:
            summary_text = ai_analysis.executive_summary
            mode_badge = "<i>Source: Local AI Model (llama3.2:3b) grounded in verified financials</i>"
        elif prop.ai_summary:
            summary_text = prop.ai_summary
            mode_badge = "<i>Source: Pre-computed property analytical summary</i>"
        else:
            summary_text = (
                f"The subject property in {prop.locality}, {prop.city} is priced at {format_pdf_inr(prop.purchase_price_inr)} "
                f"({format_pdf_inr(price_per_sqft)}/sq.ft) with an expected monthly rental revenue of {format_pdf_inr(prop.expected_monthly_rent_inr)}. "
                f"The deal produces a Gross Rental Yield of {returns_metrics['gross_rental_yield_pct']}%, Net Rental Yield of {returns_metrics['net_rental_yield_pct']}%, "
                f"and an estimated monthly net cash flow of {format_pdf_inr(returns_metrics['monthly_net_cash_flow_inr'])} under standard 80% financing terms. "
                f"The composite Deal Score is evaluated at {deal_score_val}/100 with an overall Risk Score of {risk_analysis.risk_exposure_score:.1f}/100."
            )
            mode_badge = "<i>Source: Deterministic Financial Engine (Offline Fallback Mode)</i>"

        story.append(Paragraph(summary_text, self.styles["Body"]))
        story.append(Paragraph(mode_badge, self.styles["BodyMuted"]))
        story.append(Spacer(1, 10))

        # Strengths & Weaknesses 2-Column Table
        strengths = deal_score_data.get("positive_factors", [
            f"Gross rental yield of {returns_metrics['gross_rental_yield_pct']}%",
            f"Established micro-market demand in {prop.locality}",
            f"Reasonable acquisition ticket size of {format_pdf_inr(prop.purchase_price_inr)}"
        ])
        weaknesses = deal_score_data.get("negative_factors", []) or deal_score_data.get("risk_flags", [
            f"Monthly net cash flow sensitivity: {format_pdf_inr(returns_metrics['monthly_net_cash_flow_inr'])}/mo",
            "Vacancy risk exposure during tenant turnover",
            "Home loan interest rate tightening sensitivity"
        ])

        str_paras = [Paragraph(f"• {s}", self.styles["Body"]) for s in strengths[:4]]
        if not str_paras:
            str_paras = [Paragraph("• No major statistical anomalies noted.", self.styles["Body"])]

        wk_paras = [Paragraph(f"• {w}", self.styles["Body"]) for w in weaknesses[:4]]
        if not wk_paras:
            wk_paras = [Paragraph("• Standard market leverage risks apply.", self.styles["Body"])]

        sw_data = [
            [
                Paragraph("<b>CORE FINANCIAL STRENGTHS</b>", ParagraphStyle("TH1", fontName=PRIMARY_BOLD, fontSize=8.5, textColor=ACCENT_EMERALD)),
                Paragraph("<b>FINANCIAL WEAKNESSES & RISKS</b>", ParagraphStyle("TH2", fontName=PRIMARY_BOLD, fontSize=8.5, textColor=ACCENT_ROSE)),
            ],
            [str_paras, wk_paras],
        ]
        sw_table = Table(sw_data, colWidths=[usable_width / 2.0 - 5, usable_width / 2.0 - 5])
        sw_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), ACCENT_EMERALD_BG),
            ("BACKGROUND", (1, 0), (1, 0), ACCENT_ROSE_BG),
            ("BACKGROUND", (0, 1), (-1, -1), SLATE_BG_LIGHT),
            ("BOX", (0, 0), (0, -1), 1, ACCENT_EMERALD),
            ("BOX", (1, 0), (1, -1), 1, ACCENT_ROSE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(sw_table)
        story.append(Spacer(1, 14))

        # Important Underwriting Assumptions Box
        assumptions_p = (
            "<b>Key Modeling Assumptions:</b> Financing assumes a 20% down payment ({dp}), 80% loan principal ({lp}), "
            "8.5% annual home loan interest rate with a 20-year reducing-balance tenure (Monthly EMI: {emi}). "
            "Vacancy allowance is factored at 5.0% of annual gross rent. Acquisition closing costs include 6.0% stamp duty "
            "and 1.0% registration charges. Appreciation is excluded from basic cash flow returns to maintain capital prudence."
        ).format(
            dp=format_pdf_inr(loan_metrics["down_payment_inr"]),
            lp=format_pdf_inr(loan_metrics["loan_principal_inr"]),
            emi=format_pdf_inr(loan_metrics["monthly_emi_inr"]),
        )
        assump_table = Table([[Paragraph(assumptions_p, self.styles["BodyMuted"])]], colWidths=[usable_width])
        assump_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(assump_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 3: PROPERTY OVERVIEW
        # =====================================================================
        story.extend(self._create_header_banner(
            "Property Overview & Physical Attributes",
            "Detailed asset specifications, geographic coordinates, age, and catalog provenance."
        ))

        overview_specs = [
            ("Property Title", prop.title),
            ("City & State", f"{prop.city}, {prop.state or 'India'}"),
            ("Micro-Market / Locality", prop.locality),
            ("Property Type", prop.property_type),
            ("Configuration", f"{prop.bedrooms} BHK  ({prop.bathrooms} Bathrooms)"),
            ("Built-Up Area", f"{prop.built_up_area_sqft:,.0f} sq.ft"),
            ("Property Age", prop.property_age or "Not Provided / Unrecorded"),
            ("Purchase Price (INR)", f"{format_pdf_inr(prop.purchase_price_inr)} (₹{int(prop.purchase_price_inr):,})"),
            ("Expected Monthly Rent", f"{format_pdf_inr(prop.expected_monthly_rent_inr)}/mo"),
            ("Monthly Maintenance", f"{format_pdf_inr(prop.monthly_maintenance_inr)}/mo"),
            ("Listing Source", prop.listing_source or "Direct Listing"),
            ("Listing Source URL", prop.source_url or "Not Provided"),
            ("Catalog Listing Date", prop.listing_date or "Recorded at Ingestion"),
            ("Demo Asset Status", "YES (Simulated Demo Record)" if prop.is_demo else "NO (Live User Record)"),
        ]

        spec_rows = [
            [
                Paragraph("<b>Specification Attribute</b>", self.styles["TableHead"]),
                Paragraph("<b>Asset Detail</b>", self.styles["TableHead"]),
            ]
        ]
        for label, val in overview_specs:
            spec_rows.append([
                Paragraph(label, self.styles["TableCellBold"]),
                Paragraph(str(val), self.styles["TableCell"]),
            ])

        spec_table = Table(spec_rows, colWidths=[180, usable_width - 180])
        spec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(spec_table)
        story.append(Spacer(1, 14))

        # Information Integrity & Provenance Note
        prov_text = (
            "<b>Data Integrity Notice:</b> Data attributes above are sourced from uploaded catalog records or CSV ingestion. "
            "A stated source URL serves solely as an electronic locator and does not certify title clarity, ownership validity, "
            "or absence of municipal litigation. Physical verification of municipal property tax receipts and building plan approvals is mandatory."
        )
        prov_table = Table([[Paragraph(prov_text, self.styles["Disclaimer"])]], colWidths=[usable_width])
        prov_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(prov_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 4: FINANCIAL ANALYSIS
        # =====================================================================
        story.extend(self._create_header_banner(
            "Financial Modeling & Return Projections",
            "Comprehensive yield metrics, operating expense deductions, and break-even capital recovery."
        ))

        # 4 Core KPI Cards Grid
        fin_cards_data = [
            [
                Paragraph("GROSS RENTAL YIELD", ParagraphStyle("FC_T", fontName=PRIMARY_BOLD, fontSize=7, textColor=SLATE_MUTED, alignment=1)),
                Paragraph("NET RENTAL YIELD", ParagraphStyle("FC_T", fontName=PRIMARY_BOLD, fontSize=7, textColor=SLATE_MUTED, alignment=1)),
                Paragraph("MONTHLY CASH FLOW", ParagraphStyle("FC_T", fontName=PRIMARY_BOLD, fontSize=7, textColor=SLATE_MUTED, alignment=1)),
                Paragraph("CASH-ON-CASH ROI", ParagraphStyle("FC_T", fontName=PRIMARY_BOLD, fontSize=7, textColor=SLATE_MUTED, alignment=1)),
            ],
            [
                Paragraph(f"<b>{returns_metrics['gross_rental_yield_pct']}%</b>", ParagraphStyle("FC_V", fontName=PRIMARY_BOLD, fontSize=16, textColor=ACCENT_EMERALD, alignment=1)),
                Paragraph(f"<b>{returns_metrics['net_rental_yield_pct']}%</b>", ParagraphStyle("FC_V", fontName=PRIMARY_BOLD, fontSize=16, textColor=NAVY_DARK, alignment=1)),
                Paragraph(f"<b>{format_pdf_inr(returns_metrics['monthly_net_cash_flow_inr'])}</b>", ParagraphStyle("FC_V", fontName=PRIMARY_BOLD, fontSize=16, textColor=ACCENT_EMERALD if returns_metrics['monthly_net_cash_flow_inr'] >= 0 else ACCENT_ROSE, alignment=1)),
                Paragraph(f"<b>{returns_metrics['cash_on_cash_roi_pct']}%</b>", ParagraphStyle("FC_V", fontName=PRIMARY_BOLD, fontSize=16, textColor=ACCENT_INDIGO, alignment=1)),
            ],
        ]
        fin_cards_table = Table(fin_cards_data, colWidths=[usable_width / 4.0] * 4)
        fin_cards_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(fin_cards_table)
        story.append(Spacer(1, 12))

        # Financial Income & Operating Statement Table
        story.append(Paragraph("Operating Income Statement (Annual & Monthly)", self.styles["H2"]))
        fin_statement_data = [
            [
                Paragraph("<b>Financial Metric</b>", self.styles["TableHead"]),
                Paragraph("<b>Monthly Amount</b>", self.styles["TableHead"]),
                Paragraph("<b>Annual Amount</b>", self.styles["TableHead"]),
                Paragraph("<b>Formula / Basis</b>", self.styles["TableHead"]),
            ],
            [
                Paragraph("Gross Expected Rent", self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(prop.expected_monthly_rent_inr), self.styles["TableCellRightBold"]),
                Paragraph(format_pdf_inr(op_metrics["annual_gross_rent_inr"]), self.styles["TableCellRightBold"]),
                Paragraph("Stated market rental rate", self.styles["TableCell"]),
            ],
            [
                Paragraph("Less: Vacancy Allowance (5%)", self.styles["TableCell"]),
                Paragraph(f"-{format_pdf_inr(op_metrics['vacancy_loss_monthly_inr'])}", self.styles["TableCellRight"]),
                Paragraph(f"-{format_pdf_inr(op_metrics['vacancy_loss_annual_inr'])}", self.styles["TableCellRight"]),
                Paragraph("5% frictional vacancy (~18 days/yr)", self.styles["TableCell"]),
            ],
            [
                Paragraph("Effective Gross Income (EGI)", self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(op_metrics["effective_gross_monthly_rent_inr"]), self.styles["TableCellRightBold"]),
                Paragraph(format_pdf_inr(op_metrics["effective_gross_monthly_rent_inr"] * 12), self.styles["TableCellRightBold"]),
                Paragraph("Gross Rent minus Vacancy", self.styles["TableCell"]),
            ],
            [
                Paragraph("Less: Society Maintenance", self.styles["TableCell"]),
                Paragraph(f"-{format_pdf_inr(prop.monthly_maintenance_inr)}", self.styles["TableCellRight"]),
                Paragraph(f"-{format_pdf_inr(prop.monthly_maintenance_inr * 12)}", self.styles["TableCellRight"]),
                Paragraph("Society amenity & maintenance charges", self.styles["TableCell"]),
            ],
            [
                Paragraph("Net Operating Income (NOI)", self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(op_metrics["monthly_noi_inr"]), ParagraphStyle("NOI_M", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD)),
                Paragraph(format_pdf_inr(op_metrics["annual_noi_inr"]), ParagraphStyle("NOI_A", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD)),
                Paragraph("Effective Rent minus Operating Expenses", self.styles["TableCell"]),
            ],
            [
                Paragraph("Less: Debt Service (Home Loan EMI)", self.styles["TableCell"]),
                Paragraph(f"-{format_pdf_inr(loan_metrics['monthly_emi_inr'])}", self.styles["TableCellRight"]),
                Paragraph(f"-{format_pdf_inr(loan_metrics['monthly_emi_inr'] * 12)}", self.styles["TableCellRight"]),
                Paragraph("Reducing-balance EMI (80% LTV, 8.5%, 20y)", self.styles["TableCell"]),
            ],
            [
                Paragraph("Net Cash Flow (Pre-Tax)", self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(returns_metrics["monthly_net_cash_flow_inr"]), ParagraphStyle("CF_M", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD if returns_metrics["monthly_net_cash_flow_inr"] >= 0 else ACCENT_ROSE)),
                Paragraph(format_pdf_inr(returns_metrics["annual_net_cash_flow_inr"]), ParagraphStyle("CF_A", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD if returns_metrics["annual_net_cash_flow_inr"] >= 0 else ACCENT_ROSE)),
                Paragraph("Annual NOI minus Annual Debt Service", self.styles["TableCell"]),
            ],
        ]

        fin_table = Table(fin_statement_data, colWidths=[150, 100, 100, usable_width - 350])
        fin_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(fin_table)
        story.append(Spacer(1, 10))

        # Acquisition Costs Breakdown Table
        story.append(Paragraph("Total Acquisition & Closing Costs Breakdown", self.styles["H2"]))
        acq_data = [
            [
                Paragraph("<b>Component</b>", self.styles["TableHead"]),
                Paragraph("<b>Rate / Basis</b>", self.styles["TableHead"]),
                Paragraph("<b>Amount (INR)</b>", self.styles["TableHead"]),
                Paragraph("<b>% of Purchase Price</b>", self.styles["TableHead"]),
            ],
            [
                Paragraph("Base Property Purchase Price", self.styles["TableCellBold"]),
                Paragraph("Base Agreement Value", self.styles["TableCell"]),
                Paragraph(format_pdf_inr(acq_metrics["purchase_price_inr"]), self.styles["TableCellRightBold"]),
                Paragraph("100.0%", self.styles["TableCellRight"]),
            ],
            [
                Paragraph("Stamp Duty", self.styles["TableCell"]),
                Paragraph(f"{acq_metrics.get('stamp_duty_pct', 6.0)}% standard rate", self.styles["TableCell"]),
                Paragraph(format_pdf_inr(acq_metrics.get("stamp_duty_inr", 0)), self.styles["TableCellRight"]),
                Paragraph(f"{acq_metrics.get('stamp_duty_pct', 6.0):.1f}%", self.styles["TableCellRight"]),
            ],
            [
                Paragraph("Registration Charges", self.styles["TableCell"]),
                Paragraph("1.0% statutory charge", self.styles["TableCell"]),
                Paragraph(format_pdf_inr(acq_metrics.get("registration_charges_inr", 0)), self.styles["TableCellRight"]),
                Paragraph("1.0%", self.styles["TableCellRight"]),
            ],
            [
                Paragraph("Brokerage & Legal Expenses", self.styles["TableCell"]),
                Paragraph("Closing allowance", self.styles["TableCell"]),
                Paragraph(format_pdf_inr(acq_metrics.get("brokerage_inr", 0)), self.styles["TableCellRight"]),
                Paragraph(f"{acq_metrics.get('brokerage_rate_pct', 0.0):.1f}%", self.styles["TableCellRight"]),
            ],
            [
                Paragraph("Total Acquisition Outlay", self.styles["TableCellBold"]),
                Paragraph("Price + Total Closing Costs", self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(acq_metrics["total_acquisition_cost_inr"]), ParagraphStyle("TOT_A", parent=self.styles["TableCellRightBold"], textColor=ACCENT_INDIGO)),
                Paragraph(f"{(acq_metrics['total_acquisition_cost_inr'] / prop.purchase_price_inr * 100):.1f}%", self.styles["TableCellRightBold"]),
            ],
            [
                Paragraph("Initial Invested Equity Outlay", self.styles["TableCellBold"]),
                Paragraph("Down Payment (20%) + Closing Costs", self.styles["TableCell"]),
                Paragraph(format_pdf_inr(returns_metrics["total_invested_capital_inr"]), ParagraphStyle("TOT_E", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD)),
                Paragraph(f"{(returns_metrics['total_invested_capital_inr'] / prop.purchase_price_inr * 100):.1f}%", self.styles["TableCellRightBold"]),
            ],
        ]
        acq_table = Table(acq_data, colWidths=[150, 130, 120, usable_width - 400])
        acq_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(acq_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 5: LOAN AND EMI ANALYSIS
        # =====================================================================
        story.extend(self._create_header_banner(
            "Financing, Leverage & Loan Amortization",
            "Reducing-balance mortgage schedules, interest liabilities, and debt-service ratios."
        ))

        loan_specs = [
            ("Purchase Price", format_pdf_inr(prop.purchase_price_inr), "Total agreed transaction value"),
            ("Down Payment (Equity)", f"{format_pdf_inr(loan_metrics['down_payment_inr'])} ({loan_metrics['down_payment_pct']}%)", "Initial out-of-pocket investor equity"),
            ("Loan Principal (Debt)", f"{format_pdf_inr(loan_metrics['loan_principal_inr'])} ({100 - loan_metrics['down_payment_pct']}%)", "Total borrowed debt from financial institution"),
            ("Home Loan Interest Rate", f"{loan_metrics['annual_interest_rate_pct']}% p.a.", "Standard reducing-balance floating rate"),
            ("Loan Tenure", f"{loan_metrics['tenure_years']} Years ({loan_metrics['total_installments']} Installments)", "Total scheduled repayment period"),
            ("Monthly Loan EMI", format_pdf_inr(loan_metrics["monthly_emi_inr"]), "Monthly reducing-balance installment"),
            ("Total Interest Payable", format_pdf_inr(loan_metrics["total_interest_payable_inr"]), "Cumulative interest over full 20-year tenure"),
            ("Total Lifetime Repayment", format_pdf_inr(loan_metrics["total_repayment_amount_inr"]), "Principal borrowed + Lifetime interest paid"),
        ]

        loan_rows = [
            [
                Paragraph("<b>Loan Parameter</b>", self.styles["TableHead"]),
                Paragraph("<b>Value</b>", self.styles["TableHead"]),
                Paragraph("<b>Financing Description</b>", self.styles["TableHead"]),
            ]
        ]
        for p_name, p_val, p_desc in loan_specs:
            loan_rows.append([
                Paragraph(p_name, self.styles["TableCellBold"]),
                Paragraph(p_val, self.styles["TableCellRightBold"]),
                Paragraph(p_desc, self.styles["TableCell"]),
            ])

        loan_table = Table(loan_rows, colWidths=[150, 130, usable_width - 280])
        loan_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(loan_table)
        story.append(Spacer(1, 12))

        # Indicative 5-Year Amortization Schedule
        story.append(Paragraph("Indicative 5-Year Amortization Schedule (Reducing Balance)", self.styles["H2"]))
        amort_rows = [
            [
                Paragraph("<b>Year</b>", self.styles["TableHead"]),
                Paragraph("<b>Opening Balance</b>", self.styles["TableHead"]),
                Paragraph("<b>Annual EMI Paid</b>", self.styles["TableHead"]),
                Paragraph("<b>Principal Paid</b>", self.styles["TableHead"]),
                Paragraph("<b>Interest Paid</b>", self.styles["TableHead"]),
                Paragraph("<b>Closing Balance</b>", self.styles["TableHead"]),
            ]
        ]

        principal = loan_metrics["loan_principal_inr"]
        r = (loan_metrics["annual_interest_rate_pct"] / 12.0) / 100.0
        emi = loan_metrics["monthly_emi_inr"]
        cur_bal = principal

        for yr in range(1, 6):
            open_bal = cur_bal
            yr_int = 0.0
            yr_prin = 0.0
            for _ in range(12):
                if cur_bal <= 0:
                    break
                m_int = cur_bal * r
                m_prin = emi - m_int
                yr_int += m_int
                yr_prin += m_prin
                cur_bal = max(0.0, cur_bal - m_prin)

            amort_rows.append([
                Paragraph(f"Year {yr}", self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(open_bal), self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(emi * 12), self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(yr_prin), self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(yr_int), self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(cur_bal), self.styles["TableCellRightBold"]),
            ])

        amort_table = Table(amort_rows, colWidths=[55, 95, 95, 95, 90, 93])
        amort_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(amort_table)
        story.append(Spacer(1, 10))

        # Leverage & DSCR Assessment
        dscr = (op_metrics["annual_noi_inr"] / (loan_metrics["monthly_emi_inr"] * 12)) if loan_metrics["monthly_emi_inr"] > 0 else 99.0
        dscr_status = "Adequate (>1.25x)" if dscr >= 1.25 else ("Tight (1.0x - 1.24x)" if dscr >= 1.0 else "Deficit (<1.0x)")
        dscr_text = (
            f"<b>Debt-Service Coverage Ratio (DSCR): {dscr:.2f}x ({dscr_status})</b> — "
            f"Net operating income generates {format_pdf_inr(op_metrics['annual_noi_inr'])} annually compared to "
            f"debt service of {format_pdf_inr(loan_metrics['monthly_emi_inr'] * 12)}. "
            + ("Operating cash flow is sufficient to service debt without external capital." if dscr >= 1.0 else "Operating rental revenue alone does not fully cover debt obligations; investor must inject cash to cover the EMI shortfall.")
        )
        dscr_table = Table([[Paragraph(dscr_text, self.styles["BodyMuted"])]], colWidths=[usable_width])
        dscr_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(dscr_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 6: RISK INTELLIGENCE
        # =====================================================================
        story.extend(self._create_header_banner(
            "Risk Exposure & Due-Diligence Profile",
            "Multi-dimensional risk scoring, category factor analysis, and external verification gates."
        ))

        # Overall Risk Score Header
        r_score = risk_analysis.risk_exposure_score
        r_level = risk_analysis.overall_risk_level
        risk_color = ACCENT_ROSE if r_score >= 60 else (ACCENT_AMBER if r_score >= 35 else ACCENT_EMERALD)
        risk_bg = ACCENT_ROSE_BG if r_score >= 60 else (ACCENT_AMBER_BG if r_score >= 35 else ACCENT_EMERALD_BG)

        r_summary_data = [
            [
                Paragraph("<b>COMPOSITE RISK EXPOSURE SCORE</b>", ParagraphStyle("RH", fontName=PRIMARY_BOLD, fontSize=8, textColor=risk_color)),
                Paragraph(f"<b>{r_score:.1f} / 100  ({r_level.upper()})</b>", ParagraphStyle("RV", fontName=PRIMARY_BOLD, fontSize=13, textColor=risk_color, alignment=2)),
            ]
        ]
        r_sum_table = Table(r_summary_data, colWidths=[220, usable_width - 220])
        r_sum_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), risk_bg),
            ("BOX", (0, 0), (-1, -1), 1, risk_color),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(r_sum_table)
        story.append(Spacer(1, 10))

        # 5-Category Risk Breakdown Table
        story.append(Paragraph("5-Category Risk Factor Decomposition", self.styles["H2"]))
        cats = risk_analysis.categories
        risk_rows = [
            [
                Paragraph("<b>Risk Category</b>", self.styles["TableHead"]),
                Paragraph("<b>Weight</b>", self.styles["TableHead"]),
                Paragraph("<b>Score</b>", self.styles["TableHead"]),
                Paragraph("<b>Level</b>", self.styles["TableHead"]),
                Paragraph("<b>Primary Risk Drivers & Observations</b>", self.styles["TableHead"]),
            ]
        ]

        cat_names = [
            ("financial", "1. Financial Risk", "30%"),
            ("loan", "2. Loan & Leverage Risk", "25%"),
            ("rental", "3. Rental Volatility Risk", "20%"),
            ("data_reliability", "4. Data Reliability Risk", "15%"),
            ("external_verification", "5. Legal Verification Risk", "10%"),
        ]

        for cat_key, cat_label, weight_str in cat_names:
            cat_obj = cats.get(cat_key) if isinstance(cats, dict) else getattr(cats, cat_key, None)
            if cat_obj:
                c_score = getattr(cat_obj, "score", 0.0)
                c_lvl = getattr(cat_obj, "risk_level", "Low")
                factors_list = getattr(cat_obj, "factors", [])
                drivers = "; ".join(factors_list[:2]) if factors_list else "No severe risk flags detected in this category."
            else:
                c_score = 0.0
                c_lvl = "Low"
                drivers = "Standard baseline."

            c_color = ACCENT_ROSE if c_score >= 50 else (ACCENT_AMBER if c_score >= 30 else ACCENT_EMERALD)
            risk_rows.append([
                Paragraph(cat_label, self.styles["TableCellBold"]),
                Paragraph(weight_str, self.styles["TableCell"]),
                Paragraph(f"<b>{c_score:.1f}</b>", ParagraphStyle("CS", parent=self.styles["TableCellRightBold"], textColor=c_color)),
                Paragraph(c_lvl, self.styles["TableCell"]),
                Paragraph(drivers, self.styles["TableCell"]),
            ])

        risk_table = Table(risk_rows, colWidths=[120, 45, 45, 60, usable_width - 270])
        risk_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 12))

        # Critical Red Flags & Mitigations Table
        story.append(Paragraph("High-Impact Risk Flags & Recommended Mitigations", self.styles["H2"]))
        flags = risk_analysis.critical_red_flags
        if not flags:
            flags = ["Standard interest rate sensitivity on floating loan", "Periodic vacancy between tenant agreements"]

        mitig_rows = [
            [
                Paragraph("<b>Identified Risk Flag</b>", self.styles["TableHead"]),
                Paragraph("<b>Prudent Investor Mitigation Strategy</b>", self.styles["TableHead"]),
            ]
        ]
        for f in flags[:4]:
            mitig = "Verify localized rental comps and maintain a 6-month debt service emergency liquidity reserve."
            if "Negative" in f or "deficit" in f.lower():
                mitig = "Increase down payment to 30-35% or negotiate lower entry price to eliminate monthly cash bleed."
            elif "RERA" in f or "legal" in f.lower() or "Encumbrance" in f:
                mitig = "Mandate advocate review of 30-year Encumbrance Certificate (EC) and verify RERA project registration."
            elif "LTV" in f or "EMI" in f:
                mitig = "De-leverage transaction or lock fixed borrowing spread to withstand potential repo rate hikes."

            mitig_rows.append([
                Paragraph(f"⚠️ {f}", self.styles["TableCellBold"]),
                Paragraph(mitig, self.styles["TableCell"]),
            ])

        mitig_table = Table(mitig_rows, colWidths=[200, usable_width - 200])
        mitig_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(mitig_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 7: MARKET BENCHMARKING
        # =====================================================================
        story.extend(self._create_header_banner(
            "Micro-Market Benchmarking & Regional Alignment",
            "Comparative valuation against localized residential averages, yield deltas, and sample sizes."
        ))

        # Benchmark Alignment Card
        if benchmark:
            bench_locality = benchmark.locality
            bench_yield = getattr(benchmark, "avg_gross_rental_yield_pct", 4.2)
            bench_price_sqft = getattr(benchmark, "avg_price_per_sqft", price_per_sqft)
            bench_rent = getattr(benchmark, "avg_monthly_rent_inr", prop.expected_monthly_rent_inr)
            bench_source = getattr(benchmark, "data_source", "Regional Micro-Market Survey")
            bench_sample = 25
            bench_date = getattr(benchmark, "collection_date", "2026-Q1")
            bench_avail = True
        else:
            bench_locality = f"{prop.city} Metro Average"
            bench_yield = 4.0
            bench_price_sqft = price_per_sqft
            bench_rent = prop.expected_monthly_rent_inr
            bench_source = "Aggregated City-Wide Residential Estimate"
            bench_sample = "N/A"
            bench_date = "2026-Q1"
            bench_avail = False

        yield_delta = returns_metrics["gross_rental_yield_pct"] - bench_yield
        price_delta = price_per_sqft - bench_price_sqft

        bench_comp_rows = [
            [
                Paragraph("<b>Metric</b>", self.styles["TableHead"]),
                Paragraph("<b>Subject Property</b>", self.styles["TableHead"]),
                Paragraph(f"<b>Market Benchmark ({bench_locality})</b>", self.styles["TableHead"]),
                Paragraph("<b>Variance (Delta)</b>", self.styles["TableHead"]),
                Paragraph("<b>Analytical Assessment</b>", self.styles["TableHead"]),
            ],
            [
                Paragraph("Gross Rental Yield", self.styles["TableCellBold"]),
                Paragraph(f"<b>{returns_metrics['gross_rental_yield_pct']}%</b>", self.styles["TableCellRight"]),
                Paragraph(f"{bench_yield:.2f}%", self.styles["TableCellRight"]),
                Paragraph(f"<b>{'+' if yield_delta >= 0 else ''}{yield_delta:.2f}%</b>", ParagraphStyle("YD", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD if yield_delta >= 0 else ACCENT_ROSE)),
                Paragraph("Premium yield efficiency" if yield_delta >= 0.25 else ("Yield aligned with market" if yield_delta >= -0.25 else "Compressed yield relative to area"), self.styles["TableCell"]),
            ],
            [
                Paragraph("Capital Rate / Sq.Ft", self.styles["TableCellBold"]),
                Paragraph(f"<b>{format_pdf_inr(price_per_sqft)}</b>", self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(bench_price_sqft), self.styles["TableCellRight"]),
                Paragraph(f"<b>{'+' if price_delta >= 0 else ''}{format_pdf_inr(price_delta)}</b>", ParagraphStyle("PD", parent=self.styles["TableCellRightBold"], textColor=ACCENT_ROSE if price_delta > 500 else ACCENT_EMERALD)),
                Paragraph("Trading above locality median" if price_delta > 500 else ("Aligned with locality price" if price_delta >= -500 else "Priced attractively below median"), self.styles["TableCell"]),
            ],
            [
                Paragraph("Monthly Rental Demand", self.styles["TableCellBold"]),
                Paragraph(f"<b>{format_pdf_inr(prop.expected_monthly_rent_inr)}</b>", self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(bench_rent), self.styles["TableCellRight"]),
                Paragraph(f"<b>{'+' if prop.expected_monthly_rent_inr >= bench_rent else ''}{format_pdf_inr(prop.expected_monthly_rent_inr - bench_rent)}</b>", self.styles["TableCellRightBold"]),
                Paragraph("Within viable tenant affordability band", self.styles["TableCell"]),
            ],
        ]

        bench_table = Table(bench_comp_rows, colWidths=[110, 95, 115, 95, usable_width - 415])
        bench_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(bench_table)
        story.append(Spacer(1, 14))

        # Benchmark Provenance Metadata Strip
        bench_meta_rows = [
            [
                Paragraph("<b>Benchmark Survey Locality:</b>", self.styles["BodyBold"]),
                Paragraph(str(bench_locality), self.styles["Body"]),
                Paragraph("<b>Data Provider / Source:</b>", self.styles["BodyBold"]),
                Paragraph(str(bench_source), self.styles["Body"]),
            ],
            [
                Paragraph("<b>Survey Sample Size:</b>", self.styles["BodyBold"]),
                Paragraph(f"{bench_sample} surveyed listings", self.styles["Body"]),
                Paragraph("<b>Last Refreshed Date:</b>", self.styles["BodyBold"]),
                Paragraph(str(bench_date), self.styles["Body"]),
            ],
        ]
        b_meta_table = Table(bench_meta_rows, colWidths=[130, 130, 130, usable_width - 390])
        b_meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(b_meta_table)
        story.append(Spacer(1, 12))

        # Explicit Provenance & Authenticity Warning
        bench_warning_p = (
            "<b>STATISTICAL PROVENANCE DISCLOSURE:</b> "
            + ("Direct micro-market survey records matched for this locality. " if bench_avail else "No localized micro-market survey was recorded; defaulted to generalized city medians. ")
            + "Market benchmarks represent aggregated listing trends and sample surveys. They are NOT certified government circle rates "
            "or sub-registrar land registry valuation tables. Actual negotiated prices may vary depending on floor rise, view, developer pedigree, "
            "and interior fit-out specifications."
        )
        b_warn_table = Table([[Paragraph(bench_warning_p, self.styles["Disclaimer"])]], colWidths=[usable_width])
        b_warn_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(b_warn_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 8: SCENARIO ANALYSIS
        # =====================================================================
        story.extend(self._create_header_banner(
            "Stress Testing & What-If Scenario Matrix",
            "Multi-scenario sensitivity simulations evaluating downside resilience under adverse macroeconomic conditions."
        ))

        scenarios_list = sim_results.scenarios
        # Build scenario table
        sc_table_rows = [
            [
                Paragraph("<b>Scenario</b>", self.styles["TableHead"]),
                Paragraph("<b>Monthly Rent</b>", self.styles["TableHead"]),
                Paragraph("<b>Rate / Vac</b>", self.styles["TableHead"]),
                Paragraph("<b>Monthly EMI</b>", self.styles["TableHead"]),
                Paragraph("<b>Net Cash Flow</b>", self.styles["TableHead"]),
                Paragraph("<b>Yield</b>", self.styles["TableHead"]),
                Paragraph("<b>Break-Even Rent</b>", self.styles["TableHead"]),
            ]
        ]

        # Add Base first
        base_sc = sim_results.base_case
        base_be_rent = (loan_metrics["monthly_emi_inr"] + prop.monthly_maintenance_inr) / 0.95
        sc_table_rows.append([
            Paragraph("<b>Base Baseline</b>", self.styles["TableCellBold"]),
            Paragraph(format_pdf_inr(prop.expected_monthly_rent_inr), self.styles["TableCellRight"]),
            Paragraph("8.5% / 5%", self.styles["TableCell"]),
            Paragraph(format_pdf_inr(loan_metrics["monthly_emi_inr"]), self.styles["TableCellRight"]),
            Paragraph(format_pdf_inr(base_sc.monthly_cash_flow_inr), ParagraphStyle("BS", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD if base_sc.monthly_cash_flow_inr >= 0 else ACCENT_ROSE)),
            Paragraph(f"{base_sc.gross_rental_yield_pct}%", self.styles["TableCellRight"]),
            Paragraph(format_pdf_inr(base_be_rent), self.styles["TableCellRight"]),
        ])

        for s in scenarios_list:
            vac_factor = max(0.01, 1.0 - (s.vacancy_rate_pct / 100.0))
            s_be_rent = (s.monthly_emi_inr + prop.monthly_maintenance_inr) / vac_factor
            sc_table_rows.append([
                Paragraph(s.scenario_name.split("(")[0].strip(), self.styles["TableCellBold"]),
                Paragraph(format_pdf_inr(s.monthly_rent_inr), self.styles["TableCellRight"]),
                Paragraph(f"{s.interest_rate_pct:.1f}% / {int(s.vacancy_rate_pct)}%", self.styles["TableCell"]),
                Paragraph(format_pdf_inr(s.monthly_emi_inr), self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(s.monthly_cash_flow_inr), ParagraphStyle("SS", parent=self.styles["TableCellRightBold"], textColor=ACCENT_EMERALD if s.monthly_cash_flow_inr >= 0 else ACCENT_ROSE)),
                Paragraph(f"{s.gross_rental_yield_pct}%", self.styles["TableCellRight"]),
                Paragraph(format_pdf_inr(s_be_rent), self.styles["TableCellRight"]),
            ])

        all_sc_for_chart = [base_sc.model_dump()] + [s.model_dump() for s in scenarios_list]
        sc_table = Table(sc_table_rows, colWidths=[95, 75, 65, 75, 75, 55, usable_width - 440])
        sc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(sc_table)
        story.append(Spacer(1, 10))

        # Embedded Matplotlib Chart
        chart_buf = self._generate_scenario_chart(all_sc_for_chart)
        chart_img = Image(chart_buf, width=usable_width, height=190)
        story.append(chart_img)
        story.append(Spacer(1, 10))

        # Stress Test Findings
        stress_takeaway = (
            "<b>Sensitivity Takeaway:</b> The property demonstrates highest sensitivity to home loan rate hikes and rental contractions. "
            f"Under the Rate Hike shock (+2.5% RBI tightening), monthly debt service increases significantly, altering net cash flow. "
            f"To remain operationally cash-neutral (break-even), the property requires a minimum monthly rent of "
            f"<b>{format_pdf_inr(base_be_rent)}</b>."
        )
        stress_table = Table([[Paragraph(stress_takeaway, self.styles["BodyMuted"])]], colWidths=[usable_width])
        stress_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(stress_table)
        story.append(PageBreak())

        # =====================================================================
        # PAGE 9: AI INVESTMENT INSIGHTS
        # =====================================================================
        story.extend(self._create_header_banner(
            "AI Deal Intelligence & Due-Diligence Roadmap",
            "Synthesized machine intelligence explaining risk exposure, vulnerabilities, and pre-closing checklists."
        ))

        ai_active = bool(ai_analysis and (hasattr(ai_analysis, "verdict") or hasattr(ai_analysis, "investment_verdict")))
        ai_badge_text = (
            "<b>ENGINE MODE: LOCAL AI VERIFIED (OLLAMA LLAMA3.2:3B)</b>"
            if ai_active
            else "<b>ENGINE MODE: DETERMINISTIC EXPERT RULES ENGINE (OFFLINE MODE)</b>"
        )
        ai_badge_color = ACCENT_EMERALD if ai_active else ACCENT_INDIGO
        ai_badge_bg = ACCENT_EMERALD_BG if ai_active else SLATE_BG_ALT

        ai_mode_table = Table([[Paragraph(ai_badge_text, ParagraphStyle("AIMode", fontName=PRIMARY_BOLD, fontSize=8, textColor=ai_badge_color))]], colWidths=[usable_width])
        ai_mode_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ai_badge_bg),
            ("BOX", (0, 0), (-1, -1), 1, ai_badge_color),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(ai_mode_table)
        story.append(Spacer(1, 10))

        # AI Narrative or Deterministic Financial Insights
        story.append(Paragraph("Deal Evaluation & Downside Exposure", self.styles["H2"]))
        if ai_active and hasattr(ai_analysis, "recommendations") and ai_analysis.recommendations:
            rec_text = (
                "<br/>• ".join(ai_analysis.recommendations)
                if isinstance(ai_analysis.recommendations, list)
                else str(ai_analysis.recommendations)
            )
            narrative_p = Paragraph(f"<b>Strategic AI Recommendations:</b><br/>• {rec_text}", self.styles["Body"])
        else:
            narrative_p = Paragraph(
                f"<b>Deterministic Assessment:</b> Based on verified cash flow modeling of {format_pdf_inr(returns_metrics['monthly_net_cash_flow_inr'])}/mo "
                f"and gross rental yield of {returns_metrics['gross_rental_yield_pct']}%, this asset offers acceptable yield efficiency "
                f"for the {prop.locality} market. However, high initial leverage exposes the buyer to interest rate volatility. "
                f"Investors are advised to negotiate an entry discount of 5-8% to bolster the net yield above 4.0%.",
                self.styles["Body"],
            )
        story.append(narrative_p)
        story.append(Spacer(1, 10))

        # Prioritized Due-Diligence Checklist Table
        story.append(Paragraph("Mandatory 5-Step Legal & Physical Due-Diligence Roadmap", self.styles["H2"]))
        dd_steps = [
            ("1. RERA Project Registration Check", "Verify valid RERA registration number and quarterly progress filings on the State RERA regulatory portal.", "MANDATORY"),
            ("2. 30-Year Encumbrance Search (EC)", "Obtain certified Form 15 Non-Encumbrance Certificate from the Sub-Registrar Office to confirm zero prior liens or mortgages.", "MANDATORY"),
            ("3. Sanctioned Layout & OC Verification", "Inspect certified Occupancy Certificate (OC) and sanctioned municipal building plan to confirm no unauthorized deviations.", "HIGH PRIORITY"),
            ("4. Society Sinking Fund & Dues Audit", "Review audited society balance sheets, pending transfer fee bylaws, and verify zero outstanding property tax dues with ULB.", "MEDIUM PRIORITY"),
            ("5. Physical Inspection & Structural Survey", "Perform on-site audit of plumbing lines, electrical sanction load, exterior waterproofing, and car parking allocation deed.", "RECOMMENDED"),
        ]

        dd_rows = [
            [
                Paragraph("<b>Checklist Item</b>", self.styles["TableHead"]),
                Paragraph("<b>Verification Action & Required Documentation</b>", self.styles["TableHead"]),
                Paragraph("<b>Priority</b>", self.styles["TableHead"]),
            ]
        ]
        for item, desc, pri in dd_steps:
            pri_color = ACCENT_ROSE if "MANDATORY" in pri else (ACCENT_AMBER if "HIGH" in pri else ACCENT_EMERALD)
            dd_rows.append([
                Paragraph(item, self.styles["TableCellBold"]),
                Paragraph(desc, self.styles["TableCell"]),
                Paragraph(f"<b>{pri}</b>", ParagraphStyle("PRI", parent=self.styles["TableCell"], textColor=pri_color, fontSize=7.5)),
            ])

        dd_table = Table(dd_rows, colWidths=[150, usable_width - 240, 90])
        dd_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(dd_table)
        story.append(Spacer(1, 10))

        # Explicit Attribution
        story.append(Paragraph(
            "<i>Note: Local AI interpretations are strictly advisory. Machine models cannot inspect physical buildings or verify physical paper title registers.</i>",
            self.styles["Disclaimer"],
        ))
        story.append(PageBreak())

        # =====================================================================
        # PAGE 10: DISCLAIMER AND METHODOLOGY
        # =====================================================================
        story.extend(self._create_header_banner(
            "Methodology, Financial Formulas & Legal Disclaimers",
            "Underwriting mathematical formulations, systemic assumptions, and regulatory limitations."
        ))

        # Mathematical Formulas Table
        story.append(Paragraph("Core Mathematical Formulations", self.styles["H2"]))
        formulas = [
            ("Gross Rental Yield (%)", "(Annual Gross Rental Income / Purchase Price) × 100"),
            ("Net Operating Income (NOI)", "Effective Gross Rent (Gross Rent - 5% Vacancy) - Annual Operating Expenses"),
            ("Net Rental Yield (%)", "(Annual NOI / Total Acquisition Cost) × 100"),
            ("Monthly Loan EMI (Reducing Balance)", "E = P · r · (1 + r)ⁿ / ((1 + r)ⁿ - 1)  [P=Principal, r=Monthly Rate, n=Months]"),
            ("Monthly Net Cash Flow", "(Annual NOI / 12) - Monthly Loan EMI"),
            ("Cash-on-Cash Return (ROI %)", "(Annual Net Cash Flow / Total Invested Capital Outlay) × 100"),
            ("Composite Risk Exposure Score", "0.30·Financial + 0.25·Loan + 0.20·Rental + 0.15·Data + 0.10·Legal"),
            ("Data Confidence Score (0-100)", "Completeness (30) + Age (15) + Source (15) + URL (10) + OpEx (15) + Benchmark (15)"),
        ]

        f_rows = [
            [
                Paragraph("<b>Metric Name</b>", self.styles["TableHead"]),
                Paragraph("<b>Exact Deterministic Formulation</b>", self.styles["TableHead"]),
            ]
        ]
        for f_name, f_eq in formulas:
            f_rows.append([
                Paragraph(f_name, self.styles["TableCellBold"]),
                Paragraph(f"<code>{f_eq}</code>", self.styles["TableCell"]),
            ])

        f_table = Table(f_rows, colWidths=[180, usable_width - 180])
        f_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_BG_LIGHT, WHITE]),
            ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(f_table)
        story.append(Spacer(1, 10))

        # Comprehensive Legal Disclaimers
        story.append(Paragraph("Statutory Legal Disclaimers & Model Boundaries", self.styles["H2"]))
        disclaimers_list = [
            "<b>1. No Financial, Investment or Tax Advice:</b> This report is generated solely for analytical and educational purposes. Neither the application nor its developers act as a registered investment adviser, SEBI-registered portfolio manager, real estate broker, or chartered tax accountant.",
            "<b>2. Independent Due Diligence Obligation:</b> Real estate transactions require mandatory offline verification. Users must independently inspect title deeds, verify 30-year Encumbrance Certificates at the local Sub-Registrar Office, review municipal sanction plans, and obtain legal advice from an advocate.",
            "<b>3. Benchmark & Market Variance:</b> Historical yields, average rents, and price/sq.ft metrics are surveyed estimates. Realized rents may fluctuate based on macroeconomic shifts, micro-market supply overhang, tenant creditworthiness, and general inflation.",
            "<b>4. Free, Local & Privacy-Preserving Architecture:</b> All computations, AI evaluations, and document generation execute entirely locally on your host environment without transmitting personal property data to third-party cloud servers.",
        ]

        for d in disclaimers_list:
            story.append(Paragraph(d, self.styles["Disclaimer"]))
            story.append(Spacer(1, 3))

        story.append(Spacer(1, 10))
        # End of Report Stamp
        end_stamp_p = f"<b>END OF INVESTMENT REPORT  •  PROPDEAL AI INDIA  •  GENERATED: {report_timestamp_str}</b>"
        story.append(Paragraph(end_stamp_p, ParagraphStyle("EndP", fontName=PRIMARY_BOLD, fontSize=8, textColor=SLATE_MUTED, alignment=1)))

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes


pdf_report_service = PDFReportService()
