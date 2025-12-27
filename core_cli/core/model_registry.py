"""
Model Registry & Management - Phase 5.3 Week 4

Central model registry, versioning, and promotion workflows
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelStage(Enum):
    """Model lifecycle stages"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ModelQuality(Enum):
    """Model quality rating"""
    EXPERIMENTAL = "experimental"
    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"
    PRODUCTION_READY = "production_ready"


@dataclass
class ModelRegistryEntry:
    """Registry entry for model"""
    model_id: str
    name: str
    version: str
    stage: ModelStage
    quality: ModelQuality
    framework: str
    task_type: str
    registered_at: datetime
    registered_by: str
    model_path: str
    description: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    promoted_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model_id': self.model_id,
            'name': self.name,
            'version': self.version,
            'stage': self.stage.value,
            'quality': self.quality.value,
            'framework': self.framework,
            'task_type': self.task_type,
            'registered_at': self.registered_at.isoformat(),
            'registered_by': self.registered_by,
            'model_path': self.model_path,
            'description': self.description,
            'metrics': self.metrics,
            'tags': self.tags,
            'dependencies': self.dependencies,
            'promoted_at': self.promoted_at.isoformat() if self.promoted_at else None,
            'deprecated_at': self.deprecated_at.isoformat() if self.deprecated_at else None
        }


@dataclass
class ModelPromotion:
    """Model promotion record"""
    model_id: str
    from_stage: ModelStage
    to_stage: ModelStage
    promoted_at: datetime
    promoted_by: str
    reason: str
    validation_results: Dict[str, Any] = field(default_factory=dict)
    approved_by: Optional[str] = None


