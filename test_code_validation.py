"""
Test script for CodeValidationAgent
Tests the quality scoring system on generated code.
"""

import sys
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add core_cli to path
sys.path.insert(0, str(Path(__file__).parent / "core_cli"))

from agents.code_validator_agent import CodeValidationAgent
from agents.base import AgentContext
from core.llm_client import create_llm_client_from_config
from core.config import ConfigManager

def main():
    print("=" * 70)
    print("CODE VALIDATION AGENT TEST")
    print("=" * 70)
    
    # Load configuration
    config_mgr = ConfigManager()
    config = config_mgr.load()
    
    # Initialize LLM client
    llm_client = create_llm_client_from_config(config)
    
    # Initialize CodeValidationAgent
    validator = CodeValidationAgent(llm_client=llm_client)
    
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
    
    print(f"\n📋 Testing validation on {len(code_json['files'])} files:")
    for file_info in code_json['files']:
        print(f"  - {file_info['path']}: {file_info['description']}")
    
    # Create context for validation
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
    
    print("\n🔍 Running CodeValidationAgent...")
    print("-" * 70)
    
    # Execute validation
    result = validator.execute(context)
    
    # Debug: print the full output
    print(f"\n📄 Validation Output:\n{result.output}\n")
    
    # Debug: print metadata
    if result.metadata:
        hall_meta = result.metadata.get('hallucination_meta', {})
        if hall_meta:
            print(f"\n🔬 Hallucination Detection Details:")
            print(f"   Max Severity: {hall_meta.get('max_severity')}")
            print(f"   Min Score: {hall_meta.get('min_score', 0):.2f}")
            print(f"   Total Findings: {hall_meta.get('total_findings', 0)}")
            print(f"   Halt Triggered: {hall_meta.get('halt', False)}")
    
    print("\n📊 VALIDATION RESULTS")
    print("=" * 70)
    
    if result.success:
        print("✅ Validation Status: SUCCESS")
    else:
        print("❌ Validation Status: FAILED")
    
    print(f"\n⏱️  Execution Time: {result.execution_time:.2f}s")
    
    # Parse metadata
    if result.metadata:
        overall_score = result.metadata.get('overall_score', 0)
        print(f"\n⭐ Overall Quality Score: {overall_score:.1f}/10")
        
        if overall_score >= 8:
            print("   Rating: EXCELLENT ✨")
        elif overall_score >= 6:
            print("   Rating: GOOD ✓")
        elif overall_score >= 4:
            print("   Rating: FAIR ⚠️")
        else:
            print("   Rating: POOR ❌")
        
        # Show validation object details
        validation_data = result.metadata.get('validation', {})
        if validation_data:
            print(f"\n📁 Files Checked: {validation_data.get('files_checked', 0)}")
            print(f"🔍 Issues Found: {validation_data.get('issues_found', []) if isinstance(validation_data.get('issues_found'), int) else len(validation_data.get('issues_found', []))}")
        
        # Show metrics
        metrics = validation_data.get('metrics', []) if validation_data else result.metadata.get('metrics', [])
        if metrics:
            print("\n📈 Quality Metrics:")
            for metric in metrics:
                if isinstance(metric, dict):
                    print(f"   • {metric['metric_name']}: {metric['score']:.1f}/10 ({metric['status']})")
                    print(f"     {metric['details']}")
                else:
                    print(f"   • {metric.metric_name}: {metric.score:.1f}/10 ({metric.status})")
                    print(f"     {metric.details}")
        
        # Show issues
        issues = validation_data.get('issues_found', []) if validation_data else result.metadata.get('issues', [])
        if issues:
            print(f"\n⚠️  Issues Found: {len(issues)}")
            
            # Group by severity
            critical = [i for i in issues if (i.get('severity') if isinstance(i, dict) else i.severity) == 'critical']
            errors = [i for i in issues if (i.get('severity') if isinstance(i, dict) else i.severity) == 'error']
            warnings = [i for i in issues if (i.get('severity') if isinstance(i, dict) else i.severity) == 'warning']
            info = [i for i in issues if (i.get('severity') if isinstance(i, dict) else i.severity) == 'info']
            
            if critical:
                print(f"\n   🔴 Critical ({len(critical)}):")
                for issue in critical[:3]:  # Show first 3
                    desc = issue.get('description') if isinstance(issue, dict) else issue.description
                    print(f"      - {desc}")
            
            if errors:
                print(f"\n   🟠 Errors ({len(errors)}):")
                for issue in errors[:3]:
                    desc = issue.get('description') if isinstance(issue, dict) else issue.description
                    print(f"      - {desc}")
            
            if warnings:
                print(f"\n   🟡 Warnings ({len(warnings)}):")
                for issue in warnings[:3]:
                    desc = issue.get('description') if isinstance(issue, dict) else issue.description
                    print(f"      - {desc}")
            
            if info:
                print(f"\n   🔵 Info ({len(info)}):")
                for issue in info[:3]:
                    desc = issue.get('description') if isinstance(issue, dict) else issue.description
                    print(f"      - {desc}")
        
        # Show recommendations
        recommendations = validation_data.get('recommendations', []) if validation_data else result.metadata.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"   {i}. {rec}")
        
        # Deployment readiness
        can_deploy = result.metadata.get('can_deploy', False)
        print(f"\n🚀 Deployment Ready: {'YES ✓' if can_deploy else 'NO ✗'}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
