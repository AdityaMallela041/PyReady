"""Report generation module for OnboardAI"""

from pyready.reporting.generator import generate_report, export_json, export_markdown
from pyready.reporting.diff import (
    diff_reports,
    export_diff_json,
    export_diff_markdown
)

__all__ = [
    'generate_report',
    'export_json',
    'export_markdown',
    'diff_reports',
    'export_diff_json',
    'export_diff_markdown'
]