class ModelRegistry:
    """Centralized model registry and lifecycle management"""
    
    def __init__(self):
        """Initialize registry"""
        self.registry: Dict[str, ModelRegistryEntry] = {}
        self.promotion_history: Dict[str, List[ModelPromotion]] = {}
        self.model_aliases: Dict[str, str] = {}  # alias -> model_id
        self.stage_tracking: Dict[ModelStage, List[str]] = {
            stage: [] for stage in ModelStage
        }
    
    def register_model(
        self,
        model_id: str,
        name: str,
        version: str,
        framework: str,
        task_type: str,
        model_path: str,
        registered_by: str,
        quality: ModelQuality = ModelQuality.EXPERIMENTAL,
        metrics: Dict[str, float] = None,
        tags: List[str] = None
    ) -> ModelRegistryEntry:
        """Register new model"""
        entry = ModelRegistryEntry(
            model_id=model_id,
            name=name,
            version=version,
            stage=ModelStage.DEVELOPMENT,
            quality=quality,
            framework=framework,
            task_type=task_type,
            registered_at=datetime.now(),
            registered_by=registered_by,
            model_path=model_path,
            metrics=metrics or {},
            tags=tags or []
        )
        
        self.registry[model_id] = entry
        self.stage_tracking[ModelStage.DEVELOPMENT].append(model_id)
        self.promotion_history[model_id] = []
        
        logger.info(f"Registered model: {model_id} v{version}")
        
        return entry
    
    def promote_model(
        self,
        model_id: str,
        to_stage: ModelStage,
        promoted_by: str,
        reason: str,
        validation_results: Dict[str, Any] = None,
        approved_by: Optional[str] = None
    ) -> bool:
        """Promote model to new stage"""
        if model_id not in self.registry:
            logger.error(f"Model not found: {model_id}")
            return False
        
        entry = self.registry[model_id]
        from_stage = entry.stage
        
        # Validate transition
        if from_stage == to_stage:
            logger.warning(f"Model already in {to_stage.value}")
            return False
        
        # Create promotion record
        promotion = ModelPromotion(
            model_id=model_id,
            from_stage=from_stage,
            to_stage=to_stage,
            promoted_at=datetime.now(),
            promoted_by=promoted_by,
            reason=reason,
            validation_results=validation_results or {},
            approved_by=approved_by
        )
        
        # Update entry
        entry.stage = to_stage
        entry.promoted_at = datetime.now()
        
        # Update stage tracking
        if model_id in self.stage_tracking[from_stage]:
            self.stage_tracking[from_stage].remove(model_id)
        self.stage_tracking[to_stage].append(model_id)
        
        # Record promotion
        self.promotion_history[model_id].append(promotion)
        
        logger.info(f"Promoted {model_id} from {from_stage.value} to {to_stage.value}")
        
        return True
    
    def deprecate_model(
        self,
        model_id: str,
        reason: str,
        deprecated_by: str
    ) -> bool:
        """Mark model as deprecated"""
        if model_id not in self.registry:
            logger.error(f"Model not found: {model_id}")
            return False
        
        entry = self.registry[model_id]
        entry.stage = ModelStage.DEPRECATED
        entry.deprecated_at = datetime.now()
        
        if model_id in self.stage_tracking[entry.stage]:
            self.stage_tracking[entry.stage].remove(model_id)
        self.stage_tracking[ModelStage.DEPRECATED].append(model_id)
        
        logger.info(f"Deprecated model: {model_id}")
        
        return True
    
    def get_model(self, model_id: str) -> Optional[ModelRegistryEntry]:
        """Get model entry"""
        return self.registry.get(model_id)
    
    def get_latest_by_name(self, name: str) -> Optional[ModelRegistryEntry]:
        """Get latest version of model by name"""
        matching = [
            entry for entry in self.registry.values()
            if entry.name == name
        ]
        if not matching:
            return None
        return max(matching, key=lambda x: x.registered_at)
    
    def get_production_model(self, name: str) -> Optional[ModelRegistryEntry]:
        """Get production model"""
        matching = [
            entry for entry in self.registry.values()
            if entry.name == name and entry.stage == ModelStage.PRODUCTION
        ]
        return matching[0] if matching else None
    
    def list_by_stage(self, stage: ModelStage) -> List[ModelRegistryEntry]:
        """List models in stage"""
        return [
            self.registry[model_id]
            for model_id in self.stage_tracking[stage]
            if model_id in self.registry
        ]
    
    def list_by_task(self, task_type: str) -> List[ModelRegistryEntry]:
        """List models by task type"""
        return [
            entry for entry in self.registry.values()
            if entry.task_type == task_type
        ]
    
    def create_alias(self, alias: str, model_id: str) -> bool:
        """Create model alias"""
        if model_id not in self.registry:
            logger.error(f"Model not found: {model_id}")
            return False
        
        self.model_aliases[alias] = model_id
        logger.info(f"Created alias '{alias}' -> {model_id}")
        
        return True
    
    def get_by_alias(self, alias: str) -> Optional[ModelRegistryEntry]:
        """Get model by alias"""
        if alias in self.model_aliases:
            model_id = self.model_aliases[alias]
            return self.registry.get(model_id)
        return None
    
    def update_metrics(
        self,
        model_id: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Update model metrics"""
        if model_id not in self.registry:
            logger.error(f"Model not found: {model_id}")
            return False
        
        self.registry[model_id].metrics.update(metrics)
        
        return True
    
    def get_promotion_history(self, model_id: str) -> List[ModelPromotion]:
        """Get promotion history"""
        return self.promotion_history.get(model_id, [])
    
    def search(
        self,
        name: Optional[str] = None,
        stage: Optional[ModelStage] = None,
        task_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ModelRegistryEntry]:
        """Search registry"""
        results = list(self.registry.values())
        
        if name:
            results = [r for r in results if name.lower() in r.name.lower()]
        
        if stage:
            results = [r for r in results if r.stage == stage]
        
        if task_type:
            results = [r for r in results if r.task_type == task_type]
        
        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]
        
        return results


# Singleton factory
_registry_instance: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get ModelRegistry singleton"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
        logger.info("ModelRegistry initialized")
    return _registry_instance
