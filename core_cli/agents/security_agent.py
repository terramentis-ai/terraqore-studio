"""
TerraQore security Vulnerability Agent
Scans code for security vulnerabilities and compliance issues.
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from agents.base import BaseAgent, AgentContext, AgentResult
from core.security_validator import validate_agent_input, SecurityViolation

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Security risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""
    vulnerability_id: str      # e.g., "SEC-001"
    title: str
    description: str
    risk_level: str           # low, medium, high, critical
    affected_code: str        # Code snippet or location
    remediation: str
    owasp_category: Optional[str]
    cwe_id: Optional[str]


@dataclass
class DependencyVulnerability:
    """Represents a vulnerable dependency."""
    package_name: str
    current_version: str
    vulnerable_version_range: str
    fixed_version: str
    vulnerability_description: str
    severity: str


@dataclass
class SecurityScanResult:
    """Complete security scan result."""
    scan_timestamp: str
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    vulnerabilities: List[Vulnerability]
    dependency_vulnerabilities: List[DependencyVulnerability]
    compliance_issues: List[Dict[str, str]]
    risk_score: float
    scan_passed: bool
    recommendations: List[str]


class SecurityVulnerabilityAgent(BaseAgent):
    """Agent specialized in security vulnerability detection.
    
    Capabilities:
    - Code vulnerability scanning
    - Dependency vulnerability detection
    - OWASP Top 10 compliance checking
    - CWE (Common Weakness Enumeration) mapping
    - Credential leak detection
    - Supply chain risk assessment
    - Security hardening recommendations
    """
    
    PROMPT_PROFILE = {
        "role": "Security Vulnerability Agent — red-team style reviewer",
        "mission": "Identify code and dependency weaknesses before release and map them to OWASP/CWE standards.",
        "objectives": [
            "Prioritize high/critical risks and block unsafe code",
            "Check code, configs, and dependencies for OWASP Top 10 issues",
            "Provide remediation guidance tied to best practices",
            "Report in strict JSON so orchestrator can enforce quality gates"
        ],
        "guardrails": [
            "Never assume missing context — request it via context metadata",
            "Flag suspected secrets immediately",
            "If unsure about severity, err toward higher risk"
        ],
        "response_format": (
            "Return ONLY JSON with keys total_vulnerabilities, critical_vulnerabilities, high_vulnerabilities, "
            "medium_vulnerabilities, low_vulnerabilities, vulnerabilities (array), dependency_vulnerabilities (array), "
            "compliance_issues (array), risk_score, scan_passed, recommendations (array)."
        ),
        "tone": "Direct, incident-response ready"
    }

    def __init__(self, llm_client=None, verbose: bool = False, retriever: object = None):
        """Initialize Security Vulnerability Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
        super().__init__(
            name="SecurityVulnerabilityAgent",
            description="Scans code for security vulnerabilities, dependency issues, and compliance risks",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever,
            prompt_profile=self.PROMPT_PROFILE
        )
        
        # OWASP Top 10 (2021)
        self.owasp_top_10 = [
            "Broken Access Control",
            "Cryptographic Failures",
            "Injection",
            "Insecure Design",
            "Security Misconfiguration",
            "Vulnerable Components",
            "Authentication Failures",
            "Data Integrity Failures",
            "Logging & Monitoring Failures",
            "SSRF"
        ]
        
        # Common vulnerable patterns
        self.vulnerable_patterns = {
            "hardcoded_credentials": {
                "patterns": ["password", "api_key", "secret", "token"],
                "severity": "critical"
            },
            "sql_injection": {
                "patterns": ["f\"SELECT", "f'SELECT", ".format(", "query()"],
                "severity": "critical"
            },
            "unsafe_deserialization": {
                "patterns": ["pickle.loads", "eval(", "exec("],
                "severity": "critical"
            },
            "insecure_random": {
                "patterns": ["random.choice", "random.randint"],
                "severity": "high"
            },
            "missing_validation": {
                "patterns": ["request.args", "request.form", "request.json()"],
                "severity": "high"
            },
            "insecure_logging": {
                "patterns": ["logger.info(password", "print(password"],
                "severity": "high"
            }
        }
        
        # Known vulnerable dependencies
        self.known_vulnerabilities = {
            "django": {"vulnerable": ["<3.2"], "fixed": "3.2+"},
            "flask": {"vulnerable": ["<2.0"], "fixed": "2.0+"},
            "requests": {"vulnerable": ["<2.28"], "fixed": "2.28+"},
            "pyyaml": {"vulnerable": ["<5.4"], "fixed": "5.4+"}
        }
    
    
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute security scanning workflow.
        
        Args:
            context: Agent execution context with code metadata.
            
        Returns:
            AgentResult with security scan results.
        """
        # Validate input for security violations
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            logger.error(f"[{self.name}] Security validation failed: {str(e)}")
            return self.create_result(success=False, output="", execution_time=0, 
                                     error=f"Security validation failed: {str(e)}")
        start_time = time.time()
        steps = []
        
        # Classify task sensitivity (Phase 5) - Security tasks are CRITICAL
        task_sensitivity = self.classify_task_sensitivity(
            task_type="security_analysis",
            has_private_data=True,
            has_sensitive_data=True,
            is_security_task=True  # Security analysis is always CRITICAL
        )
        self._log_step(f"Task classified as: {task_sensitivity} (CRITICAL - stays local)")
        
        try:
            # Step 1: Extract code information
            self._log_step("Extracting code for security analysis")
            code_info = self._extract_code_info(context)
            steps.append("Extracted code information")
            
            # Step 2: Scan for credential leaks
            self._log_step("Scanning for hardcoded credentials")
            credential_vulns = self._scan_credentials(code_info)
            steps.append(f"Found {len(credential_vulns)} credential-related issues")
            
            # Step 3: Scan for injection vulnerabilities
            self._log_step("Scanning for injection vulnerabilities")
            injection_vulns = self._scan_injection(code_info)
            steps.append(f"Found {len(injection_vulns)} injection vulnerabilities")
            
            # Step 4: Scan for insecure patterns
            self._log_step("Scanning for insecure patterns")
            pattern_vulns = self._scan_insecure_patterns(code_info)
            steps.append(f"Found {len(pattern_vulns)} insecure patterns")
            
            # Step 5: Check dependencies
            self._log_step("Checking for vulnerable dependencies")
            dep_vulns = self._check_dependencies(code_info)
            steps.append(f"Found {len(dep_vulns)} vulnerable dependencies")
            
            # Step 6: Generate security report
            self._log_step("Generating security report")
            all_vulns = credential_vulns + injection_vulns + pattern_vulns
            scan_result = self._generate_scan_result(
                code_info, all_vulns, dep_vulns
            )
            steps.append("Security scan complete")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=scan_result.scan_passed,
                output=self._format_scan_output(scan_result),
                execution_time=execution_time,
                metadata={
                    "scan_passed": scan_result.scan_passed,
                    "risk_score": scan_result.risk_score,
                    "total_vulnerabilities": scan_result.total_vulnerabilities,
                    "critical_count": scan_result.critical_vulnerabilities,
                    "provider": "security_vulnerability_agent",
                    "scan_result": scan_result.__dict__
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Security scan failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output=error_msg,
                execution_time=time.time() - start_time,
                metadata={"provider": "security_vulnerability_agent", "error": str(e)},
                intermediate_steps=steps
            )
    
    def _extract_code_info(self, context: AgentContext) -> Dict[str, Any]:
        """Extract code information from context."""
        return {
            "project_name": context.project_name,
            "code_files": context.metadata.get("code_generation", {}).get("files", []) if context.metadata else [],
            "language": context.metadata.get("language", "python") if context.metadata else "python",
            "dependencies": context.metadata.get("dependencies", []) if context.metadata else [],
            "metadata": context.metadata or {}
        }
    
    def _scan_credentials(self, code_info: Dict[str, Any]) -> List[Vulnerability]:
        """Scan for hardcoded credentials and secrets."""
        vulnerabilities = []
        files = code_info.get("code_files", [])
        
        credential_keywords = [
            "password", "api_key", "secret", "token", "aws_secret",
            "private_key", "encryption_key", "auth_token", "bearer"
        ]
        
        for file in files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            for keyword in credential_keywords:
                if keyword in content.lower():
                    # Check if it looks like actual credential (contains = and quotes)
                    if f'{keyword} = "' in content or f"{keyword} = '" in content:
                        vulnerabilities.append(Vulnerability(
                            vulnerability_id="SEC-CRED-001",
                            title="Hardcoded Credentials",
                            description=f"Potential hardcoded {keyword} found in {path}",
                            risk_level="critical",
                            affected_code=f"{keyword} found in source code",
                            remediation="Move to environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault)",
                            owasp_category="Cryptographic Failures",
                            cwe_id="CWE-798"
                        ))
        
        return vulnerabilities
    
    def _scan_injection(self, code_info: Dict[str, Any]) -> List[Vulnerability]:
        """Scan for injection vulnerabilities (SQL, Command, etc.)."""
        vulnerabilities = []
        files = code_info.get("code_files", [])
        language = code_info.get("language", "python")
        
        for file in files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            if language == "python":
                # SQL Injection patterns
                if "f\"SELECT" in content or "f'SELECT" in content:
                    vulnerabilities.append(Vulnerability(
                        vulnerability_id="SEC-SQL-001",
                        title="SQL Injection Vulnerability",
                        description=f"Potential SQL injection in {path} - using f-strings with user input",
                        risk_level="critical",
                        affected_code="f\"SELECT * FROM users WHERE id = {user_input}\"",
                        remediation="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_input,))",
                        owasp_category="Injection",
                        cwe_id="CWE-89"
                    ))
                
                # Command injection
                if "os.system(" in content or "subprocess.call(" in content and "shell=True" in content:
                    vulnerabilities.append(Vulnerability(
                        vulnerability_id="SEC-CMD-001",
                        title="Command Injection Vulnerability",
                        description=f"Potential command injection in {path}",
                        risk_level="critical",
                        affected_code="os.system(user_command)",
                        remediation="Use subprocess.run() with shell=False and pass arguments as list",
                        owasp_category="Injection",
                        cwe_id="CWE-78"
                    ))
        
        return vulnerabilities
    
    def _scan_insecure_patterns(self, code_info: Dict[str, Any]) -> List[Vulnerability]:
        """Scan for other insecure patterns."""
        vulnerabilities = []
        files = code_info.get("code_files", [])
        language = code_info.get("language", "python")
        
        for file in files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            # Insecure deserialization
            if "pickle.loads" in content:
                vulnerabilities.append(Vulnerability(
                    vulnerability_id="SEC-DESER-001",
                    title="Insecure Deserialization",
                    description="pickle.loads() allows arbitrary code execution",
                    risk_level="critical",
                    affected_code="pickle.loads(user_data)",
                    remediation="Use JSON for untrusted data, avoid pickle for user input",
                    owasp_category="Insecure Design",
                    cwe_id="CWE-502"
                ))
            
            # eval/exec usage
            if "eval(" in content or "exec(" in content:
                vulnerabilities.append(Vulnerability(
                    vulnerability_id="SEC-EVAL-001",
                    title="Unsafe eval/exec Usage",
                    description="eval/exec can execute arbitrary code",
                    risk_level="critical",
                    affected_code="eval(user_input)",
                    remediation="Use ast.literal_eval for safe evaluation, avoid eval/exec with user input",
                    owasp_category="Injection",
                    cwe_id="CWE-95"
                ))
            
            # Missing input validation
            if "request.args" in content and "if " not in content:
                vulnerabilities.append(Vulnerability(
                    vulnerability_id="SEC-VAL-001",
                    title="Missing Input Validation",
                    description="User input used without validation",
                    risk_level="high",
                    affected_code="user_id = request.args.get('id')",
                    remediation="Validate all user input: check type, length, format before use",
                    owasp_category="Broken Access Control",
                    cwe_id="CWE-20"
                ))
        
        return vulnerabilities
    
    def _check_dependencies(self, code_info: Dict[str, Any]) -> List[DependencyVulnerability]:
        """Check for vulnerable dependencies."""
        vulns = []
        files = code_info.get("code_files", [])
        
        # Check requirements.txt or package.json
        for file in files:
            path = file.get("path", "")
            content = file.get("content", "")
            
            if path.endswith("requirements.txt"):
                for line in content.split("\n"):
                    if "==" in line:
                        pkg_info = line.split("==")
                        if len(pkg_info) == 2:
                            pkg_name = pkg_info[0].strip()
                            pkg_version = pkg_info[1].strip()
                            
                            # Check against known vulnerabilities
                            if pkg_name in self.known_vulnerabilities:
                                vuln_info = self.known_vulnerabilities[pkg_name]
                                if any(pkg_version in v for v in vuln_info["vulnerable"]):
                                    vulns.append(DependencyVulnerability(
                                        package_name=pkg_name,
                                        current_version=pkg_version,
                                        vulnerable_version_range=str(vuln_info["vulnerable"]),
                                        fixed_version=vuln_info["fixed"],
                                        vulnerability_description=f"{pkg_name} {pkg_version} has known vulnerabilities",
                                        severity="high"
                                    ))
        
        return vulns
    
    def _generate_scan_result(self,
                             code_info: Dict[str, Any],
                             vulnerabilities: List[Vulnerability],
                             dep_vulnerabilities: List[DependencyVulnerability]) -> SecurityScanResult:
        """Generate security scan result."""
        from datetime import datetime
        
        critical = len([v for v in vulnerabilities if v.risk_level == "critical"])
        high = len([v for v in vulnerabilities if v.risk_level == "high"])
        medium = len([v for v in vulnerabilities if v.risk_level == "medium"])
        low = len([v for v in vulnerabilities if v.risk_level == "low"])
        
        # Calculate risk score (0-10)
        risk_score = (critical * 2.5) + (high * 1.5) + (medium * 0.75) + (low * 0.25)
        risk_score = min(10, risk_score)
        
        recommendations = []
        if critical > 0:
            recommendations.append("CRITICAL: Address all critical vulnerabilities before deployment")
        if high > 0:
            recommendations.append("Remediate high-severity vulnerabilities")
        recommendations.append("Implement security best practices")
        recommendations.append("Use SAST tool (bandit, pylint) in CI/CD")
        recommendations.append("Regular dependency updates and vulnerability scanning")
        recommendations.append("Code review process with security focus")
        
        return SecurityScanResult(
            scan_timestamp=datetime.now().isoformat(),
            total_vulnerabilities=len(vulnerabilities) + len(dep_vulnerabilities),
            critical_vulnerabilities=critical,
            high_vulnerabilities=high + len(dep_vulnerabilities),
            medium_vulnerabilities=medium,
            low_vulnerabilities=low,
            vulnerabilities=vulnerabilities,
            dependency_vulnerabilities=dep_vulnerabilities,
            compliance_issues=[],
            risk_score=risk_score,
            scan_passed=critical == 0,
            recommendations=recommendations
        )
    
    def _format_scan_output(self, result: SecurityScanResult) -> str:
        """Format security scan report."""
        output = f"""
