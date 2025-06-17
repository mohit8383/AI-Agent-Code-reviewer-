#!/usr/bin/env python3
"""
REST API Server for AI Code Review Agent
Provides programmatic access to the code review functionality
"""
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import json
import tempfile
import zipfile
import threading
import uuid
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Store active review sessions
active_reviews = {}
review_results = {}

class ReviewSession:
    """Manages a code review session"""
    
    def __init__(self, session_id: str, config: dict):
        self.session_id = session_id
        self.config = config
        self.status = "initializing"
        self.progress = 0
        self.current_step = ""
        self.start_time = datetime.now()
        self.results = None
        self.error = None
        
    def update_progress(self, progress: int, step: str):
        self.progress = progress
        self.current_step = step
        logger.info(f"Session {self.session_id}: {progress}% - {step}")

class MockCodeReviewEngine:
    """Mock implementation of the code review engine for demo purposes"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def analyze_codebase(self, files: List[str], config: dict, session: ReviewSession):
        """Analyze the provided codebase"""
        steps = [
            "Extracting and organizing files",
            "Parsing source code structure", 
            "Running security analysis",
            "Checking performance patterns",
            "Evaluating code style",
            "Detecting complexity issues",
            "Generating improvement suggestions",
            "Creating optimized code variants",
            "Compiling final report"
        ]
        
        try:
            session.update_progress(0, "Starting analysis...")
            await asyncio.sleep(1)
            
            for i, step in enumerate(steps):
                session.update_progress(int((i + 1) / len(steps) * 100), step)
                # Simulate processing time
                await asyncio.sleep(2)
            
            # Generate mock results
            results = self._generate_analysis_results(files, config)
            session.results = results
            session.status = "completed"
            
            logger.info(f"Analysis completed for session {session.session_id}")
            return results
            
        except Exception as e:
            session.error = str(e)
            session.status = "failed"
            logger.error(f"Analysis failed for session {session.session_id}: {e}")
            raise
    
    def _generate_analysis_results(self, files: List[str], config: dict) -> dict:
        """Generate realistic mock analysis results"""
        import random
        
        # Simulate different types of issues based on file types
        issues = []
        security_issues = []
        performance_issues = []
        style_issues = []
        
        file_extensions = [f.split('.')[-1] for f in files if '.' in f]
        
        # Security issues
        if any(ext in ['py', 'js', 'php'] for ext in file_extensions):
            security_issues.extend([
                {
                    "type": "Security",
                    "severity": "high",
                    "category": "injection", 
                    "file": random.choice(files),
                    "line": random.randint(10, 200),
                    "description": "SQL injection vulnerability detected",
                    "suggestion": "Use parameterized queries instead of string concatenation",
                    "cwe_id": "CWE-89",
                    "confidence": 0.9
                },
                {
                    "type": "Security",
                    "severity": "medium",
                    "category": "crypto",
                    "file": random.choice(files),
                    "line": random.randint(10, 200), 
                    "description": "Weak cryptographic algorithm (MD5) detected",
                    "suggestion": "Use SHA-256 or stronger hashing algorithms",
                    "cwe_id": "CWE-327",
                    "confidence": 0.8
                }
            ])
        
        # Performance issues
        performance_issues.extend([
            {
                "type": "Performance",
                "severity": "medium",
                "category": "algorithm",
                "file": random.choice(files),
                "line": random.randint(10, 200),
                "description": "O(n²) algorithm detected in loop",
                "suggestion": "Consider using dictionary lookup for O(1) access",
                "impact": "High memory usage with large datasets",
                "confidence": 0.85
            },
            {
                "type": "Performance", 
                "severity": "low",
                "category": "memory",
                "file": random.choice(files),
                "line": random.randint(10, 200),
                "description": "Large object created in loop without cleanup",
                "suggestion": "Move object creation outside loop or use object pooling",
                "impact": "Memory leak potential",
                "confidence": 0.7
            }
        ])
        
        # Style issues
        style_issues.extend([
            {
                "type": "Style",
                "severity": "low", 
                "category": "formatting",
                "file": random.choice(files),
                "line": random.randint(10, 200),
                "description": "Line exceeds maximum length (120 characters)",
                "suggestion": "Break long line into multiple lines",
                "rule": config.get('styleGuide', 'pep8') + "-line-length",
                "confidence": 1.0
            }
        ])
        
        all_issues = security_issues + performance_issues + style_issues
        
        # Calculate metrics
        metrics = {
            "totalIssues": len(all_issues),
            "filesProcessed": len(files),
            "securityIssues": len(security_issues),
            "performanceIssues": len(performance_issues), 
            "styleIssues": len(style_issues),
            "complexityReduction": random.randint(15, 45),
            "codeQualityScore": max(100 - len(all_issues) * 2, 60),
            "testCoverage": random.randint(65, 95),
            "maintainabilityIndex": random.randint(70, 90)
        }
        
        # Generate improved code samples
        improvements = {
            "optimized_functions": random.randint(5, 15),
            "security_fixes": len(security_issues),
            "performance_optimizations": len(performance_issues),
            "refactored_components": random.randint(3, 8)
        }
        
        return {
            "session_id": uuid.uuid4().hex,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "issues": all_issues,
            "improvements": improvements,
            "config_used": config,
            "recommendations": [
                "Consider implementing automated testing for security-sensitive functions",
                "Add input validation for all user-facing interfaces", 
                "Implement caching strategy for frequently accessed data",
                "Consider using static analysis tools in CI/CD pipeline"
            ]
        }

# Initialize the review engine
review_engine = MockCodeReviewEngine()

@app.route('/')
def serve_index():
    """Serve the main web interface"""
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_reviews)
    })

@app.route('/api/review/start', methods=['POST'])
def start_review():
    """Start a new code review session"""
    try:
        # Get uploaded files
        files = request.files.getlist('files')
        config = json.loads(request.form.get('config', '{}'))
        
        if not files:
            return jsonify({"error": "No files provided"}), 400
        
        # Create session
        session_id = str(uuid.uuid4())
        session = ReviewSession(session_id, config)
        active_reviews[session_id] = session
        
        # Save uploaded files
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        
        for file in files:
            if file.filename:
                file_path = os.path.join(temp_dir, file.filename.replace('/', '_'))
                file.save(file_path)
                file_paths.append(file.filename)
        
        # Start analysis in background
        def run_analysis():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    review_engine.analyze_codebase(file_paths, config, session)
                )
                review_results[session_id] = results
            except Exception as e:
                logger.error(f"Background analysis failed: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "message": "Code review analysis initiated"
        })
        
    except Exception as e:
        logger.error(f"Failed to start review: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/review/<session_id>/status')
def get_review_status(session_id):
    """Get the status of a review session"""
    session = active_reviews.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "session_id": session_id,
        "status": session.status,
        "progress": session.progress,
        "current_step": session.current_step,
        "start_time": session.start_time.isoformat(),
        "error": session.error
    })

@app.route('/api/review/<session_id>/results')
def get_review_results(session_id):
    """Get the results of a completed review"""
    if session_id not in review_results:
        return jsonify({"error": "Results not found"}), 404
    
    return jsonify(review_results[session_id])

@app.route('/api/review/<session_id>/report')
def download_report(session_id):
    """Download HTML report for a review session"""
    if session_id not in review_results:
        return jsonify({"error": "Results not found"}), 404
    
    results = review_results[session_id]
    
    # Generate HTML report
    html_content = generate_html_report(results)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    temp_file.write(html_content)
    temp_file.close()
    
    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f'code_review_report_{session_id}.html',
        mimetype='text/html'
    )

@app.route('/api/review/<session_id>/download')
def download_improved_code(session_id):
    """Download improved code package"""
    if session_id not in review_results:
        return jsonify({"error": "Results not found"}), 404
    
    results = review_results[session_id]
    
    # Create ZIP file with improved code (mock implementation)
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f'improved_code_{session_id}.zip')
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add results JSON
        zipf.writestr('review_results.json', json.dumps(results, indent=2))
        
        # Add mock improved files
        zipf.writestr('improved/README.md', f"""# Code Review Results

