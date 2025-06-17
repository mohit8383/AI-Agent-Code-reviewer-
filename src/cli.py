#!/usr/bin/env python3
"""
AI Code Review Agent - Command Line Interface
A powerful CLI tool for automated code analysis and review
"""

import argparse
import requests
import json
import time
import os
import sys
from pathlib import Path
import mimetypes
from typing import List, Dict, Optional
import zipfile
import tempfile
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from rich.prompt import Prompt, Confirm
import yaml

console = Console()

class CodeReviewCLI:
    """Command Line Interface for AI Code Review Agent"""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        
    def check_server_health(self) -> bool:
        """Check if the server is running and healthy"""
        try:
            response = self.session.get(f"{self.server_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from file"""
        if not os.path.exists(config_file):
            console.print(f"[yellow]Config file {config_file} not found, using defaults[/yellow]")
            return self.get_default_config()
        
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "analysis": {
                "security": True,
                "performance": True,
                "style": True,
                "complexity": True
            },
            "rules": {
                "styleGuide": "pep8",
                "maxLineLength": 120,
                "maxComplexity": 10,
                "allowUnsafeOperations": False
            },
            "output": {
                "format": "detailed",
                "includeFixSuggestions": True,
                "generateReport": True
            },
            "filters": {
                "minSeverity": "low",
                "excludeFiles": [".git/*", "node_modules/*", "*.min.js"],
                "includeTests": True
            }
        }
    
    def discover_files(self, paths: List[str], extensions: List[str] = None) -> List[str]:
        """Discover code files from given paths"""
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs']
        
        files = []
        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                if any(path.suffix == ext for ext in extensions):
                    files.append(str(path))
            elif path.is_dir():
                for ext in extensions:
                    files.extend([str(f) for f in path.rglob(f'*{ext}')])
        
        return sorted(list(set(files)))
    
    def upload_files(self, files: List[str], config: Dict) -> Optional[str]:
        """Upload files to server and start analysis"""
        if not files:
            console.print("[red]No files to upload[/red]")
            return None
        
        console.print(f"[blue]Uploading {len(files)} files for analysis...[/blue]")
        
        try:
            # Prepare files for upload
            files_data = []
            for file_path in files:
                if os.path.exists(file_path):
                    files_data.append(('files', (os.path.basename(file_path), open(file_path, 'rb'))))
            
            # Upload files
            data = {'config': json.dumps(config)}
            response = self.session.post(
                f"{self.server_url}/api/review/start",
                files=files_data,
                data=data,
                timeout=30
            )
            
            # Close file handles
            for _, (_, file_handle) in files_data:
                file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"[green]✓ Analysis started with session ID: {result['session_id']}[/green]")
                return result['session_id']
            else:
                console.print(f"[red]Upload failed: {response.text}[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]Upload error: {e}[/red]")
            return None
    
    def wait_for_completion(self, session_id: str) -> Optional[Dict]:
        """Wait for analysis to complete with progress tracking"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Analyzing code...", total=100)
            
            while True:
                try:
                    response = self.session.get(f"{self.server_url}/api/review/{session_id}/status")
                    if response.status_code != 200:
                        console.print(f"[red]Error getting status: {response.text}[/red]")
                        return None
                    
                    status = response.json()
                    progress.update(task, completed=status['progress'], description=status['current_step'])
                    
                    if status['status'] == 'completed':
                        progress.update(task, completed=100, description="Analysis complete!")
                        return self.get_results(session_id)
                    elif status['status'] == 'failed':
                        console.print(f"[red]Analysis failed: {status.get('error', 'Unknown error')}[/red]")
                        return None
                    
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Analysis interrupted by user[/yellow]")
                    return None
                except Exception as e:
                    console.print(f"[red]Error checking status: {e}[/red]")
                    return None
    
    def get_results(self, session_id: str) -> Optional[Dict]:
        """Get analysis results"""
        try:
            response = self.session.get(f"{self.server_url}/api/review/{session_id}/results")
            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red]Error getting results: {response.text}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error fetching results: {e}[/red]")
            return None
    
    def display_results(self, results: Dict, format_type: str = "detailed"):
        """Display analysis results"""
        if format_type == "json":
            console.print_json(data=results)
            return
        
        # Display header
        panel = Panel.fit(
            "[bold blue]🤖 AI Code Review Results[/bold blue]",
            border_style="blue"
        )
        console.print(panel)
        
        # Display metrics
        metrics = results.get('metrics', {})
        
        metrics_table = Table(title="📊 Analysis Metrics", show_header=True, header_style="bold magenta")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        metrics_table.add_row("Files Processed", str(metrics.get('filesProcessed', 0)))
        metrics_table.add_row("Total Issues", str(metrics.get('totalIssues', 0)))
        metrics_table.add_row("Security Issues", str(metrics.get('securityIssues', 0)))
        metrics_table.add_row("Performance Issues", str(metrics.get('performanceIssues', 0)))
        metrics_table.add_row("Style Issues", str(metrics.get('styleIssues', 0)))
        metrics_table.add_row("Code Quality Score", f"{metrics.get('codeQualityScore', 0)}/100")
        
        console.print(metrics_table)
        console.print()
        
        # Display issues
        issues = results.get('issues', [])
        if issues:
            issues_table = Table(title="🐛 Issues Found", show_header=True, header_style="bold red")
            issues_table.add_column("Severity", style="bold")
            issues_table.add_column("Type", style="cyan")
            issues_table.add_column("File", style="blue")
            issues_table.add_column("Line", style="magenta")
            issues_table.add_column("Description", style="white")
            
            for issue in issues[:20]:  # Show first 20 issues
                severity_color = {
                    'high': 'red',
                    'medium': 'yellow', 
                    'low': 'green'
                }.get(issue.get('severity', 'low'), 'white')
                
                issues_table.add_row(
                    f"[{severity_color}]{issue.get('severity', 'N/A').upper()}[/{severity_color}]",
                    issue.get('type', 'N/A'),
                    issue.get('file', 'N/A'),
                    str(issue.get('line', 'N/A')),
                    issue.get('description', 'N/A')[:60] + ('...' if len(issue.get('description', '')) > 60 else '')
                )
            
            console.print(issues_table)
            
            if len(issues) > 20:
                console.print(f"[yellow]... and {len(issues) - 20} more issues[/yellow]")
        
        # Display recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            console.print()
            recs_panel = Panel(
                "\n".join(f"• {rec}" for rec in recommendations),
                title="💡 Recommendations",
                border_style="green"
            )
            console.print(recs_panel)
    
    def download_report(self, session_id: str, output_file: str = None):
        """Download HTML report"""
        try:
            response = self.session.get(f"{self.server_url}/api/review/{session_id}/report")
            if response.status_code == 200:
                if output_file is None:
                    output_file = f"code_review_report_{session_id}.html"
                
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                console.print(f"[green]✓ Report saved to {output_file}[/green]")
                
                if Confirm.ask("Open report in browser?"):
                    import webbrowser
                    webbrowser.open(f"file://{os.path.abspath(output_file)}")
            else:
                console.print(f"[red]Error downloading report: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error downloading report: {e}[/red]")
    
    def download_improved_code(self, session_id: str, output_file: str = None):
        """Download improved code package"""
        try:
            response = self.session.get(f"{self.server_url}/api/review/{session_id}/download")
            if response.status_code == 200:
                if output_file is None:
                    output_file = f"improved_code_{session_id}.zip"
                
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                console.print(f"[green]✓ Improved code saved to {output_file}[/green]")
            else:
                console.print(f"[red]Error downloading improved code: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error downloading improved code: {e}[/red]")

def create_sample_config():
    """Create a sample configuration file"""
    config = {
        "analysis": {
            "security": True,
            "performance": True,
            "style": True,
            "complexity": True
        },
        "rules": {
            "styleGuide": "pep8",
            "maxLineLength": 120,
            "maxComplexity": 10,
            "allowUnsafeOperations": False
        },
        "output": {
            "format": "detailed",
            "includeFixSuggestions": True,
            "generateReport": True
        },
        "filters": {
            "minSeverity": "low",
            "excludeFiles": [".git/*", "node_modules/*", "*.min.js", "__pycache__/*"],
            "includeTests": True
        }
    }
    
    with open('code_review_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    console.print("[green]✓ Sample configuration created: code_review_config.yaml[/green]")

def main():
    parser = argparse.ArgumentParser(
        description="AI Code Review Agent - Automated code analysis and review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze src/                          # Analyze all files in src/ directory
  %(prog)s analyze file1.py file2.js            # Analyze specific files
  %(prog)s analyze . --config custom.yaml       # Use custom configuration
  %(prog)s analyze . --format json              # Output results as JSON
  %(prog)s analyze . --no-report                # Skip HTML report generation
  %(prog)s create-config                         # Create sample configuration file
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code files')
    analyze_parser.add_argument('paths', nargs='+', help='Files or directories to analyze')
    analyze_parser.add_argument('--config', '-c', default='code_review_config.yaml',
                               help='Configuration file path (default: code_review_config.yaml)')
    analyze_parser.add_argument('--server', '-s', default='http://localhost:5000',
                               help='Server URL (default: http://localhost:5000)')
    analyze_parser.add_argument('--format', '-f', choices=['detailed', 'json'], default='detailed',
                               help='Output format (default: detailed)')
    analyze_parser.add_argument('--extensions', nargs='+',
                               help='File extensions to include (default: common code files)')
    analyze_parser.add_argument('--output', '-o', help='Save results to file')
    analyze_parser.add_argument('--report', help='HTML report output file')
    analyze_parser.add_argument('--no-report', action='store_true', help='Skip HTML report')
    analyze_parser.add_argument('--download-improved', help='Download improved code to specified file')
    
    # Create config command
    config_parser = subparsers.add_parser('create-config', help='Create sample configuration file')
    
    args = parser.parse_args()
    
    if args.command == 'create-config':
        create_sample_config()
        return
    
    if args.command == 'analyze':
        cli = CodeReviewCLI(args.server)
        
        # Check server health
        if not cli.check_server_health():
            console.print(f"[red]❌ Cannot connect to server at {args.server}[/red]")
            console.print("[yellow]Make sure the Flask server is running:[/yellow]")
            console.print("[white]python app.py[/white]")
            sys.exit(1)
        
        # Load configuration
        config = cli.load_config(args.config)
        
        # Discover files
        files = cli.discover_files(args.paths, args.extensions)
        
        if not files:
            console.print("[red]No code files found to analyze[/red]")
            sys.exit(1)
        
        console.print(f"[blue]Found {len(files)} files to analyze[/blue]")
        
        # Upload and start analysis
        session_id = cli.upload_files(files, config)
        if not session_id:
            sys.exit(1)
        
        # Wait for completion
        results = cli.wait_for_completion(session_id)
        if not results:
            sys.exit(1)
        
        # Display results
        cli.display_results(results, args.format)
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]✓ Results saved to {args.output}[/green]")
        
        # Download HTML report
        if not args.no_report:
            cli.download_report(session_id, args.report)
        
        # Download improved code
        if args.download_improved:
            cli.download_improved_code(session_id, args.download_improved)
        
        console.print("\n[bold green]🎉 Code review completed successfully![/bold green]")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)