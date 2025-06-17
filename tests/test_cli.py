# test_cli.py - Complete Test Suite for CLI Tool
import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import requests_mock
from src.cli import CodeReviewCLI

class TestCodeReviewCLI(unittest.TestCase):
    """Test suite for the Code Review CLI"""
    
    def setUp(self):
        self.cli = CodeReviewCLI("http://localhost:5000")
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config(self):
        """Test default configuration generation"""
        config = self.cli.get_default_config()
        
        self.assertIn('analysis', config)
        self.assertIn('rules', config)
        self.assertIn('output', config)
        self.assertIn('filters', config)
        
        self.assertTrue(config['analysis']['security'])
        self.assertEqual(config['rules']['styleGuide'], 'pep8')
        self.assertEqual(config['rules']['maxLineLength'], 120)
        self.assertTrue(config['output']['includeFixSuggestions'])
    
    def test_file_discovery(self):
        """Test file discovery functionality"""
        # Create test files
        test_files = [
            'test.py',
            'main.js', 
            'style.css',
            'README.md',
            'subdir/another.py'
        ]
        
        # Create subdirectory
        os.makedirs(os.path.join(self.temp_dir, 'subdir'), exist_ok=True)
        
        for filename in test_files:
            file_path = os.path.join(self.temp_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write('# test content')
        
        # Test discovery
        discovered = self.cli.discover_files([self.temp_dir])
        
        # Should find .py and .js files, but not .css or .md
        self.assertEqual(len(discovered), 3)  # test.py, main.js, subdir/another.py
        self.assertTrue(any('test.py' in f for f in discovered))
        self.assertTrue(any('main.js' in f for f in discovered))
        self.assertTrue(any('another.py' in f for f in discovered))
        self.assertFalse(any('style.css' in f for f in discovered))
        self.assertFalse(any('README.md' in f for f in discovered))
    
    def test_file_discovery_specific_extensions(self):
        """Test file discovery with specific extensions"""
        # Create test files
        test_files = ['test.py', 'main.js', 'app.go', 'style.css']
        
        for filename in test_files:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write('# test content')
        
        # Test discovery with specific extensions
        discovered = self.cli.discover_files([self.temp_dir], ['.py', '.go'])
        
        self.assertEqual(len(discovered), 2)
        self.assertTrue(any('test.py' in f for f in discovered))
        self.assertTrue(any('app.go' in f for f in discovered))
        self.assertFalse(any('main.js' in f for f in discovered))
        self.assertFalse(any('style.css' in f for f in discovered))
    
    @requests_mock.Mocker()
    def test_health_check(self, m):
        """Test server health check"""
        # Mock successful health check
        m.get('http://localhost:5000/api/health', json={'status': 'healthy'}, status_code=200)
        
        result = self.cli.check_server_health()
        self.assertTrue(result)
        
        # Mock failed health check
        m.get('http://localhost:5000/api/health', status_code=500)
        
        result = self.cli.check_server_health()
        self.assertFalse(result)
        
        # Mock connection error
        m.get('http://localhost:5000/api/health', exc=requests_mock.exceptions.ConnectTimeout)
        
        result = self.cli.check_server_health()
        self.assertFalse(result)
    
    @requests_mock.Mocker()
    def test_upload_files(self, m):
        """Test file upload functionality"""
        # Mock successful upload
        mock_response = {
            'session_id': 'test-session-123',
            'status': 'started',
            'message': 'Code review analysis initiated'
        }
        m.post('http://localhost:5000/api/review/start', json=mock_response, status_code=200)
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write('print("Hello, World!")')
        
        config = self.cli.get_default_config()
        session_id = self.cli.upload_files([test_file], config)
        
        self.assertEqual(session_id, 'test-session-123')
    
    @requests_mock.Mocker()
    def test_upload_files_failure(self, m):
        """Test file upload failure"""
        # Mock failed upload
        m.post('http://localhost:5000/api/review/start', status_code=400, text='Bad Request')
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write('print("Hello, World!")')
        
        config = self.cli.get_default_config()
        session_id = self.cli.upload_files([test_file], config)
        
        self.assertIsNone(session_id)
    
    @requests_mock.Mocker()
    def test_get_results(self, m):
        """Test results retrieval"""
        mock_results = {
            'session_id': 'test-session-123',
            'metrics': {
                'filesProcessed': 3,
                'totalIssues': 12,
                'securityIssues': 2,
                'performanceIssues': 4,
                'styleIssues': 6,
                'codeQualityScore': 85
            },
            'issues': [
                {
                    'severity': 'high',
                    'type': 'security',
                    'file': 'main.py',
                    'line': 42,
                    'description': 'Potential SQL injection vulnerability'
                },
                {
                    'severity': 'medium', 
                    'type': 'performance',
                    'file': 'utils.py',
                    'line': 18,
                    'description': 'Inefficient loop detected'
                }
            ],
            'recommendations': [
                'Consider using parameterized queries to prevent SQL injection',
                'Optimize loops for better performance',
                'Add more comprehensive error handling'
            ]
        }
        
        m.get('http://localhost:5000/api/review/test-session-123/results', 
              json=mock_results, status_code=200)
        
        results = self.cli.get_results('test-session-123')
        
        self.assertIsNotNone(results)
        self.assertEqual(results['session_id'], 'test-session-123')
        self.assertEqual(results['metrics']['totalIssues'], 12)
        self.assertEqual(len(results['issues']), 2)
    
    @requests_mock.Mocker()
    def test_status_polling(self, m):
        """Test status polling during analysis"""
        # Mock status responses
        status_responses = [
            {'status': 'processing', 'progress': 25, 'current_step': 'Analyzing files...'},
            {'status': 'processing', 'progress': 50, 'current_step': 'Running security checks...'},
            {'status': 'processing', 'progress': 75, 'current_step': 'Generating report...'},
            {'status': 'completed', 'progress': 100, 'current_step': 'Analysis complete!'}
        ]
        
        # Mock results
        mock_results = {
            'session_id': 'test-session-123',
            'metrics': {'totalIssues': 5},
            'issues': [],
            'recommendations': []
        }
        
        m.get('http://localhost:5000/api/review/test-session-123/status', 
              [{'json': resp, 'status_code': 200} for resp in status_responses])
        
        m.get('http://localhost:5000/api/review/test-session-123/results',
              json=mock_results, status_code=200)
        
        # This would normally show progress, but we'll just test completion
        with patch('time.sleep'):  # Skip actual delays in test
            results = self.cli.wait_for_completion('test-session-123')
        
        self.assertIsNotNone(results)
        self.assertEqual(results['session_id'], 'test-session-123')
    
    @requests_mock.Mocker()
    def test_download_report(self, m):
        """Test HTML report download"""
        mock_html = b'<html><body><h1>Code Review Report</h1></body></html>'
        
        m.get('http://localhost:5000/api/review/test-session-123/report',
              content=mock_html, status_code=200)
        
        report_file = os.path.join(self.temp_dir, 'test_report.html')
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            self.cli.download_report('test-session-123', report_file)
            
            mock_file.write.assert_called_once_with(mock_html)
    
    @requests_mock.Mocker()
    def test_download_improved_code(self, m):
        """Test improved code package download"""
        mock_zip = b'PK\x03\x04...'  # Mock ZIP content
        
        m.get('http://localhost:5000/api/review/test-session-123/download',
              content=mock_zip, status_code=200)
        
        zip_file = os.path.join(self.temp_dir, 'improved_code.zip')
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            self.cli.download_improved_code('test-session-123', zip_file)
            
            mock_file.write.assert_called_once_with(mock_zip)
    
    def test_config_loading_yaml(self):
        """Test YAML configuration loading"""
        config_content = """
analysis:
  security: true
  performance: false
rules:
  styleGuide: "google"
  maxLineLength: 100
"""
        config_file = os.path.join(self.temp_dir, 'test_config.yaml')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        config = self.cli.load_config(config_file)
        
        self.assertTrue(config['analysis']['security'])
        self.assertFalse(config['analysis']['performance'])
        self.assertEqual(config['rules']['styleGuide'], 'google')
        self.assertEqual(config['rules']['maxLineLength'], 100)
    
    def test_config_loading_json(self):
        """Test JSON configuration loading"""
        config_data = {
            'analysis': {'security': True, 'performance': False},
            'rules': {'styleGuide': 'airbnb', 'maxLineLength': 80}
        }
        
        config_file = os.path.join(self.temp_dir, 'test_config.json')
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = self.cli.load_config(config_file)
        
        self.assertTrue(config['analysis']['security'])
        self.assertFalse(config['analysis']['performance'])
        self.assertEqual(config['rules']['styleGuide'], 'airbnb')
        self.assertEqual(config['rules']['maxLineLength'], 80)
    
    def test_config_loading_nonexistent(self):
        """Test loading non-existent configuration file"""
        config = self.cli.load_config('nonexistent.yaml')
        
        # Should return default config
        self.assertIn('analysis', config)
        self.assertTrue(config['analysis']['security'])
        self.assertEqual(config['rules']['styleGuide'], 'pep8')

if __name__ == '__main__':
    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCodeReviewCLI)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    exit(0 if result.wasSuccessful() else 1)