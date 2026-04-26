from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # AI 模型 API Keys
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    anthropic_api_key: str = ""

    # 默认模型
    default_model: str = "openai"

    # 认证配置
    secret_key: str = "change-me-in-production"

    # 速率限制（每分钟请求数）
    rate_limit_per_minute: int = 60

    # 上传文件限制（字节，默认10MB）
    max_upload_size: int = 10 * 1024 * 1024

    # 上传文件过期时间（小时，默认24小时）
    upload_expiry_hours: int = 24

    # CORS 配置
    allowed_origins: str = "chrome-extension://*,moz-extension://*"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> List[str]:
        """将 CORS origins 字符串转换为列表"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# 全局配置实例
settings = Settings()
