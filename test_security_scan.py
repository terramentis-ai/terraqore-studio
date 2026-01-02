"""
Test script for SecurityVulnerabilityAgent
Tests OWASP/CWE vulnerability scanning on generated code.
"""

import sys
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add core_cli to path
sys.path.insert(0, str(Path(__file__).parent / "core_cli"))

from agents.security_agent import SecurityVulnerabilityAgent
from agents.base import AgentContext
from core.llm_client import create_llm_client_from_config
from core.config import ConfigManager

def main():
    print("=" * 70)
    print("SECURITY VULNERABILITY AGENT TEST")
    print("=" * 70)
    
    # Load configuration
    config_mgr = ConfigManager()
    config = config_mgr.load()
    
    # Initialize LLM client
    llm_client = create_llm_client_from_config(config)
    
    # Initialize SecurityVulnerabilityAgent
    security_agent = SecurityVulnerabilityAgent(llm_client=llm_client)
    
    # Load the generated code from task 30
    code_output_path = Path("core_cli/logs/coder_outputs/task-30-Set-up-Python-environment-20260102-044346.json")
    
    if not code_output_path.exists():
        print(f"❌ Code output file not found: {code_output_path}")
        return
    
    with open(code_output_path, 'r', encoding='utf-8') as f:
        code_data = json.load(f)
    
    # Parse the response (it's JSON inside a markdown code block)
    response_text = code_data['response']
    # Remove markdown code fences
    if response_text.startswith('```'):
        response_text = response_text.split('\n', 1)[1]
    if response_text.endswith('```'):
        response_text = response_text.rsplit('```', 1)[0]
    
    code_json = json.loads(response_text.strip())
    
    print(f"\n🔒 Scanning {len(code_json['files'])} files for vulnerabilities:")
    for file_info in code_json['files']:
        print(f"  - {file_info['path']}: {file_info['description']}")
    
    # Create context for security scanning
    context = AgentContext(
        project_id=3,  # Full Pipeline Test project
        project_name="Full Pipeline Test - Task Manager API",
        project_description="RESTful API for task management",
        user_input=json.dumps(code_json),
        metadata={
            "task_id": 30,
            "task_title": "Set up Python environment",
            "language": "python",
            "code_generation": {
                "files": code_json['files']
            },
            "files": code_json['files']
        }
    )
    
    print("\n🛡️  Running SecurityVulnerabilityAgent...")
    print("-" * 70)
    
    # Execute security scan
    result = security_agent.execute(context)
    
    print("\n📊 SECURITY SCAN RESULTS")
    print("=" * 70)
    
    if result.success:
        print("✅ Scan Status: SUCCESS")
    else:
        print("❌ Scan Status: FAILED")
    
    print(f"\n⏱️  Execution Time: {result.execution_time:.2f}s")
    
    # Show output
    if result.output:
        print(f"\n📄 Security Report:\n")
        print(result.output)
    
    # Parse metadata
    if result.metadata:
        vuln_count = result.metadata.get('vulnerability_count', 0)
        critical_count = result.metadata.get('critical_vulnerabilities', 0)
        high_count = result.metadata.get('high_vulnerabilities', 0)
        medium_count = result.metadata.get('medium_vulnerabilities', 0)
        low_count = result.metadata.get('low_vulnerabilities', 0)
        
        print(f"\n📈 Vulnerability Summary:")
        print(f"   Total: {vuln_count}")
        print(f"   🔴 Critical: {critical_count}")
        print(f"   🟠 High: {high_count}")
        print(f"   🟡 Medium: {medium_count}")
        print(f"   🔵 Low: {low_count}")
        
        is_secure = result.metadata.get('is_secure', False)
        print(f"\n🔐 Security Rating: {'SECURE ✓' if is_secure else 'AT RISK ⚠️'}")
        
        # Show vulnerability details if any
        vulnerabilities = result.metadata.get('vulnerabilities', [])
        if vulnerabilities:
            print(f"\n⚠️  Detected Vulnerabilities:")
            for i, vuln in enumerate(vulnerabilities[:10], 1):  # Show first 10
                if isinstance(vuln, dict):
                    severity = vuln.get('severity', 'unknown')
                    vuln_type = vuln.get('type', 'unknown')
                    description = vuln.get('description', 'No description')
                    file_path = vuln.get('file', 'unknown')
                    print(f"\n   {i}. [{severity.upper()}] {vuln_type}")
                    print(f"      File: {file_path}")
                    print(f"      {description}")
                    
                    recommendation = vuln.get('recommendation', '')
                    if recommendation:
                        print(f"      Fix: {recommendation}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
