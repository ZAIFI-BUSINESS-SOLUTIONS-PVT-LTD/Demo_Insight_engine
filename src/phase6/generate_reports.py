"""
Phase 6: PDF Report Generator
Combines phase4 (test scores) and phase5 (insights) into per-student PDFs
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from svglib.svglib import svg2rlg
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from src.utils.logger import setup_logger
from dotenv import load_dotenv

logger = setup_logger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
PHASE4_DIR = BASE_DIR / "output" / "phase4" / "students"
PHASE5_FILE = BASE_DIR / "output" / "phase5" / "student_pattern_insights.json"
OUTPUT_DIR = BASE_DIR / "output" / "phase6" / "reports"
CHARTS_DIR = BASE_DIR / "output" / "phase6" / "charts"
TEMPLATE_DIR = Path(__file__).parent


def calculate_score(correct: int, incorrect: int, unattempted: int) -> float:
    """
    Calculate score: +4 for correct, -1 for incorrect, 0 for unattempted
    """
    return (correct * 4) + (incorrect * -1) + (unattempted * 0)


def classify_answer(correct_option: str, student_selected_option: str) -> str:
    """
    Classify answer as correct/incorrect/unattempted
    
    Args:
        correct_option: The correct answer (e.g., "A", "B")
        student_selected_option: Student's answer (e.g., "A", "" for unattempted)
    
    Returns:
        "correct", "incorrect", or "unattempted"
    """
    if not student_selected_option or student_selected_option.strip() == "":
        return "unattempted"
    elif student_selected_option == correct_option:
        return "correct"
    else:
        return "incorrect"


def load_student_data(student_id: str) -> Optional[Dict]:
    """Load phase4 JSON for a student"""
    student_file = PHASE4_DIR / f"{student_id}.json"
    
    if not student_file.exists():
        logger.warning(f"Student file not found: {student_file}")
        return None
    
    try:
        with open(student_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading student {student_id}: {e}")
        return None


def load_phase5_insights() -> Dict[str, List[Dict]]:
    """
    Load phase5 insights JSON
    Returns dict: {student_id: [list of 5 insights]}
    """
    if not PHASE5_FILE.exists():
        logger.warning(f"Phase 5 insights not found: {PHASE5_FILE}")
        return {}
    
    try:
        with open(PHASE5_FILE, "r", encoding="utf-8") as f:
            insights_list = json.load(f)
        
        # Group by student_id
        insights_by_student = defaultdict(list)
        for insight in insights_list:
            student_id = insight.get("student_id")
            if student_id:
                insights_by_student[student_id].append(insight)
        
        return dict(insights_by_student)
    
    except Exception as e:
        logger.error(f"Error loading phase5 insights: {e}")
        return {}


def aggregate_test_subject_scores(records: List[Dict]) -> Dict[str, Dict[str, Dict]]:
    """
    Aggregate records by test_name and subject
    
    Returns:
        {
            "class_7": {
                "Chemistry": {"correct": 10, "incorrect": 5, "unattempted": 2, "score": 35},
                "Physics": {...}
            },
            "class_8": {...}
        }
    """
    aggregated = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "incorrect": 0, "unattempted": 0}))
    
    for record in records:
        test_name = record.get("test_name", "Unknown")
        subject = record.get("subject", "Unknown")
        correct_option = record.get("correct_option", "")
        student_selected = record.get("student_selected_option", "")
        
        # Classify the answer
        classification = classify_answer(correct_option, student_selected)
        
        # Increment count
        aggregated[test_name][subject][classification] += 1
    
    # Calculate scores
    result = {}
    for test_name, subjects in aggregated.items():
        result[test_name] = {}
        for subject, counts in subjects.items():
            correct = counts["correct"]
            incorrect = counts["incorrect"]
            unattempted = counts["unattempted"]
            score = calculate_score(correct, incorrect, unattempted)
            
            result[test_name][subject] = {
                "correct": correct,
                "incorrect": incorrect,
                "unattempted": unattempted,
                "score": score,
                "total": correct + incorrect + unattempted
            }
    
    return result


def create_test_chart(test_name: str, subject_scores: Dict[str, Dict], student_id: str) -> str:
    """
    Create a bar chart for a single test showing subject-wise scores
    
    Returns:
        Path to saved chart PNG
    """
    subjects = list(subject_scores.keys())
    scores = [subject_scores[subj]["score"] for subj in subjects]
    correct = [subject_scores[subj]["correct"] for subj in subjects]
    incorrect = [subject_scores[subj]["incorrect"] for subj in subjects]
    unattempted = [subject_scores[subj]["unattempted"] for subj in subjects]
    
    # Normalize test title for display and filename
    if not test_name or str(test_name).strip() == "":
        test_title = "Unnamed Test"
    else:
        test_title = str(test_name).replace('_', ' ').title()
    # Safe filename: keep alnum, dash, underscore
    safe_test_name = re.sub(r'[^A-Za-z0-9_-]', '_', str(test_name).strip().replace(' ', '_'))

    # Create stacked bar chart with modern styling (no data labels)
    fig = go.Figure()

    # Correct: show positive score contribution
    fig.add_trace(go.Bar(
        name='Correct (+4)',
        x=subjects,
        y=[c * 4 for c in correct],
        marker_color='#2ecc71'
    ))

    # Incorrect: negative contribution
    fig.add_trace(go.Bar(
        name='Incorrect (-1)',
        x=subjects,
        y=[i * -1 for i in incorrect],
        marker_color='#e74c3c'
    ))

    # Unattempted: zero contribution, show counts instead of score
    fig.add_trace(go.Bar(
        name='Unattempted',
        x=subjects,
        y=[0 for _ in unattempted],
        marker_color='#95a5a6'
    ))

    # Global styling for crisp PDF rendering
    fig.update_layout(
        title=f"Test: {test_title} - Subject-wise Performance",
        xaxis_title="Subject",
        yaxis_title="Score Contribution",
        barmode='relative',
        height=400,
        template="plotly_white",
        font=dict(size=14, family='Arial'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=True
    )

    # Add net score annotation
    total_score = sum(scores)
    fig.add_annotation(
        text=f"Total Score: {total_score}",
        xref="paper", yref="paper",
        x=0.5, y=1.08,
        showarrow=False,
        font=dict(size=12, color="black")
    )

    # Save chart as SVG (vector)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_path = CHARTS_DIR / f"{student_id}_{safe_test_name}.svg"
    fig.write_image(str(chart_path), engine="kaleido")

    logger.debug(f"Created chart: {chart_path}")
    return str(chart_path)


def generate_pdf_report(student_id: str, student_data: Dict, insights: List[Dict]) -> str:
    """
    Generate PDF report for a student using ReportLab
    
    Returns:
        Path to generated PDF
    """
    logger.info(f"Generating PDF report for student {student_id}")
    
    # Aggregate test-subject scores
    records = student_data.get("records", [])
    test_subject_scores = aggregate_test_subject_scores(records)
    
    # Create PDF
    pdf_path = OUTPUT_DIR / f"{student_id}_report.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for elements
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        leftIndent=0
    )
    
    insight_heading_style = ParagraphStyle(
        'InsightHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=8
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        alignment=TA_LEFT
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        leftIndent=0
    )
    
    # Title
    story.append(Paragraph("Student Performance Report", title_style))
    story.append(Paragraph(f"<b>Student ID:</b> {student_id} | <b>Total Questions:</b> {student_data.get('total_records', 0)}", body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Test Performance Section
    story.append(Paragraph("Test-wise Performance Analysis", heading_style))
    
    # Generate charts for each test
    for test_name, subject_scores in test_subject_scores.items():
        chart_path = create_test_chart(test_name, subject_scores, student_id)
        
        # Add test name (normalized for clarity)
        if not test_name or str(test_name).strip() == "":
            display_test = "Unnamed Test"
        else:
            display_test = str(test_name).replace('_', ' ').title()
        story.append(Paragraph(f"<b>{display_test}</b>", insight_heading_style))
        
        # Add chart (SVG via svglib -> ReportLab drawing)
        try:
            drawing = svg2rlg(str(chart_path))
            if getattr(drawing, 'width', None) and drawing.width > 0:
                scale = (6.5 * inch) / drawing.width
                drawing.scale(scale, scale)
            story.append(drawing)
            story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            logger.warning(f"SVG embedding failed for {chart_path}: {e}")
            try:
                # Fallback: use PNG if available
                png_path = str(chart_path).replace('.svg', '.png')
                from reportlab.platypus import Image as RLImage
                if os.path.exists(png_path):
                    img = RLImage(png_path, width=6.5*inch, height=3.5*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
            except Exception:
                pass
        
        # Add subject details table
        table_data = [['Subject', 'Correct', 'Incorrect', 'Unattempted', 'Total', 'Score']]
        for subject, stats in sorted(subject_scores.items()):
            table_data.append([
                subject,
                str(stats['correct']),
                str(stats['incorrect']),
                str(stats['unattempted']),
                str(stats['total']),
                str(stats['score'])
            ])
        
        table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1*inch, 0.7*inch, 0.7*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9f9f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
    
    # Pattern Insights Section
    story.append(PageBreak())
    story.append(Paragraph("Learning Pattern Insights", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    if insights:
        # Sort by rank
        sorted_insights = sorted(insights, key=lambda x: x.get("insight_rank", 999))
        
        for insight in sorted_insights:
            rank = insight.get("insight_rank", "?")
            topic = insight.get("topic", "Unknown")
            subject = insight.get("subject", "Unknown")
            accuracy = insight.get("accuracy", 0.0)
            problem = insight.get("problem", "")
            action = insight.get("action", "")
            citation = insight.get("citation", "")
            
            # Insight header
            story.append(Paragraph(
                f"<b>Priority #{rank}: {topic}</b> (Accuracy: {accuracy:.1f}%)",
                insight_heading_style
            ))
            story.append(Paragraph(f"<i>Subject: {subject}</i>", label_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Problem
            story.append(Paragraph("<b>Problem Identified:</b>", label_style))
            story.append(Paragraph(problem or "Not specified.", body_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Action
            story.append(Paragraph("<b>Recommended Action:</b>", label_style))
            story.append(Paragraph(action or "No action provided.", body_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Citation
            story.append(Paragraph("<b>Evidence:</b>", label_style))
            story.append(Paragraph(f"<i>{(citation or 'No evidence provided.')}</i>", body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Separator
            story.append(Spacer(1, 0.1*inch))
    else:
        story.append(Paragraph("No pattern insights available for this student yet.", body_style))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | © Pace Analytics"
    story.append(Paragraph(footer_text, label_style))
    
    # Build PDF
    doc.build(story)
    
    logger.info(f"PDF report generated: {pdf_path}")
    return str(pdf_path)


def process(target_student_id: Optional[str] = None) -> int:
    """
    Main processing function for Phase 6
    
    Args:
        target_student_id: If specified, generate report only for this student
    
    Returns:
        Number of reports generated
    """
    logger.info("Starting Phase 6 PDF report generation")
    
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # If target_student_id not provided, check env var PHASE6_STUDENT_ID
    if not target_student_id:
        load_dotenv()
        env_student = os.getenv("PHASE6_STUDENT_ID", "").strip()
        if env_student:
            target_student_id = env_student

    # Load phase5 insights
    all_insights = load_phase5_insights()
    
    # Get list of students
    if target_student_id:
        student_ids = [target_student_id]
        logger.info(f"Generating report for single student: {target_student_id}")
    else:
        # Get all students from phase4 directory
        student_files = list(PHASE4_DIR.glob("*.json"))
        student_ids = [f.stem for f in student_files if f.stem != "_index"]
        logger.info(f"Generating reports for {len(student_ids)} students")
    
    # Generate reports
    report_count = 0
    for student_id in student_ids:
        try:
            # Load student data
            student_data = load_student_data(student_id)
            if not student_data:
                logger.warning(f"Skipping student {student_id}: no data")
                continue
            
            # Get insights (may be empty)
            insights = all_insights.get(student_id, [])
            if not insights:
                logger.warning(f"No insights found for student {student_id}, proceeding without insights")
            
            # Generate PDF
            pdf_path = generate_pdf_report(student_id, student_data, insights)
            report_count += 1
            
            logger.info(f"[{report_count}/{len(student_ids)}] Report generated: {pdf_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate report for student {student_id}: {e}", exc_info=True)
            continue
    
    logger.info(f"Phase 6 complete: {report_count} reports generated")
    return report_count


if __name__ == "__main__":
    # Load .env and allow optional PHASE6_STUDENT_ID override
    load_dotenv()
    env_student = os.getenv("PHASE6_STUDENT_ID", "").strip()
    if env_student:
        logger.info(f"PHASE6_STUDENT_ID set: generating report only for {env_student}")
        process(target_student_id=env_student)
    else:
        process()
