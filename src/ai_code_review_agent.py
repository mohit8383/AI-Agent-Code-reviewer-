#!/usr/bin/env python3
"""
AI Code Review Agent
A comprehensive code analysis and improvement tool that reviews codebases 
and generates improved versions with detailed reports.
"""

import os
import sys
import json
import ast
import re
import shutil
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import argparse
import logging
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code_review_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggestion: str
    original_code: str = ""
    improved_code: str = ""

@dataclass
class ReviewMetrics:
    """Code quality metrics before and after review"""
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    code_smells: int = 0
    security_issues: int = 0
    performance_issues: int = 0
    documentation_coverage: float = 0.0

@dataclass
class ReviewConfig:
    """Configuration for the code review process"""
    priorities: List[str] = None
    excluded_patterns: List[str] = None
    style_guide: str = "pep8"
    max_complexity: int = 10
    include_documentation: bool = True
    fix_security_issues: bool = True
    optimize_performance: bool = True

    def __post_init__(self):
        if self.priorities is None:
            self.priorities = ["security", "performance", "readability"]
        if self.excluded_patterns is None:
            self.excluded_patterns = ["__pycache__", ".git", ".venv", "node_modules"]

class CodeAnalyzer:
    """Analyzes code for various issues and improvements"""
    
    SUPPORTED_EXTENSIONS = {'.py', '.js', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go'}
    
    def __init__(self, config: ReviewConfig):
        self.config = config
        self.issues: List[CodeIssue] = []
    
    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a single file for issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            if file_path.suffix == '.py':
                issues.extend(self._analyze_python_file(file_path, content, lines))
            elif file_path.suffix in ['.js', '.jsx']:
                issues.extend(self._analyze_javascript_file(file_path, content, lines))
            else:
                issues.extend(self._analyze_generic_file(file_path, content, lines))
                
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=1,
                issue_type="analysis_error",
                severity="low",
                description=f"Could not analyze file: {e}",
                suggestion="Check file encoding and syntax"
            ))
        
        return issues
    
    def _analyze_python_file(self, file_path: Path, content: str, lines: List[str]) -> List[CodeIssue]:
        """Analyze Python-specific issues"""
        issues = []
        
        try:
            # Parse AST for syntax checking
            tree = ast.parse(content)
            
            # Check for common Python issues
            for i, line in enumerate(lines, 1):
                # Long lines
                if len(line) > 100:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="style",
                        severity="low",
                        description="Line too long (>100 characters)",
                        suggestion="Break line into multiple lines",
                        original_code=line
                    ))
                
                # Missing docstrings for functions/classes
                if line.strip().startswith(('def ', 'class ')) and not lines[i].strip().startswith('"""'):
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="documentation",
                        severity="medium",
                        description="Missing docstring",
                        suggestion="Add descriptive docstring",
                        original_code=line
                    ))
                
                # Security: eval() usage
                if 'eval(' in line:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="security",
                        severity="high",
                        description="Use of eval() function is dangerous",
                        suggestion="Use ast.literal_eval() or safer alternatives",
                        original_code=line
                    ))
                
                # Performance: inefficient string concatenation
                if '+=' in line and 'str' in line.lower():
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="performance",
                        severity="medium",
                        description="Inefficient string concatenation",
                        suggestion="Use join() or f-strings for better performance",
                        original_code=line
                    ))
            
            # Analyze AST for complexity
            complexity = self._calculate_complexity(tree)
            if complexity > self.config.max_complexity:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=1,
                    issue_type="complexity",
                    severity="high",
                    description=f"High cyclomatic complexity: {complexity}",
                    suggestion="Consider breaking down into smaller functions"
                ))
                
        except SyntaxError as e:
            issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=e.lineno or 1,
                issue_type="syntax",
                severity="high",
                description=f"Syntax error: {e.msg}",
                suggestion="Fix syntax error"
            ))
        
        return issues
    
    def _analyze_javascript_file(self, file_path: Path, content: str, lines: List[str]) -> List[CodeIssue]:
        """Analyze JavaScript-specific issues"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Use of var instead of let/const
            if re.search(r'\bvar\s+\w+', line):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="modernization",
                    severity="medium",
                    description="Use of 'var' keyword",
                    suggestion="Use 'let' or 'const' instead of 'var'",
                    original_code=line
                ))
            
            # Missing semicolons
            if line.strip() and not line.strip().endswith((';', '{', '}', ')', ',')):
                if not line.strip().startswith(('if', 'for', 'while', 'function', 'class')):
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="style",
                        severity="low",
                        description="Missing semicolon",
                        suggestion="Add semicolon at end of statement",
                        original_code=line
                    ))
        
        return issues
    
    def _analyze_generic_file(self, file_path: Path, content: str, lines: List[str]) -> List[CodeIssue]:
        """Analyze generic code issues"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # TODO comments
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="maintenance",
                    severity="low",
                    description="TODO/FIXME comment found",
                    suggestion="Complete the pending task",
                    original_code=line
                ))
            
            # Long lines (generic)
            if len(line) > 120:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="style",
                    severity="low",
                    description="Line too long",
                    suggestion="Break into multiple lines",
                    original_code=line
                ))
        
        return issues
    
    def _calculate_complexity(self, tree) -> int:
        """Calculate cyclomatic complexity of Python AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

class CodeImprover:
    """Improves code based on identified issues"""
    
    def __init__(self, config: ReviewConfig):
        self.config = config
    
    def improve_file(self, file_path: Path, issues: List[CodeIssue]) -> str:
        """Generate improved version of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            improved_lines = lines.copy()
            
            # Sort issues by line number in reverse order to avoid index issues
            sorted_issues = sorted(issues, key=lambda x: x.line_number, reverse=True)
            
            for issue in sorted_issues:
                if issue.line_number <= len(improved_lines):
                    improved_lines[issue.line_number - 1] = self._apply_fix(
                        improved_lines[issue.line_number - 1], issue
                    )
            
            # Add file header documentation if missing
            if file_path.suffix == '.py' and not content.startswith('"""'):
                header = self._generate_file_header(file_path)
                improved_lines.insert(0, header)
            
            return '\n'.join(improved_lines)
            
        except Exception as e:
            logger.error(f"Error improving {file_path}: {e}")
            return content  # Return original if improvement fails
    
    def _apply_fix(self, line: str, issue: CodeIssue) -> str:
        """Apply a specific fix to a line of code"""
        if issue.issue_type == "style" and "Line too long" in issue.description:
            # Simple line breaking for demonstration
            if len(line) > 100 and ',' in line:
                parts = line.split(',')
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    return ',\n'.join([parts[0]] + [' ' * (indent + 4) + part.strip() for part in parts[1:]])
        
        elif issue.issue_type == "security" and "eval(" in line:
            return line.replace("eval(", "ast.literal_eval(")
        
        elif issue.issue_type == "modernization" and "var " in line:
            return line.replace("var ", "const ")
        
        elif issue.issue_type == "style" and "Missing semicolon" in issue.description:
            if not line.rstrip().endswith(';'):
                return line.rstrip() + ';'
        
        elif issue.issue_type == "documentation" and "Missing docstring" in issue.description:
            indent = len(line) - len(line.lstrip())
            docstring = ' ' * (indent + 4) + '"""Add description here"""'
            return line + '\n' + docstring
        
        return line  # Return unchanged if no specific fix available
    
    def _generate_file_header(self, file_path: Path) -> str:
        """Generate a file header with documentation"""
        return f'"""\n{file_path.name}\n\nModule description goes here.\n\nAuthor: AI Code Review Agent\nDate: {datetime.now().strftime("%Y-%m-%d")}\n"""\n'

