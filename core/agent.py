import os
import json
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI, RateLimitError, APIStatusError, NotFoundError, BadRequestError, AuthenticationError
from config.settings import settings
from core.prompts import SYSTEM_PROMPT
from core.memory import memory
from core.state import state_manager, SystemState
from core.permissions import permission_gate
from tools.registry import tool_registry

AFFIRMATIVE_RESPONSES = {
    "yes", "yeah", "yep", "proceed", "confirm", "go ahead", "do it", 
    "sure", "ok", "okay", "affirmative", "run it", "approved", "execute"
}

NEGATIVE_RESPONSES = {
    "no", "nope", "cancel", "abort", "stop", "dont", "don't", 
    "nevermind", "deny", "negative", "halt"
}

class JarvisAgent:
    def __init__(self):
        self.client = None
        self._active_model = None
        self.pending_confirmation: Optional[Dict[str, Any]] = None

    def get_effective_config(self):
        """Resolves API Key, Base URL, and Model with smart auto-alignment."""
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "").strip()
        base_url = settings.OPENAI_BASE_URL or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        model_name = settings.LLM_MODEL or os.getenv("LLM_MODEL", "gemini-2.0-flash").strip()

        # Auto-align mismatched Key & Base URL
        if api_key.startswith("AQ.") or api_key.startswith("AIzaSy"):
            # Google Gemini Key
            if "openrouter.ai" in base_url or "api.openai.com" in base_url or "api.groq.com" in base_url:
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
                if ":" in model_name or "meta-llama" in model_name:
                    model_name = "gemini-2.0-flash"
        elif api_key.startswith("sk-or-v1-"):
            # OpenRouter Key
            base_url = "https://openrouter.ai/api/v1"
            if model_name in ("gemini-2.0-flash", "gpt-4o-mini", "llama-3.3-70b-versatile"):
                model_name = "google/gemini-2.0-flash-exp:free"
        elif api_key.startswith("gsk_"):
            # Groq Key
            base_url = "https://api.groq.com/openai/v1"
            if "gemini" in model_name:
                model_name = "llama-3.3-70b-versatile"

        return api_key, base_url, model_name

    def get_client(self) -> AsyncOpenAI:
        if self.client is not None:
            return self.client

        api_key, base_url, _ = self.get_effective_config()
        
        headers = {}
        if "openrouter.ai" in base_url.lower():
            headers = {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "JARVIS Assistant"
            }
            
        return AsyncOpenAI(
            api_key=api_key or "none", 
            base_url=base_url, 
            default_headers=headers if headers else None
        )

    def get_model(self) -> str:
        if self._active_model:
            return self._active_model
        _, _, model_name = self.get_effective_config()
        return model_name

    def _get_fallback_candidates(self, base_url: str, initial_model: str) -> list:
        base_url_lower = (base_url or "").lower()
        if "openrouter.ai" in base_url_lower:
            candidates = [
                "google/gemini-2.0-flash-exp:free",
                "deepseek/deepseek-chat:free",
                "meta-llama/llama-3.1-8b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free"
            ]
        elif "groq.com" in base_url_lower:
            candidates = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
        elif "googleapis.com" in base_url_lower:
            candidates = ["gemini-2.0-flash", "gemini-1.5-flash"]
        elif "openai.com" in base_url_lower:
            candidates = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        else:
            candidates = ["llama3.2", "llama3.1", "llama3"]

        return [initial_model] + [m for m in candidates if m != initial_model]

    async def _create_completion_with_retry(self, client: AsyncOpenAI, **kwargs):
        """Executes completion with automatic retry on rate limits and model fallbacks."""
        initial_model = kwargs.get("model", self.get_model())
        base_url = str(client.base_url)
        models_to_try = self._get_fallback_candidates(base_url, initial_model)
        
        last_error = None
        for m in models_to_try:
            kwargs["model"] = m
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = await client.chat.completions.create(**kwargs)
                    if m != self._active_model:
                        self._active_model = m
                        print(f"[AGENT] Active model resolved to: '{m}'")
                    return response
                except AuthenticationError as auth_err:
                    raise auth_err
                except (RateLimitError, APIStatusError, NotFoundError, BadRequestError) as err:
                    err_str = str(err).lower()
                    is_rate_limit = (
                        isinstance(err, RateLimitError) or 
                        getattr(err, "status_code", None) == 429 or 
                        "429" in err_str or 
                        "resource_exhausted" in err_str
                    )
                    if is_rate_limit and attempt < max_retries:
                        wait_sec = 3.0 * (attempt + 1)
                        print(f"\n[AGENT] Rate limit reached. Retrying in {wait_sec:.0f}s (attempt {attempt+1}/{max_retries})...")
                        await asyncio.sleep(wait_sec)
                        continue
                        
                    is_model_unavailable = any(k in err_str for k in [
                        "unavailable for free", "model_not_found", "decommissioned", 
                        "not found", "does not exist"
                    ])
                    if is_model_unavailable:
                        print(f"[AGENT WARN] Model '{m}' unavailable ({err_str[:70]}...). Trying next candidate...")
                        last_error = err
                        break
                    raise err

        if last_error:
            raise last_error

    async def _execute_single_tool(self, tool_call) -> Any:
        fn_name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
        except Exception:
            args = {}

        tool = tool_registry.get_tool(fn_name)
        if tool:
            return await tool.execute(**args)
        return f"Error: Tool {fn_name} not found."

    async def process_user_input(self, text: str) -> str:
        if not text or not text.strip():
            return "How may I help you, Sir?"

        clean_text = text.strip().lower()

        # 1. Handle Pending Confirmation Check
        if self.pending_confirmation:
            pending = self.pending_confirmation
            self.pending_confirmation = None

            # Check for Affirmative response
            is_confirmed = any(word in clean_text.split() for word in AFFIRMATIVE_RESPONSES) or clean_text in AFFIRMATIVE_RESPONSES
            is_denied = any(word in clean_text.split() for word in NEGATIVE_RESPONSES) or clean_text in NEGATIVE_RESPONSES

            if is_confirmed and not is_denied:
                await state_manager.set_state(SystemState.EXECUTING)
                tool_call = pending["tool_call"]
                messages = pending["messages"]
                fn_name = pending["fn_name"]

                print(f"[PERMISSION] ✅ User confirmed execution of '{fn_name}'.")
                result = await self._execute_single_tool(tool_call)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result
                })

                client = self.get_client()
                active_model = self.get_model()
                final_res = await self._create_completion_with_retry(
                    client,
                    model=active_model,
                    messages=messages
                )
                final_text = final_res.choices[0].message.content or f"Action {fn_name} completed successfully, Sir."
                memory.add_message("assistant", final_text)
                await state_manager.set_state(SystemState.IDLE)
                return final_text
            else:
                await state_manager.set_state(SystemState.IDLE)
                cancel_msg = f"Understood, Sir. I have cancelled the execution of {pending['fn_name']}."
                memory.add_message("assistant", cancel_msg)
                return cancel_msg

        await state_manager.set_state(SystemState.THINKING)
        memory.add_message("user", text)
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(memory.get_recent_history(limit=10))
        
        tools = tool_registry.get_openai_tools()
        client = self.get_client()
        model_name = self.get_model()
        
        try:
            max_autonomous_steps = 6
            step_count = 0
            final_text = "All systems nominal, Sir."

            while step_count < max_autonomous_steps:
                step_count += 1
                kwargs = {
                    "model": model_name,
                    "messages": messages,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = await self._create_completion_with_retry(client, **kwargs)
                msg = response.choices[0].message

                # If no tool calls, conversation turn is complete
                if not msg.tool_calls:
                    final_text = msg.content or "All systems nominal, Sir."
                    break

                # Execute Autonomous Tool Loop
                await state_manager.set_state(SystemState.EXECUTING)
                messages.append(msg)

                has_pending_confirmation = False

                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    except Exception:
                        args = {}
                    
                    # Security Policy Gate Check
                    policy = permission_gate.check_permission(fn_name)
                    if policy == "require_confirmation":
                        self.pending_confirmation = {
                            "tool_call": tool_call,
                            "fn_name": fn_name,
                            "args": args,
                            "messages": messages
                        }
                        has_pending_confirmation = True
                        final_text = f"Sir, executing {fn_name} requires your confirmation. Should I proceed?"
                        break
                    elif policy == "deny":
                        result = f"Error: Execution of {fn_name} is prohibited by security policy."
                    else:
                        result = await self._execute_single_tool(tool_call)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result) if not isinstance(result, str) else result
                    })

                if has_pending_confirmation:
                    break

            memory.add_message("assistant", final_text)
            return final_text

        except AuthenticationError as auth_err:
            print(f"\n[AGENT AUTH ERROR] {auth_err}")
            return "Sir, authentication failed (401). Please verify that your API key matches the configured provider URL in .env."
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "rate" in err_msg.lower():
                user_msg = "Sir, we have momentarily reached our free API request quota. Please wait a few moments and try again."
            else:
                user_msg = f"I encountered an issue processing that: {err_msg}"
            print(f"\n[AGENT ERROR] {err_msg}")
            return user_msg
        finally:
            await state_manager.set_state(SystemState.IDLE)

jarvis_agent = JarvisAgent()