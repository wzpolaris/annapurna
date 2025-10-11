"""
Checkpoint orchestration module.

Main CheckpointRunner class that manages human-in-the-loop interactions during
RBSA analysis. Presents formatted prompts, collects user decisions, handles
AI-powered explanations, and logs decision history.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
import time
import os
from .checkpoint_loader import CheckpointConfig, load_checkpoint_configs
from .checkpoint_data import prepare_checkpoint_data
from .rbsa_utils import Summarizer


class CheckpointRunner:
    """Orchestrates human-in-the-loop checkpoints.

    Design Philosophy:
        - Load checkpoint configs from YAML files (declarative, modular)
        - Present formatted prompts to user (context-aware)
        - Collect multiple-choice responses (simple, validated)
        - Handle "explain" option with AI assistance (optional, graceful)
        - Log decision history for audit/reproducibility

    Attributes:
        cfg: Project configuration dict
        summarizer: AI summarizer for explanations (can be None)
        enabled: Whether interactive mode is enabled
        checkpoints: Dict of loaded CheckpointConfig objects
        history: List of all checkpoint decisions

    Example:
        >>> runner = CheckpointRunner(cfg, summarizer)
        >>> decision = runner.run_checkpoint("checkpoint-post-diagnostics", context)
        >>> print(decision)
        'yes'
    """

    def __init__(
        self,
        cfg: Dict[str, Any],
        summarizer: Optional[Summarizer] = None,
        checkpoint_dir: Optional[str] = None
    ):
        """Initialize checkpoint runner.

        Args:
            cfg: Project configuration dict
            summarizer: AI summarizer for explanations (None to disable AI explanations)
            checkpoint_dir: Path to checkpoint YAML files (default: "rbsa/checkpoint_configs/")

        Note:
            If interactive.enabled is False, no checkpoints will be loaded and
            run_checkpoint() will always return the default option immediately.
        """
        self.cfg = cfg
        self.enabled = cfg.get("interactive", {}).get("enabled", False)
        self.history: List[Dict[str, Any]] = []  # Track all decisions

        # Check if AI explanations are enabled
        use_ai_explanations = cfg.get("interactive", {}).get("use_ai_explanations", True)
        self.summarizer = summarizer if use_ai_explanations else None

        # Load checkpoint configurations only if interactive mode enabled
        if self.enabled:
            # Determine checkpoint directory
            if checkpoint_dir is None:
                # Default to rbsa/checkpoint_configs/
                rbsa_dir = os.path.dirname(__file__)
                checkpoint_dir = os.path.join(rbsa_dir, "checkpoint_configs")

            try:
                self.checkpoints = load_checkpoint_configs(checkpoint_dir)
                if self.checkpoints:
                    print(f"✓ Interactive mode enabled")
                    print(f"  Loaded {len(self.checkpoints)} checkpoint(s): {list(self.checkpoints.keys())}")
                else:
                    print(f"✓ Interactive mode enabled (no checkpoint configs found in {checkpoint_dir})")
            except Exception as e:
                print(f"⚠ Warning: Failed to load checkpoint configs: {e}")
                print(f"  Interactive mode will be disabled.")
                self.enabled = False
                self.checkpoints = {}
        else:
            self.checkpoints = {}

    def run_checkpoint(
        self,
        checkpoint_name: str,
        context: Dict[str, Any],
        auto_proceed: bool = False
    ) -> str:
        """Run a checkpoint and get user decision.

        This is the main entry point for triggering checkpoints. It handles the
        complete flow from data preparation to user input to logging.

        Args:
            checkpoint_name: Name of checkpoint (must match YAML filename stem)
            context: Raw data from analysis (passed to prepare function)
            auto_proceed: If True, return default without prompting (for testing)

        Returns:
            Selected option value (e.g., "proceed", "skip", "yes", "no", "1", "2")

        Flow:
            1. Check if interactive mode enabled (return default if not)
            2. Load checkpoint config
            3. Prepare data payload
            4. Format prompt with data
            5. Display prompt and options
            6. Get user input (handles "explain" internally)
            7. Validate and return choice
            8. Log decision to history

        Example:
            >>> decision = runner.run_checkpoint(
            ...     "checkpoint-post-diagnostics",
            ...     {"ar_test": {...}}
            ... )
            >>> print(decision)  # "yes" or "no"
        """
        # If disabled or auto_proceed, return default immediately
        if not self.enabled or auto_proceed:
            if checkpoint_name in self.checkpoints:
                return self.checkpoints[checkpoint_name].get_default_option().value
            else:
                # Graceful degradation if checkpoint not found
                return "proceed"

        # Load checkpoint config
        if checkpoint_name not in self.checkpoints:
            raise KeyError(
                f"Checkpoint not found: {checkpoint_name}. "
                f"Available checkpoints: {list(self.checkpoints.keys())}"
            )

        config = self.checkpoints[checkpoint_name]

        # Prepare data
        try:
            data = prepare_checkpoint_data(checkpoint_name, context)
        except Exception as e:
            print(f"⚠ Warning: Failed to prepare checkpoint data: {e}")
            print(f"  Using default option: {config.get_default_option().value}")
            return config.get_default_option().value

        # Format prompt
        try:
            prompt = config.format_prompt(data)
        except Exception as e:
            print(f"⚠ Warning: Failed to format checkpoint prompt: {e}")
            print(f"  Using default option: {config.get_default_option().value}")
            return config.get_default_option().value

        # Display checkpoint
        self._display_checkpoint(config, prompt)

        # Get user choice (handles "explain" internally)
        choice = self._get_user_choice(config, data)

        # Log decision
        self.history.append({
            "checkpoint": checkpoint_name,
            "stage": config.stage,
            "choice": choice,
            "timestamp": time.time(),
            "context_summary": str(data)[:200]  # Truncated for logging
        })

        return choice

    def _display_checkpoint(self, config: CheckpointConfig, prompt: str):
        """Display checkpoint header, prompt, and options.

        Args:
            config: Checkpoint configuration
            prompt: Formatted prompt text
        """
        print("\n" + "="*80)
        print(f"CHECKPOINT: {config.stage}")
        print("="*80)
        print()
        print(prompt)
        print()
        print("OPTIONS:")
        for i, opt in enumerate(config.options, 1):
            default_marker = " (default)" if opt.is_default else ""
            print(f"  {i}. {opt.label}{default_marker}")
        print()

    def _get_user_choice(self, config: CheckpointConfig, data: Dict[str, Any]) -> str:
        """Get and validate user choice.

        Handles multiple input formats:
            - Numeric input (1, 2, 3)
            - Full value input ("yes", "no", "explain")
            - Partial match (case-insensitive): "y"→"yes", "n"→"no", "e"→"explain"
            - Special: "?" → "explain"
            - Empty input → default
            - "explain" option → AI explanation, then re-prompt

        Args:
            config: Checkpoint configuration
            data: Prepared data for context (used in explanations)

        Returns:
            Selected option value

        Note:
            This method loops until valid input is received. If "explain" is
            selected, it shows an AI explanation and re-prompts.
        """
        default_option = config.get_default_option()
        option_values = [opt.value for opt in config.options]

        while True:
            # Prompt for input
            user_input = input(f"Your choice [default: {default_option.label}]: ").strip().lower()

            # Empty input → use default
            if not user_input:
                return default_option.value

            # Special case: "?" → "explain"
            if user_input == "?":
                explain_option = next((opt for opt in config.options if opt.value == "explain"), None)
                if explain_option:
                    self._show_explanation(config, data)
                    continue
                else:
                    print("Explain option not available for this checkpoint.")
                    continue

            # Try to parse as number (1, 2, 3)
            try:
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(config.options):
                    chosen_value = config.options[choice_idx].value
                    # If it's "explain", show explanation and re-prompt
                    if chosen_value == "explain":
                        self._show_explanation(config, data)
                        continue
                    return chosen_value
                else:
                    print(f"Invalid choice. Please enter 1-{len(config.options)}.")
                    continue
            except ValueError:
                pass  # Not a number, try value matching

            # Exact match
            if user_input in option_values:
                # If it's "explain", show explanation and re-prompt
                if user_input == "explain":
                    self._show_explanation(config, data)
                    continue
                return user_input

            # Partial match (case-insensitive, unique prefix)
            matches = [opt for opt in option_values if opt.startswith(user_input)]
            if len(matches) == 1:
                matched_value = matches[0]
                # If it's "explain", show explanation and re-prompt
                if matched_value == "explain":
                    self._show_explanation(config, data)
                    continue
                return matched_value
            elif len(matches) > 1:
                print(f"Ambiguous input '{user_input}' matches: {', '.join(matches)}. Please be more specific.")
                continue

            # Invalid input
            print(f"Invalid choice. Options: {', '.join(option_values)} (or 1-{len(config.options)})")

    def _show_explanation(self, config: CheckpointConfig, data: Dict[str, Any]):
        """Generate and display AI explanation for checkpoint.

        Args:
            config: Checkpoint configuration
            data: Prepared checkpoint data for context

        Note:
            If summarizer is None or explanation fails, shows a fallback message.
        """
        print("\n" + "-"*80)
        print("AI EXPLANATION")
        print("-"*80)

        # Check if AI explanations are available
        if self.summarizer is None:
            print("⚠ AI explanations are disabled (interactive.use_ai_explanations: false)")
            print("  Review the context above and make your choice based on the information provided.")
            print("-"*80 + "\n")
            return

        # Build explanation prompt
        explanation_prompt = f"""
