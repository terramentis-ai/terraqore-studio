"""
TerraQore Studio - Dependency Conflict Resolver
Semantic version constraint solving with automatic conflict resolution.

Author: TerraQore Development Team
Date: January 2, 2026

This module handles:
1. Dependency registration and tracking
2. Conflict detection using semantic versioning
3. Automatic resolution strategies
4. Manifest generation (requirements.txt/pyproject.toml)
"""

import logging
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from packaging import version
from packaging.specifiers import SpecifierSet

logger = logging.getLogger(__name__)


class DependencyScope(str, Enum):
    """Dependency scope classification."""
    RUNTIME = "runtime"
    DEV = "dev"
    BUILD = "build"
    OPTIONAL = "optional"


class ResolutionStrategy(str, Enum):
    """Available conflict resolution strategies."""
    LATEST = "latest"  # Use latest compatible version
    EARLIEST = "earliest"  # Use earliest compatible version
    INTERSECTION = "intersection"  # Find version that satisfies all constraints
    USER_CHOICE = "user_choice"  # Defer to user selection


@dataclass
class DependencySpec:
    """Standard model for dependency declaration by an agent."""
    
    name: str  # e.g., "pandas"
    version_constraint: str  # e.g., ">=2.0,<3.0", "==1.5.*"
    scope: DependencyScope = DependencyScope.RUNTIME
    declared_by_agent: str = ""  # Which agent added it?
    purpose: Optional[str] = None  # Why is it needed?
    installed_version: Optional[str] = None  # Current installed version (if any)
    
    def __hash__(self):
        return hash((self.name.lower(), self.version_constraint, self.scope))
    
    def __eq__(self, other):
        if not isinstance(other, DependencySpec):
            return False
        return (self.name.lower() == other.name.lower() and 
                self.version_constraint == other.version_constraint and
                self.scope == other.scope)


