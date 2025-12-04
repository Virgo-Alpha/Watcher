"""
Configuration schema and validation for haunt configurations
"""
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class SelectorType(Enum):
    """Types of selectors supported"""
    CSS = "css"
    XPATH = "xpath"


class NormalizationType(Enum):
    """Types of normalization supported"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"


@dataclass
class SelectorConfig:
    """Configuration for a single selector"""
    selector_type: SelectorType
    selector: str
    
    @classmethod
    def from_string(cls, selector_string: str) -> 'SelectorConfig':
        """Create SelectorConfig from string like 'css:.status' or 'xpath://div'"""
        if selector_string.startswith('css:'):
            return cls(SelectorType.CSS, selector_string[4:])
        elif selector_string.startswith('xpath:'):
            return cls(SelectorType.XPATH, selector_string[6:])
        else:
            # Default to CSS selector
            return cls(SelectorType.CSS, selector_string)
    
    def to_string(self) -> str:
        """Convert back to string format"""
        return f"{self.selector_type.value}:{self.selector}"


@dataclass
class NormalizationConfig:
    """Configuration for value normalization"""
    type: NormalizationType
    transform: Optional[str] = None  # 'lowercase', 'uppercase', 'strip'
    strip: bool = True
    format: Optional[str] = None  # For date parsing
    regex_pattern: Optional[str] = None  # For text extraction
    regex_group: int = 0  # Which regex group to extract
    
    def normalize_value(self, value: str) -> Union[str, int, float, bool, None]:
        """Apply normalization to a value"""
        if value is None:
            return None
        
        # Convert to string first
        value = str(value)
        
        # Apply strip if enabled
        if self.strip:
            value = value.strip()
        
        # Apply regex extraction if specified
        if self.regex_pattern:
            match = re.search(self.regex_pattern, value)
            if match:
                value = match.group(self.regex_group)
            else:
                return None
        
        # Apply text transformations
        if self.transform == 'lowercase':
            value = value.lower()
        elif self.transform == 'uppercase':
            value = value.upper()
        
        # Apply type-specific normalization
        if self.type == NormalizationType.TEXT:
            return value
        elif self.type == NormalizationType.NUMBER:
            try:
                # Try integer first, then float
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return None
        elif self.type == NormalizationType.BOOLEAN:
            return value.lower() in ['true', '1', 'yes', 'on', 'enabled', 'active']
        elif self.type == NormalizationType.DATE:
            # For now, return as string - date parsing can be added later
            return value
        
        return value


@dataclass
class HauntConfig:
    """Complete haunt configuration"""
    selectors: Dict[str, SelectorConfig]
    normalization: Dict[str, NormalizationConfig]
    truthy_values: Dict[str, List[str]]
    
    def get_selector_string(self, key: str) -> Optional[str]:
        """Get selector string for a key"""
        if key in self.selectors:
            return self.selectors[key].to_string()
        return None
    
    def normalize_extracted_value(self, key: str, value: str) -> Union[str, int, float, bool, None]:
        """Normalize an extracted value using the configuration"""
        if key in self.normalization:
            return self.normalization[key].normalize_value(value)
        return value
    
    def is_truthy_value(self, key: str, value: Any) -> bool:
        """Check if a value is considered 'truthy' for change detection"""
        if key not in self.truthy_values:
            return bool(value)  # Default boolean check
        
        # Convert value to string for comparison
        value_str = str(value).lower() if value is not None else ""
        truthy_list = [v.lower() for v in self.truthy_values[key]]
        return value_str in truthy_list


class ConfigurationValidator:
    """Validates haunt configurations"""
    
    @staticmethod
    def validate_raw_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate raw configuration dictionary
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required top-level keys
        required_keys = ['selectors', 'normalization', 'truthy_values']
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return errors  # Don't continue if missing required keys
        
        # Validate selectors
        if not isinstance(config['selectors'], dict):
            errors.append("'selectors' must be a dictionary")
        else:
            for selector_name, selector_value in config['selectors'].items():
                if not isinstance(selector_value, str):
                    errors.append(f"Selector '{selector_name}' must be a string")
                else:
                    # Validate selector format
                    selector_errors = ConfigurationValidator._validate_selector(
                        selector_name, selector_value
                    )
                    errors.extend(selector_errors)
        
        # Validate normalization
        if not isinstance(config['normalization'], dict):
            errors.append("'normalization' must be a dictionary")
        else:
            for norm_name, norm_rules in config['normalization'].items():
                if not isinstance(norm_rules, dict):
                    errors.append(f"Normalization rules for '{norm_name}' must be a dictionary")
                else:
                    norm_errors = ConfigurationValidator._validate_normalization(
                        norm_name, norm_rules
                    )
                    errors.extend(norm_errors)
        
        # Validate truthy values
        if not isinstance(config['truthy_values'], dict):
            errors.append("'truthy_values' must be a dictionary")
        else:
            for truthy_name, truthy_list in config['truthy_values'].items():
                if not isinstance(truthy_list, list):
                    errors.append(f"Truthy values for '{truthy_name}' must be a list")
                else:
                    for i, value in enumerate(truthy_list):
                        if not isinstance(value, str):
                            errors.append(f"Truthy value {i} for '{truthy_name}' must be a string")
        
        return errors
    
    @staticmethod
    def _validate_selector(name: str, selector: str) -> List[str]:
        """Validate a single selector"""
        errors = []
        
        # Check if it has a valid prefix
        if not (selector.startswith('css:') or selector.startswith('xpath:')):
            # This is okay - we'll auto-add css: prefix
            pass
        
        # Basic CSS selector validation
        if selector.startswith('css:'):
            css_selector = selector[4:]
            if not css_selector.strip():
                errors.append(f"CSS selector for '{name}' cannot be empty")
        
        # Basic XPath validation
        elif selector.startswith('xpath:'):
            xpath_selector = selector[6:]
            if not xpath_selector.strip():
                errors.append(f"XPath selector for '{name}' cannot be empty")
        
        return errors
    
    @staticmethod
    def _validate_normalization(name: str, rules: Dict[str, Any]) -> List[str]:
        """Validate normalization rules"""
        errors = []
        
        # Check required 'type' field
        if 'type' not in rules:
            errors.append(f"Normalization rules for '{name}' must include 'type'")
            return errors
        
        # Validate type value
        valid_types = [t.value for t in NormalizationType]
        if rules['type'] not in valid_types:
            errors.append(f"Invalid normalization type '{rules['type']}' for '{name}'. "
                         f"Valid types: {valid_types}")
        
        # Validate optional fields
        if 'transform' in rules and rules['transform'] is not None:
            valid_transforms = ['lowercase', 'uppercase', 'strip']
            if rules['transform'] not in valid_transforms:
                errors.append(f"Invalid transform '{rules['transform']}' for '{name}'. "
                             f"Valid transforms: {valid_transforms}")
        
        if 'strip' in rules and not isinstance(rules['strip'], bool):
            errors.append(f"'strip' option for '{name}' must be a boolean")
        
        if 'regex_pattern' in rules and rules['regex_pattern'] is not None:
            try:
                re.compile(rules['regex_pattern'])
            except re.error as e:
                errors.append(f"Invalid regex pattern for '{name}': {e}")
        
        if 'regex_group' in rules and not isinstance(rules['regex_group'], int):
            errors.append(f"'regex_group' for '{name}' must be an integer")
        
        return errors
    
    @staticmethod
    def parse_config(config: Dict[str, Any]) -> HauntConfig:
        """
        Parse and validate a raw configuration into a HauntConfig object
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            HauntConfig object
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate first
        errors = ConfigurationValidator.validate_raw_config(config)
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        # Parse selectors
        selectors = {}
        for name, selector_str in config['selectors'].items():
            # Auto-add css: prefix if missing
            if not (selector_str.startswith('css:') or selector_str.startswith('xpath:')):
                selector_str = f"css:{selector_str}"
            selectors[name] = SelectorConfig.from_string(selector_str)
        
        # Parse normalization rules
        normalization = {}
        for name, rules in config['normalization'].items():
            norm_type = NormalizationType(rules['type'])
            normalization[name] = NormalizationConfig(
                type=norm_type,
                transform=rules.get('transform'),
                strip=rules.get('strip', True),
                format=rules.get('format'),
                regex_pattern=rules.get('regex_pattern'),
                regex_group=rules.get('regex_group', 0)
            )
        
        # Parse truthy values (already validated as lists of strings)
        truthy_values = config['truthy_values']
        
        return HauntConfig(
            selectors=selectors,
            normalization=normalization,
            truthy_values=truthy_values
        )


class ConfigurationStorage:
    """Utilities for storing and retrieving configurations"""
    
    @staticmethod
    def config_to_dict(config: HauntConfig) -> Dict[str, Any]:
        """Convert HauntConfig to dictionary for storage"""
        return {
            'selectors': {
                name: selector.to_string()
                for name, selector in config.selectors.items()
            },
            'normalization': {
                name: {
                    'type': norm.type.value,
                    'transform': norm.transform,
                    'strip': norm.strip,
                    'format': norm.format,
                    'regex_pattern': norm.regex_pattern,
                    'regex_group': norm.regex_group
                }
                for name, norm in config.normalization.items()
            },
            'truthy_values': config.truthy_values
        }
    
    @staticmethod
    def dict_to_config(config_dict: Dict[str, Any]) -> HauntConfig:
        """Convert dictionary to HauntConfig"""
        return ConfigurationValidator.parse_config(config_dict)