Provide a detailed explanation for this decision point in the RBSA analysis:

CHECKPOINT: {config.stage}

CONTEXT:
{config.format_prompt(data)}

Please explain:
1. What this decision point means
2. The implications of each option
3. Your recommendation and why

Keep the explanation concise but thorough (2-3 paragraphs).
"""

        try:
            explanation = self.summarizer.summarize(explanation_prompt)
            print(explanation)
        except Exception as e:
            print(f"⚠ Could not generate explanation: {e}")
            print("Please make your choice based on the information provided above.")

        print("-"*80 + "\n")

    def should_trigger(
        self,
        checkpoint_name: str,
        step_name: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check if checkpoint should trigger based on trigger conditions.

        This method checks both the trigger_after (step name) and optional
        trigger_condition (Python expression) to determine if a checkpoint
        should run.

        Args:
            checkpoint_name: Name of checkpoint to check
            step_name: Current analysis step name
            context: Current analysis context (for condition evaluation)

        Returns:
            True if checkpoint should trigger, False otherwise

        Note:
            The trigger_condition uses eval() which is a security risk. This
            implementation assumes YAML configs are trusted (version-controlled,
            internal to project). For production use with untrusted configs,
            implement a safe expression evaluator.

        Example:
            >>> if runner.should_trigger("checkpoint-post-diagnostics", "desmoothing", context):
            ...     decision = runner.run_checkpoint("checkpoint-post-diagnostics", context)
        """
        if not self.enabled or checkpoint_name not in self.checkpoints:
            return False

        config = self.checkpoints[checkpoint_name]

        # Check trigger step
        if config.trigger_after and config.trigger_after != step_name:
            return False

        # Check optional condition (simple eval for now, could be more sophisticated)
        if config.trigger_condition:
            try:
                # WARNING: eval is dangerous in production with untrusted input
                # This implementation assumes YAML configs are trusted (internal, version-controlled)
                # For untrusted configs, use ast.literal_eval() or a safe expression parser
                return eval(config.trigger_condition, {}, context)
            except Exception:
                # If condition evaluation fails, don't trigger (fail safe)
                return False

        return True

    def export_history(self) -> Dict[str, Any]:
        """Export decision history for audit/reproducibility.

        Returns:
            Dict with enabled status, loaded checkpoints, and decision history

        Example:
            >>> history = runner.export_history()
            >>> import json
            >>> with open("checkpoint_history.json", "w") as f:
            ...     json.dump(history, f, indent=2, default=str)
        """
        return {
            "enabled": self.enabled,
            "checkpoints_loaded": list(self.checkpoints.keys()),
            "decisions": self.history,
            "total_decisions": len(self.history)
        }