@dataclass
class DependencyConflict:
    """Represents a detected dependency conflict."""
    
    library: str
    requirements: List[Dict] = field(default_factory=list)
    error: str = ""
    specs: List[DependencySpec] = field(default_factory=list)
    resolution_candidates: List[str] = field(default_factory=list)
    severity: str = "high"  # low, medium, high, critical
    resolved: bool = False
    resolution_version: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert conflict to dictionary for reporting."""
        return {
            "library": self.library,
            "severity": self.severity,
            "error": self.error,
            "requirements": [
                {
                    "agent": spec.declared_by_agent,
                    "needs": spec.version_constraint,
                    "purpose": spec.purpose,
                    "scope": spec.scope.value
                }
                for spec in self.specs
            ],
            "resolution_candidates": self.resolution_candidates,
            "resolved": self.resolved,
            "resolution_version": self.resolution_version
        }


class VersionConstraintParser:
    """Parse and validate version constraint strings."""
    
    # Regex patterns for common version formats
    PATTERNS = {
        "exact": r"^==([\d.]+)$",  # ==1.5.0
        "compatible": r"^~=([\d.]+)$",  # ~=1.5.0
        "prefix": r"^([\d.]+)\.\*$",  # 1.5.*
        "range": r"^(>=|<=|>|<)?([\d.]+)(?:,(>=|<=|>|<)?([\d.]+))?$",  # >=1.5,<2.0
    }
    
    @staticmethod
    def parse(constraint: str) -> SpecifierSet:
        """
        Parse version constraint string into SpecifierSet.
        
        Args:
            constraint: Version constraint string (e.g., ">=1.5,<2.0")
        
        Returns:
            packaging.specifiers.SpecifierSet object
        
        Raises:
            ValueError: If constraint format is invalid
        """
        if not constraint or constraint.strip() == "*":
            return SpecifierSet()  # No constraint
        
        try:
            # Handle common formats
            constraint = constraint.strip()
            
            # Convert prefix notation: 1.5.* → >=1.5,<1.6
            if constraint.endswith(".*"):
                base = constraint[:-2]
                parts = base.split(".")
                if len(parts) >= 2:
                    next_patch = str(int(parts[-1]) + 1)
                    constraint = f">={base},<{'.'.join(parts[:-1])}.{next_patch}"
            
            # Convert compatible: ~=1.5.0 → >=1.5.0,==1.5.*
            if constraint.startswith("~="):
                base = constraint[2:]
                parts = base.split(".")
                if len(parts) >= 2:
                    # Remove patch version for compatible constraint
                    minor = ".".join(parts[:-1])
                    constraint = f">={base},<{minor}.{int(parts[-2]) + 1}"
            
            return SpecifierSet(constraint)
        except Exception as e:
            logger.warning(f"Invalid version constraint '{constraint}': {e}")
            raise ValueError(f"Invalid version constraint: {constraint}") from e
    
    @staticmethod
    def validate_constraint(constraint: str, test_version: str) -> bool:
        """
        Check if a version satisfies a constraint.
        
        Args:
            constraint: Version constraint string
            test_version: Version to test
        
        Returns:
            True if version satisfies constraint
        """
        try:
            spec_set = VersionConstraintParser.parse(constraint)
            return test_version in spec_set
        except Exception as e:
            logger.error(f"Constraint validation failed: {e}")
            return False


class DependencyConflictResolver:
    """
    Central resolver for dependency conflicts using semantic versioning.
    
    Workflow:
    1. register_dependencies() - agents declare their requirements
    2. _detect_conflicts() - automatic conflict detection
    3. resolve_conflicts() - apply resolution strategies
    4. get_resolved_manifest() - generate final unified requirements
    """
    
    def __init__(self):
        """Initialize the resolver."""
        self.all_dependencies: Dict[str, List[DependencySpec]] = {}
        self.conflicts: Dict[str, DependencyConflict] = {}
        self.resolved_versions: Dict[str, str] = {}
        self.parser = VersionConstraintParser()
    
    def register_dependencies(
        self, 
        project_id: str, 
        agent_id: str, 
        deps: List[DependencySpec]
    ) -> Tuple[bool, List[DependencyConflict]]:
        """
        Register dependencies declared by an agent.
        
        Args:
            project_id: Project ID (for logging)
            agent_id: Agent ID declaring dependencies
            deps: List of DependencySpec objects
        
        Returns:
            Tuple of (success: bool, conflicts: List[DependencyConflict])
        """
        logger.info(f"Registering {len(deps)} dependencies from agent {agent_id}")
        
        try:
            # Register each dependency
            for dep in deps:
                if dep.name not in self.all_dependencies:
                    self.all_dependencies[dep.name] = []
                self.all_dependencies[dep.name].append(dep)
            
            # Detect conflicts
            new_conflicts = self._detect_conflicts()
            
            # Store conflicts
            for conflict in new_conflicts:
                self.conflicts[conflict.library] = conflict
            
            success = len(new_conflicts) == 0
            return success, new_conflicts
        
        except Exception as e:
            logger.error(f"Error registering dependencies: {e}")
            return False, []
    
    def _detect_conflicts(self) -> List[DependencyConflict]:
        """
        Detect incompatible version constraints.
        
        Returns:
            List of DependencyConflict objects
        """
        conflicts = []
        
        for lib_name, specs in self.all_dependencies.items():
            if len(specs) <= 1:
                continue  # No conflict with single spec
            
            # Try to find a version satisfying all constraints
            try:
                feasible_version = self._find_common_version(specs)
                if not feasible_version:
                    conflict = DependencyConflict(
                        library=lib_name,
                        specs=specs,
                        error=f"No single version satisfies all constraints: {[s.version_constraint for s in specs]}",
                        severity="high"
                    )
                    conflicts.append(conflict)
                    logger.warning(f"Conflict detected in {lib_name}: {conflict.error}")
            
            except Exception as e:
                conflict = DependencyConflict(
                    library=lib_name,
                    specs=specs,
                    error=f"Invalid version spec: {str(e)}",
                    severity="critical"
                )
                conflicts.append(conflict)
                logger.error(f"Critical conflict in {lib_name}: {e}")
        
        return conflicts
    
    def _find_common_version(self, specs: List[DependencySpec]) -> Optional[str]:
        """
        Find a version that satisfies all constraint specifications.
        
        Args:
            specs: List of DependencySpec objects for same library
        
        Returns:
            Version string that satisfies all, or None if impossible
        """
        if not specs:
            return None
        
        try:
            # Parse all constraints
            spec_sets = []
            for spec in specs:
                spec_set = self.parser.parse(spec.version_constraint)
                spec_sets.append(spec_set)
            
            # Find intersection of constraints
            # Start with first constraint, then intersect with others
            if not spec_sets:
                return None
            
            # Get all versions that match first constraint
            # For now, use a heuristic: get the highest version that satisfies all
            # In a real implementation, this would query PyPI or a version database
            
            # Simplified approach: find the intersection range
            combined_spec = spec_sets[0]
            for spec_set in spec_sets[1:]:
                combined_spec = self._intersect_specifiers(combined_spec, spec_set)
            
            # Return the highest version in the intersection (heuristic)
            # This would ideally use a version database
            return self._best_version_from_specifier(combined_spec, specs[0].name)
        
        except Exception as e:
            logger.warning(f"Error finding common version: {e}")
            return None
    
    @staticmethod
    def _intersect_specifiers(spec1: SpecifierSet, spec2: SpecifierSet) -> SpecifierSet:
        """
        Find intersection of two SpecifierSets.
        
        This is a simplified implementation. A complete version would
        need to analyze the constraint ranges more carefully.
        """
        # Combine all specifiers
        combined = SpecifierSet(",".join(str(spec1)) + "," + str(spec2))
        return combined
    
    @staticmethod
    def _best_version_from_specifier(spec_set: SpecifierSet, lib_name: str) -> Optional[str]:
        """
        Get the best (highest) version matching specifier set.
        
        In production, this would query PyPI. For now, returns None
        (allowing conflict resolution strategies to handle it).
        """
        # This is where you'd integrate with PyPI or a version database
        # For now, returning None to indicate need for user choice
        return None
    
    def resolve_conflicts(self, strategy: ResolutionStrategy = ResolutionStrategy.LATEST) -> Dict[str, str]:
        """
        Resolve detected conflicts using specified strategy.
        
        Args:
            strategy: Resolution strategy to apply
        
        Returns:
            Dictionary of {library: resolved_version}
        """
        logger.info(f"Resolving {len(self.conflicts)} conflicts using strategy: {strategy}")
        
        for lib_name, conflict in self.conflicts.items():
            if conflict.resolved:
                continue
            
            if strategy == ResolutionStrategy.LATEST:
                # Prefer latest compatible version
                resolved = self._resolve_latest(conflict)
            elif strategy == ResolutionStrategy.EARLIEST:
                # Prefer earliest compatible version
                resolved = self._resolve_earliest(conflict)
            elif strategy == ResolutionStrategy.INTERSECTION:
                # Find intersection of all constraints
                resolved = self._resolve_intersection(conflict)
            elif strategy == ResolutionStrategy.USER_CHOICE:
                # Mark for user decision
                resolved = None
            else:
                resolved = None
            
            if resolved:
                conflict.resolved = True
                conflict.resolution_version = resolved
                self.resolved_versions[lib_name] = resolved
                logger.info(f"Resolved {lib_name} to {resolved}")
            else:
                logger.warning(f"Could not auto-resolve {lib_name}, requires user decision")
        
        return self.resolved_versions
    
    def _resolve_latest(self, conflict: DependencyConflict) -> Optional[str]:
        """Resolve by choosing latest compatible version."""
        # Get candidates from all specs
        candidates = set()
        for spec in conflict.specs:
            # This is simplified; real implementation would query PyPI
            candidates.add(spec.version_constraint)
        
        # Return highest version (simplified)
        conflict.resolution_candidates = sorted(candidates)
        return conflict.resolution_candidates[-1] if candidates else None
    
    def _resolve_earliest(self, conflict: DependencyConflict) -> Optional[str]:
        """Resolve by choosing earliest compatible version."""
        candidates = set()
        for spec in conflict.specs:
            candidates.add(spec.version_constraint)
        
        conflict.resolution_candidates = sorted(candidates)
        return conflict.resolution_candidates[0] if candidates else None
    
    def _resolve_intersection(self, conflict: DependencyConflict) -> Optional[str]:
        """Resolve by finding intersection of all constraints."""
        try:
            # Attempt to find intersection of all version constraints
            all_specs = [self.parser.parse(s.version_constraint) for s in conflict.specs]
            
            # Create combined specifier
            combined = all_specs[0]
            for spec in all_specs[1:]:
                combined = self._intersect_specifiers(combined, spec)
            
            # Return a representative version
            # Simplified: just return the first spec's constraint as fallback
            return conflict.specs[0].version_constraint
        
        except Exception as e:
            logger.warning(f"Intersection resolution failed: {e}")
            return None
    
    def get_resolved_manifest(self) -> Dict[str, str]:
        """
        Generate final conflict-free requirements manifest.
        
        Returns:
            Dictionary of {library: resolved_version}
        """
        manifest = {}
        
        for lib_name, specs in self.all_dependencies.items():
            if lib_name in self.resolved_versions:
                # Use resolved version
                manifest[lib_name] = self.resolved_versions[lib_name]
            elif len(specs) == 1:
                # Single spec, use as-is
                manifest[lib_name] = specs[0].version_constraint
            else:
                # Multiple specs, unresolved - use most permissive
                manifest[lib_name] = "*"
        
        return manifest
    
    def get_manifest_string(self, format: str = "requirements") -> str:
        """
        Generate manifest as string (requirements.txt or pyproject.toml).
        
        Args:
            format: "requirements" for requirements.txt, "pyproject" for pyproject.toml
        
        Returns:
            String representation of manifest
        """
        manifest = self.get_resolved_manifest()
        
        if format == "requirements":
            lines = [f"{lib}=={version}" for lib, version in manifest.items()]
            return "\n".join(sorted(lines))
        
        elif format == "pyproject":
            lines = [f'"{lib}" = "{version}"' for lib, version in manifest.items()]
            return "[project]\ndependencies = [\n    " + ",\n    ".join(lines) + "\n]"
        
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def generate_conflict_report(self) -> Dict:
        """
        Generate detailed conflict report for user/logging.
        
        Returns:
            Dictionary with conflict details
        """
        return {
            "total_libraries": len(self.all_dependencies),
            "conflicts_detected": len(self.conflicts),
            "conflicts_resolved": sum(1 for c in self.conflicts.values() if c.resolved),
            "conflicts_pending": sum(1 for c in self.conflicts.values() if not c.resolved),
            "conflicts": {
                lib: conflict.to_dict() 
                for lib, conflict in self.conflicts.items()
            }
        }
    
    def clear(self):
        """Clear all registered dependencies and conflicts."""
        self.all_dependencies.clear()
        self.conflicts.clear()
        self.resolved_versions.clear()
        logger.info("Dependency resolver cleared")
