"""
GPU 信息缓存模块

在程序启动时获取 GPU 信息并缓存，避免每次使用时重新检测导致卡顿。
"""

from typing import Dict, Optional
from app.utils.logger import logger


class GPUInfoCache:
    """GPU 信息缓存类（单例模式）"""
    
    _instance: Optional['GPUInfoCache'] = None
    _gpu_info: Optional[Dict[int, str]] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        """初始化 GPU 信息缓存
        
        在程序启动时调用一次，获取并缓存 GPU 信息
        """
        if self._initialized:
            logger.debug("GPU 信息已初始化，跳过")
            return
        
        logger.info("开始初始化 GPU 信息缓存...")
        
        try:
            from app.utils.tool import get_gpu_info
            
            self._gpu_info = get_gpu_info()
            self._initialized = True
            
            if self._gpu_info:
                logger.info(f"✅ GPU 信息缓存成功，检测到 {len(self._gpu_info)} 个 GPU 设备")
                for gpu_id, gpu_name in sorted(self._gpu_info.items()):
                    logger.debug(f"  GPU {gpu_id}: {gpu_name}")
            else:
                logger.info("⚠️ 未检测到 GPU 设备，将只使用 CPU/Auto 模式")
                self._gpu_info = {}
                
        except Exception as e:
            logger.error(f"❌ GPU 信息初始化失败: {e}")
            self._gpu_info = {}
            self._initialized = True
    
    def get_gpu_info(self) -> Dict[int, str]:
        """获取缓存的 GPU 信息
        
        Returns:
            Dict[int, str]: GPU 信息字典，键为 GPU ID，值为 GPU 名称
        """
        if not self._initialized:
            logger.warning("GPU 信息未初始化，现在初始化...")
            self.initialize()
        
        return self._gpu_info or {}
    
    def is_initialized(self) -> bool:
        """检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized
    
    def refresh(self):
        """刷新 GPU 信息
        
        强制重新获取 GPU 信息（通常不需要调用）
        """
        logger.info("强制刷新 GPU 信息...")
        self._initialized = False
        self._gpu_info = None
        self.initialize()


# 创建全局单例
gpu_cache = GPUInfoCache()