SECURITY VULNERABILITY SCAN REPORT
{'='*70}

Scan Status: {'PASSED' if result.scan_passed else 'FAILED'}
Risk Score: {result.risk_score:.1f}/10
Total Vulnerabilities: {result.total_vulnerabilities}

VULNERABILITY SUMMARY
{'-'*70}
Critical:  {result.critical_vulnerabilities}
High:      {result.high_vulnerabilities}
Medium:    {result.medium_vulnerabilities}
Low:       {result.low_vulnerabilities}

"""
        
        if result.vulnerabilities:
            output += f"""VULNERABILITIES FOUND
{'-'*70}
"""
            for vuln in result.vulnerabilities[:10]:
                output += f"""
[{vuln.risk_level.upper()}] {vuln.title} ({vuln.vulnerability_id})
  Description: {vuln.description}
  OWASP: {vuln.owasp_category}
  CWE: {vuln.cwe_id}
  Remediation: {vuln.remediation}
"""
        
        if result.dependency_vulnerabilities:
            output += f"""
VULNERABLE DEPENDENCIES
{'-'*70}
"""
            for dep in result.dependency_vulnerabilities:
                output += f"""
{dep.package_name} {dep.current_version}
  Issue: {dep.vulnerability_description}
  Fixed: {dep.fixed_version}
"""
        
        output += f"""
RECOMMENDATIONS
{'-'*70}
"""
        for i, rec in enumerate(result.recommendations, 1):
            output += f"{i}. {rec}\n"
        
        output += f"\nScan Time: {result.scan_timestamp}\n"
        return output
    
    def _log_step(self, message: str):
        """Log an execution step."""
        if self.verbose:
            logger.info(f"[{self.name}] {message}")
