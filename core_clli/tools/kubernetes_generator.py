"""
KubernetesGenerator - Kubernetes Manifest & Orchestration Code Generation

Generates comprehensive Kubernetes manifests for deployments, services,
networking, storage, RBAC, and advanced orchestration patterns.
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid


class KubernetesResourceType(Enum):
    """Kubernetes resource types"""
    DEPLOYMENT = "Deployment"
    STATEFULSET = "StatefulSet"
    DAEMONSET = "DaemonSet"
    SERVICE = "Service"
    INGRESS = "Ingress"
    CONFIGMAP = "ConfigMap"
    SECRET = "Secret"
    PERSISTENTVOLUME = "PersistentVolume"
    PERSISTENTVOLUMECLAIM = "PersistentVolumeClaim"
    NAMESPACE = "Namespace"
    NETWORKPOLICY = "NetworkPolicy"
    ROLE = "Role"
    ROLEBINDING = "RoleBinding"
    SERVICEACCOUNT = "ServiceAccount"
    HORIZONTALPODAUTOSCALER = "HorizontalPodAutoscaler"


class ServiceType(Enum):
    """Kubernetes service types"""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"


class RestartPolicy(Enum):
    """Pod restart policies"""
    ALWAYS = "Always"
    ON_FAILURE = "OnFailure"
    NEVER = "Never"


class StorageClass(Enum):
    """Storage classes"""
    FAST_SSD = "fast-ssd"
    STANDARD = "standard"
    SLOW = "slow"


@dataclass
class ResourceRequirements:
    """Container resource requirements"""
    cpu_request: str = "250m"
    memory_request: str = "256Mi"
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"


@dataclass
class ProbeConfig:
    """Liveness/Readiness probe configuration"""
    probe_type: str  # httpGet, tcpSocket, exec
    initial_delay_seconds: int = 30
    period_seconds: int = 10
    timeout_seconds: int = 5
    failure_threshold: int = 3
    success_threshold: int = 1
    path: Optional[str] = None
    port: int = 8000


@dataclass
class PersistentStorageConfig:
    """Persistent storage configuration"""
    enabled: bool = False
    size: str = "10Gi"
    storage_class: StorageClass = StorageClass.STANDARD
    mount_path: str = "/data"
    access_mode: str = "ReadWriteOnce"


@dataclass
class KubernetesConfig:
    """Kubernetes deployment configuration"""
    config_id: str
    app_name: str
    namespace: str = "default"
    replicas: int = 3
    image: str = ""
    image_pull_policy: str = "IfNotPresent"
    container_port: int = 8000
    service_type: ServiceType = ServiceType.CLUSTER_IP
    resource_requirements: ResourceRequirements = field(default_factory=ResourceRequirements)
    liveness_probe: Optional[ProbeConfig] = None
    readiness_probe: Optional[ProbeConfig] = None
    persistent_storage: PersistentStorageConfig = field(default_factory=PersistentStorageConfig)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    config_map: Optional[Dict[str, Any]] = None
    secrets: Dict[str, str] = field(default_factory=dict)
    enable_autoscaling: bool = True
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    enable_network_policy: bool = False
    enable_ingress: bool = False
    ingress_host: Optional[str] = None
    ingress_path: str = "/"
    labels: Dict[str, str] = field(default_factory=lambda: {"app": "default"})
    annotations: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class KubernetesGenerator:
    """
    Kubernetes Manifest Generator
    
    Generates comprehensive Kubernetes manifests for deployments,
    services, networking, storage, RBAC, and orchestration patterns.
    """
    
    def __init__(self):
        """Initialize Kubernetes Generator"""
        self.configs: Dict[str, KubernetesConfig] = {}
    
    def create_config(
        self,
        app_name: str,
        image: str,
        namespace: str = "default",
        replicas: int = 3,
        container_port: int = 8000,
        service_type: ServiceType = ServiceType.CLUSTER_IP,
        enable_autoscaling: bool = True
    ) -> KubernetesConfig:
        """
        Create Kubernetes configuration
        
        Args:
            app_name: Application name
            image: Container image
            namespace: Kubernetes namespace
            replicas: Number of replicas
            container_port: Container port
            service_type: Service type
            enable_autoscaling: Enable autoscaling
            
        Returns:
            KubernetesConfig
        """
        config_id = f"k8s_{uuid.uuid4().hex[:8]}"
        
        config = KubernetesConfig(
            config_id=config_id,
            app_name=app_name,
            namespace=namespace,
            replicas=replicas,
            image=image,
            container_port=container_port,
            service_type=service_type,
            enable_autoscaling=enable_autoscaling,
            labels={"app": app_name}
        )
        
        self.configs[config_id] = config
        return config
    
    def get_namespace_manifest(self, namespace: str) -> str:
        """
        Generate Namespace manifest
        
        Args:
            namespace: Namespace name
            
        Returns:
            YAML manifest
        """
        return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
  labels:
    name: {namespace}
"""
    
    def get_deployment_manifest(self, config_id: str) -> str:
        """
        Generate Deployment manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {config.app_name}-deployment
  namespace: {config.namespace}
  labels:
    app: {config.app_name}
  annotations:
"""
        for key, value in config.annotations.items():
            manifest += f"    {key}: \"{value}\"\n"
        
        manifest += f"""spec:
  replicas: {config.replicas}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {config.app_name}
  template:
    metadata:
      labels:
        app: {config.app_name}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{config.container_port}"
    spec:
      serviceAccountName: {config.app_name}-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: {config.image}
        imagePullPolicy: {config.image_pull_policy}
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop:
            - ALL
        ports:
        - containerPort: {config.container_port}
          name: http
        resources:
          requests:
            cpu: {config.resource_requirements.cpu_request}
            memory: {config.resource_requirements.memory_request}
          limits:
            cpu: {config.resource_requirements.cpu_limit}
            memory: {config.resource_requirements.memory_limit}
"""
        
        if config.liveness_probe:
            manifest += self._get_probe_spec("livenessProbe", config.liveness_probe)
        
        if config.readiness_probe:
            manifest += self._get_probe_spec("readinessProbe", config.readiness_probe)
        
        manifest += """        env:
"""
        for key, value in config.environment_vars.items():
            manifest += f"""        - name: {key}
          value: "{value}"
"""
        
        if config.persistent_storage.enabled:
            manifest += f"""        volumeMounts:
        - name: data
          mountPath: {config.persistent_storage.mount_path}
        - name: tmp
          mountPath: /tmp
"""
        else:
            manifest += """        volumeMounts:
        - name: tmp
          mountPath: /tmp
"""
        
        manifest += """      volumes:
"""
        
        if config.persistent_storage.enabled:
            manifest += f"""      - name: data
        persistentVolumeClaim:
          claimName: {config.app_name}-pvc
"""
        
        manifest += """      - name: tmp
        emptyDir: {}
"""
        
        return manifest
    
    def get_service_manifest(self, config_id: str) -> str:
        """
        Generate Service manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        manifest = f"""apiVersion: v1
