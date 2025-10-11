"""
Checkpoint configuration loader module.

Loads and validates YAML checkpoint configurations for human-in-the-loop interactions.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import yaml
import os
import glob


@dataclass
class CheckpointOption:
    """Single option in a checkpoint.

    Attributes:
        value: Internal value (e.g., "proceed", "skip", "explain")
        label: Display text shown to user
        is_default: Whether this is the default option (exactly one per checkpoint)

    Example:
        >>> opt = CheckpointOption(value="yes", label="Yes, apply de-smoothing", is_default=True)
    """
    value: str
    label: str
    is_default: bool = False


@dataclass
class CheckpointConfig:
    """Configuration for a single checkpoint.

    Attributes:
        name: Checkpoint identifier (e.g., "checkpoint-post-diagnostics")
        stage: Display name for user (e.g., "Post-Diagnostics Review")
        prompt_template: Prompt with {placeholders} for data interpolation
        options: Available choices for user
        trigger_after: Optional step name to trigger after
        trigger_condition: Optional filter condition (Python expression)

    Example:
        >>> config = CheckpointConfig.from_yaml("checkpoint_configs/post-diagnostics.yaml")
        >>> print(config.stage)
        Post-Diagnostics Review
    """
    name: str
    stage: str
    prompt_template: str
    options: List[CheckpointOption]
    trigger_after: Optional[str] = None
    trigger_condition: Optional[str] = None

    @classmethod
    def from_yaml(cls, path: str) -> "CheckpointConfig":
        """Load checkpoint config from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            CheckpointConfig instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML structure is invalid or missing required fields
            yaml.YAMLError: If YAML syntax is invalid

        Example:
            >>> config = CheckpointConfig.from_yaml("rbsa/checkpoint_configs/post-diagnostics.yaml")
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Checkpoint config not found: {path}")

        with open(path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML syntax in {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Checkpoint config must be a YAML dictionary, got {type(data)}")

        # Validate required fields
        required_fields = ['name', 'stage', 'prompt_template', 'options']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields in {path}: {missing_fields}")

        # Parse options
        options = []
        for opt in data.get('options', []):
            if not isinstance(opt, dict):
                raise ValueError(f"Each option must be a dictionary, got {type(opt)}")
            if 'value' not in opt or 'label' not in opt:
                raise ValueError(f"Option missing 'value' or 'label' fields: {opt}")

            options.append(CheckpointOption(
                value=opt['value'],
                label=opt['label'],
                is_default=opt.get('default', False)
            ))

        if not options:
            raise ValueError(f"Checkpoint {data['name']} must have at least one option")

        # Validate: exactly one default
        defaults = [o for o in options if o.is_default]
        if len(defaults) == 0:
            raise ValueError(
                f"Checkpoint {data['name']} must have exactly one default option. "
                f"Set 'default: true' on one option."
            )
        if len(defaults) > 1:
            default_values = [o.value for o in defaults]
            raise ValueError(
                f"Checkpoint {data['name']} has {len(defaults)} default options: {default_values}. "
                f"Only one option can have 'default: true'."
            )

        # Validate: no duplicate values
        values = [o.value for o in options]
        if len(values) != len(set(values)):
            duplicates = [v for v in values if values.count(v) > 1]
            raise ValueError(
                f"Checkpoint {data['name']} has duplicate option values: {list(set(duplicates))}"
            )

        return cls(
            name=data['name'],
            stage=data['stage'],
            prompt_template=data['prompt_template'],
            options=options,
            trigger_after=data.get('trigger', {}).get('after_step'),
            trigger_condition=data.get('trigger', {}).get('condition')
        )

    def get_default_option(self) -> CheckpointOption:
        """Return the default option.

        Returns:
            The CheckpointOption marked as default

        Example:
            >>> config = CheckpointConfig.from_yaml("post-diagnostics.yaml")
            >>> default = config.get_default_option()
            >>> print(default.value)
            yes
        """
        return next(o for o in self.options if o.is_default)

    def format_prompt(self, data: Dict[str, Any]) -> str:
        """Format prompt template with data.

        Args:
            data: Dictionary with values to interpolate into prompt template

        Returns:
            Formatted prompt string

        Raises:
            KeyError: If required placeholder is missing from data

        Example:
            >>> config = CheckpointConfig.from_yaml("post-diagnostics.yaml")
            >>> data = {"ar1_coef": 0.234, "ar1_pvalue": 0.012, "n_obs": 120}
            >>> prompt = config.format_prompt(data)
        """
        try:
            return self.prompt_template.format(**data)
        except KeyError as e:
            raise KeyError(
                f"Missing required data field for checkpoint {self.name}: {e}. "
                f"Required fields can be found in the prompt_template placeholders."
            )


def load_checkpoint_configs(checkpoint_dir: str) -> Dict[str, CheckpointConfig]:
    """Load all checkpoint YAML files from directory.

    Args:
        checkpoint_dir: Directory containing checkpoint YAML files

    Returns:
        Dict mapping checkpoint name to CheckpointConfig

    Raises:
        FileNotFoundError: If checkpoint_dir doesn't exist
        ValueError: If any YAML file is invalid

    Example:
        >>> configs = load_checkpoint_configs("rbsa/checkpoint_configs/")
        >>> print(list(configs.keys()))
        ['checkpoint-post-diagnostics', 'checkpoint-candidate-review', ...]
    """
    if not os.path.exists(checkpoint_dir):
        raise FileNotFoundError(
            f"Checkpoint config directory not found: {checkpoint_dir}. "
            f"Create the directory and add YAML checkpoint configuration files."
        )

    if not os.path.isdir(checkpoint_dir):
        raise ValueError(f"checkpoint_dir must be a directory, got file: {checkpoint_dir}")

    configs = {}
    pattern = os.path.join(checkpoint_dir, "*.yaml")
    yaml_files = glob.glob(pattern)

    if not yaml_files:
        # Not an error - just no checkpoints defined yet
        return configs

    errors = []
    for yaml_path in sorted(yaml_files):
        try:
            config = CheckpointConfig.from_yaml(yaml_path)

            # Check for duplicate checkpoint names
            if config.name in configs:
                errors.append(
                    f"Duplicate checkpoint name '{config.name}' in files: "
                    f"{configs[config.name]._source_file} and {yaml_path}"
                )
                continue

            # Store config with source file for error reporting
            config._source_file = yaml_path
            configs[config.name] = config

        except Exception as e:
            errors.append(f"Failed to load {yaml_path}: {e}")

    if errors:
        error_msg = "\n".join(errors)
        raise ValueError(f"Errors loading checkpoint configs:\n{error_msg}")

    return configs