## Summary
- Total Issues Fixed: {results['metrics']['totalIssues']}
- Security Issues: {results['metrics']['securityIssues']}
- Performance Improvements: {results['metrics']['performanceIssues']}
- Code Quality Score: {results['metrics']['codeQualityScore']}/100

## Key Improvements
{chr(10).join('- ' + rec for rec in results['recommendations'])}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
        
        zipf.writestr('improved/CHANGELOG.md', """# Changelog

## Security Fixes
- Fixed SQL injection vulnerabilities
- Updated cryptographic algorithms
- Added input validation

## Performance Optimizations  
- Optimized database queries
- Implemented caching
- Reduced memory usage

## Code Quality
- Fixed style violations
- Improved readability
- Added documentation
""")
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f'improved_code_{session_id}.zip',
        mimetype='application/zip'
    )

def generate_html_report(results: dict) -> str:
    """Generate HTML report from results"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Code Review Report</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f5f7fa;
            }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 30px; 
                text-align: center; 
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .metrics {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin: 20px 0; 
            }}
            .metric {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .metric-value {{ 
                font-size: 2rem; 
                font-weight: bold; 
                color: #667eea; 
                margin-bottom: 5px; 
            }}
            .issues {{ 
                margin: 30px 0; 
                background: white; 
                border-radius: 10px; 
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .issues h2 {{ 
                background: #f8f9fa; 
                margin: 0; 
                padding: 20px; 
                border-bottom: 1px solid #dee2e6; 
            }}
            .issue {{ 
                padding: 20px; 
                border-bottom: 1px solid #f0f0f0; 
            }}
            .issue:last-child {{ border-bottom: none; }}
            .severity-high {{ border-left: 5px solid #ff4757; }}
            .severity-medium {{ border-left: 5px solid #ffa502; }}
            .severity-low {{ border-left: 5px solid #2ed573; }}
            .recommendations {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-top: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Code Review Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{results['metrics']['totalIssues']}</div>
                <div>Total Issues Found</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['metrics']['filesProcessed']}</div>
                <div>Files Processed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['metrics']['securityIssues']}</div>
                <div>Security Issues</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['metrics']['performanceIssues']}</div>
                <div>Performance Issues</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['metrics']['codeQualityScore']}</div>
                <div>Quality Score</div>
            </div>
        </div>
        
        <div class="issues">
            <h2>🐛 Issues Found</h2>
            {''.join(f'''
            <div class="issue severity-{issue['severity']}">
                <h4>{issue['type']}: {issue['description']}</h4>
                <p><strong>File:</strong> {issue['file']} (Line {issue['line']})</p>
                <p><strong>Severity:</strong> {issue['severity'].upper()}</p>
                <p><strong>Suggestion:</strong> {issue['suggestion']}</p>
                {f"<p><strong>CWE ID:</strong> {issue.get('cwe_id', 'N/A')}</p>" if 'cwe_id' in issue else ""}
            </div>
            ''' for issue in results['issues'])}
        </div>
        
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            <ul>
                {''.join(f'<li>{rec}</li>' for rec in results['recommendations'])}
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>Report generated by AI Code Review Agent</p>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    print("🚀 Starting AI Code Review Agent API Server...")
    print("📱 Web Interface: http://localhost:5000")
    print("🔗 API Docs: http://localhost:5000/api/health")
    
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)