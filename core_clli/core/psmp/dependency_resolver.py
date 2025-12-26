"""
Dependency Conflict Resolver - Detects and resolves dependency version conflicts.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from .models import DependencySpec, DependencyConflict, DependencyScope

logger = logging.getLogger(__name__)


class VersionConstraintParser:
    """Parse and compare semantic version constraints."""
    
    @staticmethod
    def parse_constraint(constraint: str) -> Tuple[str, str, str]:
        """
        Parse constraint like ">=2.0,<3.0" into operator pairs.
        Returns: (operator, version, extra_constraints)
        """
        constraint = constraint.strip()
        
        # Simple cases
        if constraint.startswith("=="):
            return "==", constraint[2:].strip(), ""
        elif constraint.startswith(">="):
            return ">=", constraint[2:].strip(), ""
        elif constraint.startswith("<="):
            return "<=", constraint[2:].strip(), ""
        elif constraint.startswith(">"):
            return ">", constraint[1:].strip(), ""
        elif constraint.startswith("<"):
            return "<", constraint[1:].strip(), ""
        elif constraint.startswith("~="):
            return "~=", constraint[2:].strip(), ""
        else:
            # Complex constraint like ">=2.0,<3.0"
            return "complex", constraint, ""
    
    @staticmethod
    def are_compatible(constraint1: str, constraint2: str) -> bool:
        """
        Check if two version constraints can be satisfied by a common version.
        This is a simplified check; real implementation would use packaging library.
        """
        # Parse both constraints
        op1, ver1, _ = VersionConstraintParser.parse_constraint(constraint1)
        op2, ver2, _ = VersionConstraintParser.parse_constraint(constraint2)
        
        # Simple heuristic: if both are exact versions, they must match
        if op1 == "==" and op2 == "==":
            return ver1 == ver2
        
        # If one is complex, assume they might be compatible (real impl would be smarter)
        if "," in constraint1 or "," in constraint2:
            return True
        
        # Otherwise, assume compatible (conservative approach)
        return True


class DependencyConflictResolver:
    """Detects and suggests resolutions for dependency conflicts."""
    
    def __init__(self):
        """Initialize the resolver."""
        self.all_dependencies: Dict[str, List[DependencySpec]] = {}
        self.conflicts_detected: List[DependencyConflict] = []
        self.resolution_attempts: Dict[str, Any] = {}
    
    def register_dependencies(
        self, 
        project_id: int, 
        agent_id: str, 
        deps: List[DependencySpec]
    ) -> Tuple[bool, Optional[List[DependencyConflict]]]:
        """
        Register dependencies from an agent and check for conflicts.
        
        Returns:
            Tuple of (success, conflicts). If conflicts found, success=False.
        """
        # Add dependencies to registry
        for dep in deps:
            key = f"{dep.name}:{dep.scope.value}"
            if key not in self.all_dependencies:
                self.all_dependencies[key] = []
            self.all_dependencies[key].append(dep)
            
            logger.debug(f"Registered dependency: {dep.name} {dep.version_constraint} "
                        f"from {dep.declared_by_agent}")
        
        # Check for conflicts
        conflicts = self._detect_conflicts(project_id)
        
        if conflicts:
            logger.error(f"Found {len(conflicts)} dependency conflict(s)")
            self.conflicts_detected.extend(conflicts)
            return False, conflicts
        
        logger.info(f"Registered {len(deps)} dependencies with no conflicts")
        return True, None
    
    def _detect_conflicts(self, project_id: int) -> List[DependencyConflict]:
        """Detect conflicts in currently registered dependencies."""
        conflicts = []
        
        for lib_key, specs in self.all_dependencies.items():
            if len(specs) <= 1:
                continue
            
            lib_name = lib_key.split(":")[0]
            
            # Group by scope to check compatibility
            by_scope = {}
            for spec in specs:
                scope = spec.scope.value
                if scope not in by_scope:
                    by_scope[scope] = []
                by_scope[scope].append(spec)
            
            # Check within each scope
            for scope, scope_specs in by_scope.items():
                if len(scope_specs) <= 1:
                    continue
                
                # Try to find a common version
                compatible = self._find_compatible_version(scope_specs)
                
                if not compatible:
                    # Conflict found
                    requirements = [
                        {
                            "agent": spec.declared_by_agent,
                            "needs": spec.version_constraint,
                            "purpose": spec.purpose or "unspecified"
                        }
                        for spec in scope_specs
                    ]
                    
                    conflict = DependencyConflict(
                        library=lib_name,
                        requirements=requirements,
                        error=f"No single version satisfies all agents in {scope} scope",
                        severity="critical" if scope == "runtime" else "error",
                        suggested_resolutions=self._suggest_resolutions(scope_specs)
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _find_compatible_version(self, specs: List[DependencySpec]) -> Optional[str]:
        """Try to find a version that satisfies all constraints."""
        if not specs:
            return None
        
        # For simplicity, return the first constraint if all are compatible
        first_constraint = specs[0].version_constraint
        
        for spec in specs[1:]:
            if not VersionConstraintParser.are_compatible(
                first_constraint, 
                spec.version_constraint
            ):
                return None
        
        # In a real implementation, would return the actual compatible version
        # For now, return a placeholder
        return f"compatible-with-{specs[0].name}"
    
    def _suggest_resolutions(self, conflicting_specs: List[DependencySpec]) -> List[str]:
        """Generate suggested resolutions for conflicting specs."""
        suggestions = []
        
        agents = set(s.declared_by_agent for s in conflicting_specs)
        
        # Suggestion 1: Ask one agent to update
        if len(agents) > 0:
            agent = list(agents)[0]
            suggestions.append(
                f"Ask {agent} to relax its version constraint or use compatibility layer"
            )
        
        # Suggestion 2: Pin to latest compatible
        suggestions.append(
            "Identify latest version compatible with all constraints"
        )
        
        # Suggestion 3: Isolate dependency
        suggestions.append(
            "Isolate conflicting code into separate service/environment"
        )
        
        # Suggestion 4: Negotiate between agents
        if len(agents) > 1:
            suggestions.append(
                f"Create consensus between {len(agents)} agents on shared version"
            )
        
        return suggestions
    
    def get_resolved_manifest(self) -> Dict[str, str]:
        """
        Generate final conflict-free requirements manifest.
        Returns dict of {package_name: resolved_version}
        """
        manifest = {}
        
        for lib_key, specs in self.all_dependencies.items():
            lib_name = lib_key.split(":")[0]
            
            if lib_name not in manifest:
                # Select the "best" version for this library
                # In a real implementation, would use intelligent selection
                if specs:
                    manifest[lib_name] = specs[0].version_constraint
            
        return manifest
    
    def clear_conflicts(self):
        """Clear detected conflicts (after resolution)."""
        self.conflicts_detected.clear()
    
    def get_conflict_report(self) -> Dict[str, Any]:
        """Get a formatted report of current conflicts."""
        return {
            "total_conflicts": len(self.conflicts_detected),
            "conflicts": [c.to_dict() for c in self.conflicts_detected],
            "total_dependencies_registered": sum(
                len(specs) for specs in self.all_dependencies.values()
            )
        }


# Global resolver instance
_resolver: Optional[DependencyConflictResolver] = None


def get_dependency_resolver() -> DependencyConflictResolver:
    """Get or create the global dependency resolver."""
    global _resolver
    if _resolver is None:
        _resolver = DependencyConflictResolver()
    return _resolver
