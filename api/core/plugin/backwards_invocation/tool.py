from collections.abc import Generator
from typing import Any

from core.callback_handler.workflow_tool_callback_handler import DifyWorkflowCallbackHandler
from core.plugin.backwards_invocation.base import BaseBackwardsInvocation
from core.tools.entities.tool_entities import ToolInvokeMessage, ToolProviderType
from core.tools.tool_engine import ToolEngine
from core.tools.tool_manager import ToolManager
from core.tools.utils.message_transformer import ToolFileMessageTransformer


class PluginToolBackwardsInvocation(BaseBackwardsInvocation):
    """
    Backwards invocation for plugin tools.

    Used when the plugin (e.g. workflow/chatflow agent node) calls back to the API
    to run a tool. We apply the same agent-style output as ToolEngine.agent_invoke:
    when both TEXT and JSON exist, only TEXT is sent; output is truncated to 6000
    chars. This avoids context explosion for tools like Tavily in workflow agent.
    """

    # Message types that are not folded into the single TEXT for the LLM;
    # we pass them through so the plugin can show images/links etc.
    _BINARY_OR_LINK_TYPES = frozenset({
        ToolInvokeMessage.MessageType.IMAGE_LINK,
        ToolInvokeMessage.MessageType.BINARY_LINK,
        ToolInvokeMessage.MessageType.IMAGE,
        ToolInvokeMessage.MessageType.BLOB,
        ToolInvokeMessage.MessageType.LINK,
        ToolInvokeMessage.MessageType.FILE,
    })

    @classmethod
    def invoke_tool(
        cls,
        tenant_id: str,
        user_id: str,
        tool_type: ToolProviderType,
        provider: str,
        tool_name: str,
        tool_parameters: dict[str, Any],
        credential_id: str | None = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke tool and return agent-style output (TEXT priority + truncation)
        plus any binary/link messages for display.
        """
        try:
            tool_runtime = ToolManager.get_tool_runtime_from_plugin(
                tool_type, tenant_id, provider, tool_name, tool_parameters, credential_id
            )
            response = ToolEngine.generic_invoke(
                tool_runtime, tool_parameters, user_id, DifyWorkflowCallbackHandler(), workflow_call_depth=1
            )
            response = ToolFileMessageTransformer.transform_tool_invoke_messages(
                response, user_id=user_id, tenant_id=tenant_id
            )
            message_list = list(response)

            # Same logic as agent_invoke: one string for the LLM (TEXT priority, 6000 cap).
            plain_text = ToolEngine._convert_tool_response_to_str(message_list)
            yield ToolInvokeMessage(
                type=ToolInvokeMessage.MessageType.TEXT,
                message=ToolInvokeMessage.TextMessage(text=plain_text),
            )

            # Preserve binary/link messages so the plugin can show images, links, etc.
            for msg in message_list:
                if msg.type in cls._BINARY_OR_LINK_TYPES:
                    yield msg
        except Exception as e:
            raise e