kind: Service
metadata:
  name: {config.app_name}-service
  namespace: {config.namespace}
  labels:
    app: {config.app_name}
spec:
  type: {config.service_type.value}
  selector:
    app: {config.app_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: {config.container_port}
    name: http
"""
        
        if config.service_type == ServiceType.NODE_PORT:
            manifest += """  nodePort: 30080
"""
        
        return manifest
    
    def get_configmap_manifest(self, config_id: str) -> str:
        """
        Generate ConfigMap manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        if not config.config_map:
            return ""
        
        manifest = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {config.app_name}-config
  namespace: {config.namespace}
data:
"""
        
        for key, value in config.config_map.items():
            if isinstance(value, dict):
                manifest += f"  {key}: |\n"
                for k, v in value.items():
                    manifest += f"    {k}: {v}\n"
            else:
                manifest += f"  {key}: \"{value}\"\n"
        
        return manifest
    
    def get_secret_manifest(self, config_id: str) -> str:
        """
        Generate Secret manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest (base64 encoded)
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        if not config.secrets:
            return ""
        
        import base64
        
        manifest = f"""apiVersion: v1
kind: Secret
metadata:
  name: {config.app_name}-secrets
  namespace: {config.namespace}
type: Opaque
data:
"""
        
        for key, value in config.secrets.items():
            encoded = base64.b64encode(value.encode()).decode()
            manifest += f"  {key}: {encoded}\n"
        
        return manifest
    
    def get_hpa_manifest(self, config_id: str) -> str:
        """
        Generate HorizontalPodAutoscaler manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        if not config.enable_autoscaling:
            return ""
        
        manifest = f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {config.app_name}-hpa
  namespace: {config.namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {config.app_name}-deployment
  minReplicas: {config.min_replicas}
  maxReplicas: {config.max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {config.target_cpu_utilization}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
"""
        return manifest
    
    def get_ingress_manifest(self, config_id: str) -> str:
        """
        Generate Ingress manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        if not config.enable_ingress or not config.ingress_host:
            return ""
        
        manifest = f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {config.app_name}-ingress
  namespace: {config.namespace}
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - {config.ingress_host}
    secretName: {config.app_name}-tls
  rules:
  - host: {config.ingress_host}
    http:
      paths:
      - path: {config.ingress_path}
        pathType: Prefix
        backend:
          service:
            name: {config.app_name}-service
            port:
              number: 80
"""
        return manifest
    
    def get_pvc_manifest(self, config_id: str) -> str:
        """
        Generate PersistentVolumeClaim manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        if not config.persistent_storage.enabled:
            return ""
        
        manifest = f"""apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {config.app_name}-pvc
  namespace: {config.namespace}
spec:
  accessModes:
    - {config.persistent_storage.access_mode}
  storageClassName: {config.persistent_storage.storage_class.value}
  resources:
    requests:
      storage: {config.persistent_storage.size}
"""
        return manifest
    
    def get_serviceaccount_manifest(self, config_id: str) -> str:
        """
        Generate ServiceAccount manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        return f"""apiVersion: v1
kind: ServiceAccount
metadata:
  name: {config.app_name}-sa
  namespace: {config.namespace}
"""
    
    def get_network_policy_manifest(self, config_id: str) -> str:
        """
        Generate NetworkPolicy manifest
        
        Args:
            config_id: Config ID
            
        Returns:
            YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        if not config.enable_network_policy:
            return ""
        
        manifest = f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {config.app_name}-netpol
  namespace: {config.namespace}
spec:
  podSelector:
    matchLabels:
      app: {config.app_name}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: {config.namespace}
    ports:
    - protocol: TCP
      port: {config.container_port}
  egress:
  - to:
    - namespaceSelector: {{}}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - podSelector: {{}}
"""
        return manifest
    
    def get_complete_manifest(self, config_id: str) -> str:
        """
        Generate complete manifest with all resources
        
        Args:
            config_id: Config ID
            
        Returns:
            Complete YAML manifest
        """
        if config_id not in self.configs:
            return ""
        
        config = self.configs[config_id]
        
        manifest = self.get_namespace_manifest(config.namespace)
        manifest += "\n---\n" + self.get_serviceaccount_manifest(config_id)
        
        if config.config_map:
            manifest += "\n---\n" + self.get_configmap_manifest(config_id)
        
        if config.secrets:
            manifest += "\n---\n" + self.get_secret_manifest(config_id)
        
        manifest += "\n---\n" + self.get_deployment_manifest(config_id)
        manifest += "\n---\n" + self.get_service_manifest(config_id)
        
        if config.persistent_storage.enabled:
            manifest += "\n---\n" + self.get_pvc_manifest(config_id)
        
        if config.enable_autoscaling:
            manifest += "\n---\n" + self.get_hpa_manifest(config_id)
        
        if config.enable_ingress:
            manifest += "\n---\n" + self.get_ingress_manifest(config_id)
        
        if config.enable_network_policy:
            manifest += "\n---\n" + self.get_network_policy_manifest(config_id)
        
        return manifest
    
    def _get_probe_spec(self, probe_type: str, probe_config: ProbeConfig) -> str:
        """Get probe specification"""
        spec = f"""        {probe_type}:
          httpGet:
            path: {probe_config.path or '/health'}
            port: {probe_config.port}
          initialDelaySeconds: {probe_config.initial_delay_seconds}
          periodSeconds: {probe_config.period_seconds}
          timeoutSeconds: {probe_config.timeout_seconds}
          failureThreshold: {probe_config.failure_threshold}
          successThreshold: {probe_config.success_threshold}
"""
        return spec


# Singleton instance
_kubernetes_generator = None

def get_kubernetes_generator() -> KubernetesGenerator:
    """Get Kubernetes Generator singleton"""
    global _kubernetes_generator
    if _kubernetes_generator is None:
        _kubernetes_generator = KubernetesGenerator()
    return _kubernetes_generator