class ReportGenerator:
    """Generates detailed reports of the code review process"""
    
    def generate_report(self, issues: List[CodeIssue], metrics_before: ReviewMetrics, 
                       metrics_after: ReviewMetrics, output_dir: Path) -> None:
        """Generate comprehensive review report"""
        
        report_data = {
            "summary": self._generate_summary(issues, metrics_before, metrics_after),
            "issues": [asdict(issue) for issue in issues],
            "metrics": {
                "before": asdict(metrics_before),
                "after": asdict(metrics_after)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # Generate JSON report
        json_path = output_dir / "review_report.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_path = output_dir / "review_report.html"
        self._generate_html_report(report_data, html_path)
        
        # Generate Markdown report
        md_path = output_dir / "review_report.md"
        self._generate_markdown_report(report_data, md_path)
        
        logger.info(f"Reports generated: {json_path}, {html_path}, {md_path}")
    
    def _generate_summary(self, issues: List[CodeIssue], metrics_before: ReviewMetrics, 
                         metrics_after: ReviewMetrics) -> Dict[str, Any]:
        """Generate summary statistics"""
        issue_counts = {}
        severity_counts = {}
        
        for issue in issues:
            issue_counts[issue.issue_type] = issue_counts.get(issue.issue_type, 0) + 1
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        return {
            "total_issues": len(issues),
            "issues_by_type": issue_counts,
            "issues_by_severity": severity_counts,
            "files_processed": len(set(issue.file_path for issue in issues)),
            "improvement_metrics": {
                "complexity_reduction": metrics_before.cyclomatic_complexity - metrics_after.cyclomatic_complexity,
                "security_fixes": metrics_before.security_issues - metrics_after.security_issues,
                "performance_improvements": metrics_before.performance_issues - metrics_after.performance_issues
            }
        }
    
    def _generate_html_report(self, report_data: Dict, output_path: Path) -> None:
        """Generate HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Code Review Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; }}
                .summary {{ margin: 20px 0; }}
                .issue {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
                .high {{ border-left: 5px solid #ff0000; }}
                .medium {{ border-left: 5px solid #ff9900; }}
                .low {{ border-left: 5px solid #00aa00; }}
                .metrics {{ display: flex; gap: 20px; }}
                .metric-box {{ border: 1px solid #ccc; padding: 15px; flex: 1; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AI Code Review Report</h1>
                <p>Generated: {report_data['generated_at']}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Issues Found: {report_data['summary']['total_issues']}</p>
                <p>Files Processed: {report_data['summary']['files_processed']}</p>
            </div>
            
            <div class="metrics">
                <div class="metric-box">
                    <h3>Before Review</h3>
                    <p>Lines of Code: {report_data['metrics']['before']['lines_of_code']}</p>
                    <p>Cyclomatic Complexity: {report_data['metrics']['before']['cyclomatic_complexity']}</p>
                    <p>Security Issues: {report_data['metrics']['before']['security_issues']}</p>
                </div>
                <div class="metric-box">
                    <h3>After Review</h3>
                    <p>Lines of Code: {report_data['metrics']['after']['lines_of_code']}</p>
                    <p>Cyclomatic Complexity: {report_data['metrics']['after']['cyclomatic_complexity']}</p>
                    <p>Security Issues: {report_data['metrics']['after']['security_issues']}</p>
                </div>
            </div>
            
            <div class="issues">
                <h2>Issues Found</h2>
        """
        
        for issue in report_data['issues']:
            html_content += f"""
                <div class="issue {issue['severity']}">
                    <h4>{issue['issue_type'].title()}: {issue['description']}</h4>
                    <p><strong>File:</strong> {issue['file_path']} (Line {issue['line_number']})</p>
                    <p><strong>Severity:</strong> {issue['severity'].title()}</p>
                    <p><strong>Suggestion:</strong> {issue['suggestion']}</p>
                    {f"<pre><code>{issue['original_code']}</code></pre>" if issue['original_code'] else ""}
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, report_data: Dict, output_path: Path) -> None:
        """Generate Markdown report"""
        md_content = f"""# AI Code Review Report

**Generated:** {report_data['generated_at']}

## Summary

- **Total Issues Found:** {report_data['summary']['total_issues']}
- **Files Processed:** {report_data['summary']['files_processed']}

### Issues by Type
"""
        
        for issue_type, count in report_data['summary']['issues_by_type'].items():
            md_content += f"- {issue_type.title()}: {count}\n"
        
        md_content += "\n### Issues by Severity\n"
        for severity, count in report_data['summary']['issues_by_severity'].items():
            md_content += f"- {severity.title()}: {count}\n"
        
        md_content += f"""
## Metrics Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines of Code | {report_data['metrics']['before']['lines_of_code']} | {report_data['metrics']['after']['lines_of_code']} | - |
| Cyclomatic Complexity | {report_data['metrics']['before']['cyclomatic_complexity']} | {report_data['metrics']['after']['cyclomatic_complexity']} | {report_data['summary']['improvement_metrics']['complexity_reduction']} |
| Security Issues | {report_data['metrics']['before']['security_issues']} | {report_data['metrics']['after']['security_issues']} | {report_data['summary']['improvement_metrics']['security_fixes']} |

## Issues Details

"""
        
        for issue in report_data['issues']:
            md_content += f"""### {issue['issue_type'].title()}: {issue['description']}

- **File:** {issue['file_path']} (Line {issue['line_number']})
- **Severity:** {issue['severity'].title()}
- **Suggestion:** {issue['suggestion']}

"""
            if issue['original_code']:
                md_content += f"```\n{issue['original_code']}\n```\n\n"
        
        with open(output_path, 'w') as f:
            f.write(md_content)

class AICodeReviewAgent:
    """Main AI Code Review Agent class"""
    
    def __init__(self, config: ReviewConfig = None):
        self.config = config or ReviewConfig()
        self.analyzer = CodeAnalyzer(self.config)
        self.improver = CodeImprover(self.config)
        self.reporter = ReportGenerator()
    
    def review_codebase(self, input_path: str, output_path: str = None) -> None:
        """Main method to review a complete codebase"""
        input_path = Path(input_path)
        
        if output_path is None:
            output_path = input_path.parent / f"{input_path.name}_improved"
        else:
            output_path = Path(output_path)
        
        logger.info(f"Starting code review: {input_path} -> {output_path}")
        
        # Extract if ZIP file
        if input_path.suffix == '.zip':
            input_path = self._extract_zip(input_path)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        improved_code_path = output_path / "improved_code"
        improved_code_path.mkdir(exist_ok=True)
        
        # Collect all code files
        code_files = self._collect_code_files(input_path)
        logger.info(f"Found {len(code_files)} code files to review")
        
        # Calculate initial metrics
        metrics_before = self._calculate_metrics(code_files)
        
        # Analyze all files
        all_issues = []
        for file_path in code_files:
            logger.info(f"Analyzing: {file_path}")
            issues = self.analyzer.analyze_file(file_path)
            all_issues.extend(issues)
        
        logger.info(f"Found {len(all_issues)} total issues")
        
        # Improve files and copy to output
        improved_files = []
        for file_path in code_files:
            relative_path = file_path.relative_to(input_path)
            output_file_path = improved_code_path / relative_path
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get issues for this file
            file_issues = [issue for issue in all_issues if issue.file_path == str(file_path)]
            
            # Improve the file
            improved_content = self.improver.improve_file(file_path, file_issues)
            
            # Write improved file
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(improved_content)
            
            improved_files.append(output_file_path)
        
        # Calculate metrics after improvement
        metrics_after = self._calculate_metrics(improved_files)
        
        # Generate reports
        self.reporter.generate_report(all_issues, metrics_before, metrics_after, output_path)
        
        # Copy non-code files
        self._copy_non_code_files(input_path, improved_code_path)
        
        logger.info(f"Code review completed! Results saved to: {output_path}")
        logger.info(f"View the HTML report: {output_path / 'review_report.html'}")
    
    def _extract_zip(self, zip_path: Path) -> Path:
        """Extract ZIP file and return extraction path"""
        extract_path = zip_path.parent / zip_path.stem
        extract_path.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        return extract_path
    
    def _collect_code_files(self, root_path: Path) -> List[Path]:
        """Collect all code files from the directory"""
        code_files = []
        
        for file_path in root_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in CodeAnalyzer.SUPPORTED_EXTENSIONS:
                # Check if file should be excluded
                if not any(pattern in str(file_path) for pattern in self.config.excluded_patterns):
                    code_files.append(file_path)
        
        return code_files
    
    def _calculate_metrics(self, file_paths: List[Path]) -> ReviewMetrics:
        """Calculate code quality metrics"""
        metrics = ReviewMetrics()
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    metrics.lines_of_code += len([line for line in lines if line.strip()])
                
                # Simple complexity calculation
                if file_path.suffix == '.py':
                    try:
                        tree = ast.parse(content)
                        metrics.cyclomatic_complexity += self.analyzer._calculate_complexity(tree)
                    except:
                        pass
                
            except Exception as e:
                logger.error(f"Error calculating metrics for {file_path}: {e}")
        
        return metrics
    
    def _copy_non_code_files(self, source_path: Path, dest_path: Path) -> None:
        """Copy non-code files to the improved directory"""
        for file_path in source_path.rglob('*'):
            if file_path.is_file() and file_path.suffix not in CodeAnalyzer.SUPPORTED_EXTENSIONS:
                if not any(pattern in str(file_path) for pattern in self.config.excluded_patterns):
                    relative_path = file_path.relative_to(source_path)
                    dest_file_path = dest_path / relative_path
                    dest_file_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_file_path)

def main():
    """Main entry point for the AI Code Review Agent"""
    parser = argparse.ArgumentParser(description="AI Code Review Agent")
    parser.add_argument("input_path", help="Path to codebase (folder or ZIP file)")
    parser.add_argument("-o", "--output", help="Output directory for improved code")
    parser.add_argument("--priorities", nargs='+', default=["security", "performance", "readability"],
                       help="Review priorities")
    parser.add_argument("--exclude", nargs='+', default=["__pycache__", ".git", ".venv"],
                       help="Patterns to exclude")
    parser.add_argument("--max-complexity", type=int, default=10,
                       help="Maximum cyclomatic complexity threshold")
    parser.add_argument("--style-guide", default="pep8", help="Code style guide to follow")
    
    args = parser.parse_args()
    
    # Create configuration
    config = ReviewConfig(
        priorities=args.priorities,
        excluded_patterns=args.exclude,
        max_complexity=args.max_complexity,
        style_guide=args.style_guide
    )
    
    # Initialize and run the agent
    agent = AICodeReviewAgent(config)
    
    try:
        agent.review_codebase(args.input_path, args.output)
        print("\n✅ Code review completed successfully!")
        print(f"📁 Check the output directory: {args.output or args.input_path + '_improved'}")
        print("📊 Open the HTML report to view detailed results")
        
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()