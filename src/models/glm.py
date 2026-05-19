from __future__ import annotations

# mypy: disable-error-code="abstract, arg-type, assignment, attr-defined, call-arg, call-overload, dict-item, func-returns-value, import-untyped, index, misc, no-any-return, no-redef, operator, override, return, return-value, syntax, union-attr, var-annotated"


"""
智谱 GLM (ChatGLM) 模型适配器

API: https://open.bigmodel.cn/api/paas/v4
文档: https://open.bigmodel.cn/dev/api

特点：
- 智谱华章自研大模型
- 中文能力出色
- 开源版本 ChatGLM3 可本地部署
- 支持工具调用（Function Calling）
"""

import json
import time
from collections.abc import AsyncIterator
from typing import Any, Optional

import httpx

from .base import (
    BaseModel,
    Message,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    ModelTier,
    Usage,
)

# GLM 模型配置
GLM_MODELS = {
    "low": {
        "name": "glm-4-flash",
        "cost_per_1k_prompt": 0.001,
        "cost_per_1k_completion": 0.001,
    },
    "medium": {
        "name": "glm-4",
        "cost_per_1k_prompt": 0.1,
        "cost_per_1k_completion": 0.1,
    },
    "high": {
        "name": "glm-4-plus",
        "cost_per_1k_prompt": 0.1,
        "cost_per_1k_completion": 0.1,
    },
}


class GLMModel(BaseModel):
    """
    智谱 GLM (ChatGLM) 模型适配器

    兼容 OpenAI 格式，base URL: https://open.bigmodel.cn/api/paas/v4
    """

    def __init__(
        self,
        config: ModelConfig,
        tier: ModelTier = ModelTier.MEDIUM,
    ):
        if config.base_url is None:
            config.base_url = "https://open.bigmodel.cn/api/paas/v4"

        tier_key = tier.value
        model_info = GLM_MODELS.get(tier_key, GLM_MODELS["medium"])
        config.cost_per_1k_prompt = model_info["cost_per_1k_prompt"]
        config.cost_per_1k_completion = model_info["cost_per_1k_completion"]

        super().__init__(config, tier)

    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.GLM

    @property
    def model_name(self) -> str:
        return GLM_MODELS[self.tier.value]["name"]

    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._get_client()

        # 使用基类方法构建请求体
        request_body = self._build_request_body(messages, **kwargs)

        start_time = time.time()

        async def _do_request():
            """核心请求逻辑，供重试机制调用"""
            response = await client.post("/chat/completions", json=request_body)
            response.raise_for_status()
            return response

        try:
            # 使用基类的重试机制
            response = await self._execute_with_retry(_do_request)
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            choice = data["choices"][0]
            delta = choice["message"]

            # GLM 可能返回 text 或 content 或 tool_calls
            content = ""
            if "text" in delta:
                content = delta["text"]
            elif "content" in delta:
                content = delta["content"] or ""

            tool_calls = delta.get("tool_calls", [])

            usage_data = data.get("usage", {})
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            self.update_usage(usage)

            return ModelResponse(
                content=content,
                model=self.model_name,
                provider=self.provider,
                tier=self.tier,
                usage=usage,
                finish_reason=choice.get("finish_reason", "stop"),
                latency_ms=latency_ms,
                metadata={"response_id": data.get("id")},
                tool_calls=tool_calls,
            )

        except httpx.HTTPStatusError as e:
            raise GLMAPIError(f"智谱 GLM API 错误 ({e.response.status_code}): {e}")
        except httpx.RequestError as e:
            raise GLMAPIError(f"网络请求失败: {e}")

    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[str]:
        client = await self._get_client()

        # 使用基类方法构建请求体
        request_body = self._build_request_body(messages, **kwargs)
        request_body["stream"] = True

        try:
            async with client.stream(
                "POST", "/chat/completions", json=request_body
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", delta.get("text", ""))
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

        except httpx.HTTPStatusError as e:
            raise GLMAPIError(f"智谱 GLM API 错误 ({e.response.status_code}): {e}")
        except httpx.RequestError as e:
            raise GLMAPIError(f"网络请求失败: {e}")


class GLMAPIError(Exception):
    """智谱 GLM API 错误"""
