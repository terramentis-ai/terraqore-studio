"""
Ollama Bundler - Package Ollama runtime with TerraQore
Creates a distribution-ready bundle with pre-cached models
"""

import os
import sys
import shutil
import requests
import subprocess
import platform
from pathlib import Path
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OllamaBundler:
    """Bundle Ollama runtime for distribution"""
    
    OLLAMA_VERSION = "0.1.22"
    OLLAMA_DOWNLOAD_BASE = "https://github.com/ollama/ollama/releases/download"
    
    RECOMMENDED_MODELS = [
        "phi3:latest",      # 3.8GB
        "llama3:8b",        # 4.7GB
        "gemma2:9b"         # 5.4GB
    ]
    
    def __init__(self, terraqore_root: str):
        self.terraqore_root = Path(terraqore_root)
        self.runtime_dir = self.terraqore_root / "ollama_runtime"
        self.bin_dir = self.runtime_dir / "bin"
        self.models_dir = self.runtime_dir / "models"
        self.config_dir = self.runtime_dir / "config"
        
    def get_ollama_download_url(self) -> str:
        """Get platform-specific Ollama download URL"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            return f"{self.OLLAMA_DOWNLOAD_BASE}/v{self.OLLAMA_VERSION}/ollama-windows-amd64.zip"
        elif system == "linux":
            if "aarch64" in machine or "arm64" in machine:
                return f"{self.OLLAMA_DOWNLOAD_BASE}/v{self.OLLAMA_VERSION}/ollama-linux-arm64"
            else:
                return f"{self.OLLAMA_DOWNLOAD_BASE}/v{self.OLLAMA_VERSION}/ollama-linux-amd64"
        elif system == "darwin":
            return f"{self.OLLAMA_DOWNLOAD_BASE}/v{self.OLLAMA_VERSION}/ollama-darwin"
        else:
            raise ValueError(f"Unsupported platform: {system}")
    
    def download_ollama(self) -> Path:
        """Download Ollama executable for current platform"""
        url = self.get_ollama_download_url()
        logger.info(f"Downloading Ollama from {url}")
        
        # Determine output filename
        system = platform.system().lower()
        if system == "windows":
            output_file = self.bin_dir / "ollama.zip"
        else:
            output_file = self.bin_dir / "ollama"
        
        # Download
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total_size) * 100 if total_size else 0
                    print(f"\rDownload progress: {progress:.1f}%", end='', flush=True)
        
        print()  # New line
        logger.info(f"Downloaded to {output_file}")
        
        # Extract if Windows (ZIP)
        if system == "windows":
            logger.info("Extracting ZIP archive...")
            shutil.unpack_archive(output_file, self.bin_dir)
            output_file.unlink()  # Remove ZIP
            executable = self.bin_dir / "ollama.exe"
        else:
            executable = output_file
            # Make executable on Unix
            os.chmod(executable, 0o755)
        
        return executable
    
    def is_ollama_installed_system(self) -> bool:
        """Check if Ollama is already installed on system"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def copy_from_system_ollama(self) -> Optional[Path]:
        """Copy Ollama from system installation"""
        if not self.is_ollama_installed_system():
            return None
        
        logger.info("Found system Ollama installation, copying...")
        
        # Find ollama executable
        try:
            result = subprocess.run(
                ["which", "ollama"] if platform.system() != "Windows" else ["where", "ollama"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                system_ollama = Path(result.stdout.strip().split('\n')[0])
                bundled_ollama = self.bin_dir / system_ollama.name
                
                shutil.copy2(system_ollama, bundled_ollama)
                logger.info(f"Copied {system_ollama} to {bundled_ollama}")
                
                return bundled_ollama
        except Exception as e:
            logger.warning(f"Could not copy system Ollama: {e}")
        
        return None
    
    def pull_model(self, model: str) -> bool:
        """Pull a model using bundled Ollama"""
        logger.info(f"Pulling model: {model}")
        
        # Get bundled ollama path
        system = platform.system().lower()
        ollama_exe = self.bin_dir / ("ollama.exe" if system == "windows" else "ollama")
        
        if not ollama_exe.exists():
            logger.error(f"Ollama not found at {ollama_exe}")
            return False
        
        # Set OLLAMA_MODELS environment variable
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(self.models_dir)
        
        try:
            result = subprocess.run(
                [str(ollama_exe), "pull", model],
                env=env,
                capture_output=False,  # Show output
                timeout=600  # 10 minutes max per model
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled {model}")
                return True
            else:
                logger.error(f"Failed to pull {model} (exit code: {result.returncode})")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout pulling {model}")
            return False
        except Exception as e:
            logger.error(f"Error pulling {model}: {e}")
            return False
    
    def bundle(self, skip_download: bool = False, skip_models: bool = False):
        """Create complete Ollama bundle"""
        logger.info("Starting Ollama bundling process...")
        
        # Ensure directories exist
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Get Ollama executable
        if skip_download:
            logger.info("Skipping Ollama download (--skip-download)")
        else:
            # Try system installation first
            ollama_exe = self.copy_from_system_ollama()
            
            # Download if not found
            if not ollama_exe:
                ollama_exe = self.download_ollama()
        
        # Verify executable exists
        system = platform.system().lower()
        ollama_exe = self.bin_dir / ("ollama.exe" if system == "windows" else "ollama")
        
        if not ollama_exe.exists():
            logger.error(f"Ollama executable not found at {ollama_exe}")
            logger.error("Bundle incomplete. Run without --skip-download or install Ollama system-wide first.")
            return False
        
        logger.info(f"Ollama executable ready at {ollama_exe}")
        
        # Step 2: Pull models
        if skip_models:
            logger.info("Skipping model download (--skip-models)")
        else:
            logger.info(f"Pulling {len(self.RECOMMENDED_MODELS)} recommended models...")
            
            for model in self.RECOMMENDED_MODELS:
                success = self.pull_model(model)
                if not success:
                    logger.warning(f"Failed to pull {model}, continuing...")
        
        # Step 3: Report
        logger.info("=" * 60)
        logger.info("Bundle complete!")
        logger.info(f"Ollama runtime: {self.runtime_dir}")
        logger.info(f"Executable: {ollama_exe}")
        logger.info(f"Models: {self.models_dir}")
        
        # Check model sizes
        total_size = 0
        for model_file in self.models_dir.rglob("*"):
            if model_file.is_file():
                total_size += model_file.stat().st_size
        
        logger.info(f"Total model size: {total_size / (1024**3):.2f} GB")
        logger.info("=" * 60)
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Bundle Ollama runtime with TerraQore")
    parser.add_argument(
        "--terraqore-root",
        default=".",
        help="Path to TerraQore root directory (default: current directory)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading Ollama (use existing in bin/)"
    )
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip downloading models"
    )
    
    args = parser.parse_args()
    
    bundler = OllamaBundler(args.terraqore_root)
    success = bundler.bundle(skip_download=args.skip_download, skip_models=args.skip_models)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
