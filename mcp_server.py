"""MCP Server for StyleAgent - Integrates with Claude Desktop"""
import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from style_analyzer import StyleAnalyzer
from config import STYLE_PROFILE_DIR


class StyleAgentMCPServer:
    """MCP Server providing StyleAgent tools to Claude Desktop"""

    def __init__(self):
        self.analyzer = StyleAnalyzer()
        self.profiles_dir = STYLE_PROFILE_DIR

    def get_tools(self) -> list:
        """Return list of available tools"""
        return [
            {
                "name": "get_style_profile",
                "description": "Get the writing style profile for a specific language (korean or english). Returns detailed analysis of writing patterns, tone, vocabulary, and structural preferences.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["korean", "english"],
                            "description": "Language of the style profile to retrieve"
                        }
                    },
                    "required": ["language"]
                }
            },
            {
                "name": "get_style_summary",
                "description": "Get a human-readable summary of the writing style for a specific language. Use this to understand the user's writing style before generating text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["korean", "english"],
                            "description": "Language of the style profile"
                        }
                    },
                    "required": ["language"]
                }
            },
            {
                "name": "list_profiles",
                "description": "List all available style profiles",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_writing_guidelines",
                "description": "Get specific writing guidelines based on the style profile. Use this when you need to write text in the user's style.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["korean", "english"],
                            "description": "Language for the guidelines"
                        },
                        "doc_type": {
                            "type": "string",
                            "description": "Type of document (email, report, proposal, etc.)"
                        }
                    },
                    "required": ["language"]
                }
            },
            {
                "name": "analyze_text",
                "description": "Analyze a given text and create a temporary style profile. Useful for comparing styles or analyzing new text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "log_conversation",
                "description": "Log assistant response for future learning. Call this after generating text in user's style to enable incremental learning.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The generated text to log"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["korean", "english"],
                            "description": "Language of the text"
                        }
                    },
                    "required": ["text", "language"]
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Handle a tool call and return the result"""
        try:
            if tool_name == "get_style_profile":
                return self._get_style_profile(arguments.get("language", "english"))
            elif tool_name == "get_style_summary":
                return self._get_style_summary(arguments.get("language", "english"))
            elif tool_name == "list_profiles":
                return self._list_profiles()
            elif tool_name == "get_writing_guidelines":
                return self._get_writing_guidelines(
                    arguments.get("language", "english"),
                    arguments.get("doc_type")
                )
            elif tool_name == "analyze_text":
                return self._analyze_text(arguments.get("text", ""))
            elif tool_name == "log_conversation":
                return self._log_conversation(
                    arguments.get("text", ""),
                    arguments.get("language", "english")
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def _get_style_profile(self, language: str) -> dict:
        """Get full style profile for a language"""
        profile_path = self.profiles_dir / f"{language}.json"

        if not profile_path.exists():
            return {"error": f"Profile not found: {language}"}

        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        return {"profile": profile}

    def _get_style_summary(self, language: str) -> dict:
        """Get human-readable style summary"""
        profile_path = self.profiles_dir / f"{language}.json"

        if not profile_path.exists():
            return {"error": f"Profile not found: {language}"}

        self.analyzer.load_profile(str(profile_path))
        summary = self.analyzer.generate_report()

        return {"summary": summary}

    def _list_profiles(self) -> dict:
        """List available profiles"""
        profiles = []
        for p in self.profiles_dir.glob("*.json"):
            if not p.stem.endswith("_samples"):
                profiles.append({
                    "name": p.stem,
                    "path": str(p)
                })

        return {"profiles": profiles}

    def _get_writing_guidelines(self, language: str, doc_type: str = None) -> dict:
        """Generate specific writing guidelines from profile"""
        profile_path = self.profiles_dir / f"{language}.json"

        if not profile_path.exists():
            return {"error": f"Profile not found: {language}"}

        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        guidelines = []

        # Sentence length guidelines
        ss = profile.get("sentence_stats", {})
        avg_len = ss.get("avg_length_chars", 100)
        if avg_len < 80:
            guidelines.append("Use short, concise sentences (under 80 characters)")
        elif avg_len < 150:
            guidelines.append("Use moderate sentence length (80-150 characters)")
        else:
            guidelines.append("Use longer, more detailed sentences when appropriate")

        # Tone guidelines
        tone = profile.get("tone_analysis", {})
        if language == "korean":
            kr_tone = tone.get("primary_korean_tone", "formal")
            if kr_tone == "formal":
                guidelines.append("Use formal Korean endings (-습니다, -입니다)")
            else:
                guidelines.append("Use casual Korean endings (-해요, -어요)")
        else:
            en_tone = tone.get("primary_english_tone", "formal")
            if en_tone == "formal":
                guidelines.append("Maintain professional, formal tone")
            else:
                guidelines.append("Use casual, conversational tone")

        # Opening patterns
        opening = profile.get("opening_patterns", {})
        common_openings = opening.get("common_first_phrases", [])[:3]
        if common_openings:
            openings_str = ", ".join([f'"{p[0]}"' for p in common_openings])
            guidelines.append(f"Common opening patterns: {openings_str}")

        # Closing patterns
        closing = profile.get("closing_patterns", {})
        signoffs = closing.get("signoff_patterns", {})
        if signoffs:
            top_signoff = max(signoffs.items(), key=lambda x: x[1])[0]
            guidelines.append(f"Preferred sign-off: {top_signoff}")

        # Structure
        struct = profile.get("structural_patterns", {})
        patterns = struct.get("patterns", {})
        if patterns.get("uses_bullet_points"):
            guidelines.append("Use bullet points for lists")
        if patterns.get("uses_headers"):
            guidelines.append("Use headers to organize content")
        if patterns.get("uses_bold"):
            guidelines.append("Use **bold** for emphasis")

        # Signature phrases
        sig = profile.get("signature_phrases", {})
        bigrams = sig.get("signature_bigrams", [])[:5]
        if bigrams:
            phrases_str = ", ".join([f'"{b[0]}"' for b in bigrams])
            guidelines.append(f"Signature phrases: {phrases_str}")

        # Document type specific
        if doc_type:
            if doc_type.lower() in ["email", "이메일"]:
                guidelines.append("Include appropriate greeting and sign-off")
            elif doc_type.lower() in ["report", "보고서"]:
                guidelines.append("Use clear headers and organized structure")
            elif doc_type.lower() in ["proposal", "제안서"]:
                guidelines.append("Be persuasive while maintaining professional tone")

        return {
            "language": language,
            "doc_type": doc_type,
            "guidelines": guidelines
        }

    def _analyze_text(self, text: str) -> dict:
        """Analyze given text"""
        if not text or len(text) < 50:
            return {"error": "Text too short for meaningful analysis"}

        analyzer = StyleAnalyzer()
        profile = analyzer.analyze([text])

        return {
            "profile": profile,
            "summary": analyzer.generate_report()
        }

    def _log_conversation(self, text: str, language: str) -> dict:
        """Log text for future learning"""
        if not text:
            return {"error": "No text provided"}

        # Create logs directory
        logs_dir = self.profiles_dir / "conversation_logs"
        logs_dir.mkdir(exist_ok=True)

        # Log file path
        log_file = logs_dir / f"{language}_log.txt"

        # Append to log
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n\n---\n\n")
            f.write(text)

        return {
            "status": "logged",
            "language": language,
            "log_file": str(log_file),
            "message": f"Text logged for future learning. Run 'learn-append {log_file} -n {language}' to update profile."
        }


def run_stdio_server():
    """Run MCP server over stdio (for Claude Desktop integration)"""
    import sys

    server = StyleAgentMCPServer()

    # Write capabilities
    capabilities = {
        "jsonrpc": "2.0",
        "result": {
            "capabilities": {
                "tools": server.get_tools()
            }
        }
    }

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())
            method = request.get("method", "")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "styleagent-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": server.get_tools()
                    }
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = server.handle_tool_call(tool_name, arguments)
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {}
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Test mode - demonstrate tools
            server = StyleAgentMCPServer()
            print("Available tools:")
            for tool in server.get_tools():
                print(f"  - {tool['name']}: {tool['description'][:60]}...")

            print("\nTesting get_writing_guidelines...")
            result = server.handle_tool_call("get_writing_guidelines", {"language": "english"})
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: python mcp_server.py [test]")
            print("  Without arguments: Run as MCP server (stdio)")
            print("  test: Run test mode")
    else:
        # Run as MCP server
        run_stdio_server()
