"""
Unit tests for configuration schema and validation
"""
import re
from django.test import TestCase
from apps.ai.config_schema import (
    SelectorConfig, SelectorType, NormalizationConfig, NormalizationType,
    HauntConfig, ConfigurationValidator, ConfigurationStorage
)


class SelectorConfigTest(TestCase):
    """Test cases for SelectorConfig"""
    
    def test_from_string_css_selector(self):
        """Test parsing CSS selector from string"""
        config = SelectorConfig.from_string("css:.status-indicator")
        self.assertEqual(config.selector_type, SelectorType.CSS)
        self.assertEqual(config.selector, ".status-indicator")
    
    def test_from_string_xpath_selector(self):
        """Test parsing XPath selector from string"""
        config = SelectorConfig.from_string("xpath://div[@class='status']")
        self.assertEqual(config.selector_type, SelectorType.XPATH)
        self.assertEqual(config.selector, "//div[@class='status']")
    
    def test_from_string_default_css(self):
        """Test that selectors without prefix default to CSS"""
        config = SelectorConfig.from_string(".status-indicator")
        self.assertEqual(config.selector_type, SelectorType.CSS)
        self.assertEqual(config.selector, ".status-indicator")
    
    def test_to_string_css(self):
        """Test converting CSS selector back to string"""
        config = SelectorConfig(SelectorType.CSS, ".status")
        self.assertEqual(config.to_string(), "css:.status")
    
    def test_to_string_xpath(self):
        """Test converting XPath selector back to string"""
        config = SelectorConfig(SelectorType.XPATH, "//div")
        self.assertEqual(config.to_string(), "xpath://div")


class NormalizationConfigTest(TestCase):
    """Test cases for NormalizationConfig"""
    
    def test_normalize_text_basic(self):
        """Test basic text normalization"""
        config = NormalizationConfig(
            type=NormalizationType.TEXT,
            transform="lowercase",
            strip=True
        )
        
        result = config.normalize_value("  HELLO WORLD  ")
        self.assertEqual(result, "hello world")
    
    def test_normalize_text_uppercase(self):
        """Test uppercase text normalization"""
        config = NormalizationConfig(
            type=NormalizationType.TEXT,
            transform="uppercase",
            strip=True
        )
        
        result = config.normalize_value("hello world")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_normalize_text_no_strip(self):
        """Test text normalization without stripping"""
        config = NormalizationConfig(
            type=NormalizationType.TEXT,
            transform="lowercase",
            strip=False
        )
        
        result = config.normalize_value("  HELLO  ")
        self.assertEqual(result, "  hello  ")
    
    def test_normalize_text_with_regex(self):
        """Test text normalization with regex extraction"""
        config = NormalizationConfig(
            type=NormalizationType.TEXT,
            regex_pattern=r"Status: (\w+)",
            regex_group=1,
            transform="lowercase"
        )
        
        result = config.normalize_value("Status: OPEN - Details here")
        self.assertEqual(result, "open")
    
    def test_normalize_text_regex_no_match(self):
        """Test text normalization with regex that doesn't match"""
        config = NormalizationConfig(
            type=NormalizationType.TEXT,
            regex_pattern=r"Status: (\w+)",
            regex_group=1
        )
        
        result = config.normalize_value("No status here")
        self.assertIsNone(result)
    
    def test_normalize_number_integer(self):
        """Test number normalization for integers"""
        config = NormalizationConfig(type=NormalizationType.NUMBER)
        
        result = config.normalize_value("42")
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)
    
    def test_normalize_number_float(self):
        """Test number normalization for floats"""
        config = NormalizationConfig(type=NormalizationType.NUMBER)
        
        result = config.normalize_value("42.5")
        self.assertEqual(result, 42.5)
        self.assertIsInstance(result, float)
    
    def test_normalize_number_invalid(self):
        """Test number normalization with invalid input"""
        config = NormalizationConfig(type=NormalizationType.NUMBER)
        
        result = config.normalize_value("not a number")
        self.assertIsNone(result)
    
    def test_normalize_boolean_true_values(self):
        """Test boolean normalization for true values"""
        config = NormalizationConfig(type=NormalizationType.BOOLEAN)
        
        true_values = ["true", "1", "yes", "on", "enabled", "active", "TRUE", "Yes"]
        for value in true_values:
            with self.subTest(value=value):
                result = config.normalize_value(value)
                self.assertTrue(result)
    
    def test_normalize_boolean_false_values(self):
        """Test boolean normalization for false values"""
        config = NormalizationConfig(type=NormalizationType.BOOLEAN)
        
        false_values = ["false", "0", "no", "off", "disabled", "inactive"]
        for value in false_values:
            with self.subTest(value=value):
                result = config.normalize_value(value)
                self.assertFalse(result)
    
    def test_normalize_date_passthrough(self):
        """Test date normalization (currently just passes through)"""
        config = NormalizationConfig(type=NormalizationType.DATE)
        
        result = config.normalize_value("2024-01-15")
        self.assertEqual(result, "2024-01-15")
    
    def test_normalize_none_value(self):
        """Test normalization with None input"""
        config = NormalizationConfig(type=NormalizationType.TEXT)
        
        result = config.normalize_value(None)
        self.assertIsNone(result)


class HauntConfigTest(TestCase):
    """Test cases for HauntConfig"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = HauntConfig(
            selectors={
                'status': SelectorConfig(SelectorType.CSS, '.status'),
                'deadline': SelectorConfig(SelectorType.XPATH, '//span[@class="deadline"]')
            },
            normalization={
                'status': NormalizationConfig(
                    type=NormalizationType.TEXT,
                    transform='lowercase'
                ),
                'deadline': NormalizationConfig(
                    type=NormalizationType.DATE
                )
            },
            truthy_values={
                'status': ['open', 'available', 'active']
            }
        )
    
    def test_get_selector_string(self):
        """Test getting selector string for a key"""
        self.assertEqual(self.config.get_selector_string('status'), 'css:.status')
        self.assertEqual(self.config.get_selector_string('deadline'), 'xpath://span[@class="deadline"]')
        self.assertIsNone(self.config.get_selector_string('nonexistent'))
    
    def test_normalize_extracted_value(self):
        """Test normalizing extracted values"""
        result = self.config.normalize_extracted_value('status', 'OPEN')
        self.assertEqual(result, 'open')
        
        # Key without normalization rules should return as-is
        result = self.config.normalize_extracted_value('unknown', 'value')
        self.assertEqual(result, 'value')
    
    def test_is_truthy_value_with_rules(self):
        """Test truthy value checking with defined rules"""
        self.assertTrue(self.config.is_truthy_value('status', 'open'))
        self.assertTrue(self.config.is_truthy_value('status', 'OPEN'))  # Case insensitive
        self.assertTrue(self.config.is_truthy_value('status', 'available'))
        self.assertFalse(self.config.is_truthy_value('status', 'closed'))
    
    def test_is_truthy_value_without_rules(self):
        """Test truthy value checking without defined rules (default boolean)"""
        self.assertTrue(self.config.is_truthy_value('deadline', 'some value'))
        self.assertFalse(self.config.is_truthy_value('deadline', ''))
        self.assertFalse(self.config.is_truthy_value('deadline', None))


class ConfigurationValidatorTest(TestCase):
    """Test cases for ConfigurationValidator"""
    
    def test_validate_valid_config(self):
        """Test validation of a valid configuration"""
        config = {
            'selectors': {
                'status': 'css:.status'
            },
            'normalization': {
                'status': {
                    'type': 'text',
                    'transform': 'lowercase'
                }
            },
            'truthy_values': {
                'status': ['open', 'available']
            }
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertEqual(errors, [])
    
    def test_validate_missing_required_keys(self):
        """Test validation with missing required keys"""
        config = {
            'selectors': {'status': 'css:.status'}
            # Missing normalization and truthy_values
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn('Missing required key: normalization', errors)
        self.assertIn('Missing required key: truthy_values', errors)
    
    def test_validate_invalid_selectors_type(self):
        """Test validation with invalid selectors type"""
        config = {
            'selectors': 'not a dict',
            'normalization': {},
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("'selectors' must be a dictionary", errors)
    
    def test_validate_invalid_selector_value_type(self):
        """Test validation with invalid selector value type"""
        config = {
            'selectors': {
                'status': 123  # Should be string
            },
            'normalization': {},
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Selector 'status' must be a string", errors)
    
    def test_validate_empty_css_selector(self):
        """Test validation with empty CSS selector"""
        config = {
            'selectors': {
                'status': 'css:'  # Empty selector
            },
            'normalization': {},
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("CSS selector for 'status' cannot be empty", errors)
    
    def test_validate_empty_xpath_selector(self):
        """Test validation with empty XPath selector"""
        config = {
            'selectors': {
                'status': 'xpath:'  # Empty selector
            },
            'normalization': {},
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("XPath selector for 'status' cannot be empty", errors)
    
    def test_validate_invalid_normalization_type(self):
        """Test validation with invalid normalization type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': 'not a dict',
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("'normalization' must be a dictionary", errors)
    
    def test_validate_invalid_normalization_rules_type(self):
        """Test validation with invalid normalization rules type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': 'not a dict'
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Normalization rules for 'status' must be a dictionary", errors)
    
    def test_validate_missing_normalization_type(self):
        """Test validation with missing normalization type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': {
                    'transform': 'lowercase'
                    # Missing 'type'
                }
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Normalization rules for 'status' must include 'type'", errors)
    
    def test_validate_invalid_normalization_type_value(self):
        """Test validation with invalid normalization type value"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': {
                    'type': 'invalid_type'
                }
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Invalid normalization type 'invalid_type'", errors[0])
    
    def test_validate_invalid_transform(self):
        """Test validation with invalid transform value"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': {
                    'type': 'text',
                    'transform': 'invalid_transform'
                }
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Invalid transform 'invalid_transform'", errors[0])
    
    def test_validate_invalid_strip_type(self):
        """Test validation with invalid strip type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': {
                    'type': 'text',
                    'strip': 'not a boolean'
                }
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("'strip' option for 'status' must be a boolean", errors)
    
    def test_validate_invalid_regex_pattern(self):
        """Test validation with invalid regex pattern"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': {
                    'type': 'text',
                    'regex_pattern': '[invalid regex'
                }
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertTrue(any('Invalid regex pattern' in error for error in errors))
    
    def test_validate_invalid_regex_group_type(self):
        """Test validation with invalid regex group type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {
                'status': {
                    'type': 'text',
                    'regex_group': 'not an integer'
                }
            },
            'truthy_values': {}
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("'regex_group' for 'status' must be an integer", errors)
    
    def test_validate_invalid_truthy_values_type(self):
        """Test validation with invalid truthy values type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {'status': {'type': 'text'}},
            'truthy_values': 'not a dict'
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("'truthy_values' must be a dictionary", errors)
    
    def test_validate_invalid_truthy_values_list_type(self):
        """Test validation with invalid truthy values list type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {'status': {'type': 'text'}},
            'truthy_values': {
                'status': 'not a list'
            }
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Truthy values for 'status' must be a list", errors)
    
    def test_validate_invalid_truthy_value_type(self):
        """Test validation with invalid truthy value type"""
        config = {
            'selectors': {'status': 'css:.status'},
            'normalization': {'status': {'type': 'text'}},
            'truthy_values': {
                'status': ['valid', 123, 'also_valid']  # 123 is not a string
            }
        }
        
        errors = ConfigurationValidator.validate_raw_config(config)
        self.assertIn("Truthy value 1 for 'status' must be a string", errors)
    
    def test_parse_config_success(self):
        """Test successful configuration parsing"""
        config_dict = {
            'selectors': {
                'status': 'css:.status',
                'deadline': 'xpath://span'
            },
            'normalization': {
                'status': {
                    'type': 'text',
                    'transform': 'lowercase'
                },
                'deadline': {
                    'type': 'date'
                }
            },
            'truthy_values': {
                'status': ['open', 'available']
            }
        }
        
        config = ConfigurationValidator.parse_config(config_dict)
        
        self.assertIsInstance(config, HauntConfig)
        self.assertEqual(len(config.selectors), 2)
        self.assertEqual(config.selectors['status'].selector_type, SelectorType.CSS)
        self.assertEqual(config.selectors['deadline'].selector_type, SelectorType.XPATH)
        self.assertEqual(config.normalization['status'].type, NormalizationType.TEXT)
        self.assertEqual(config.truthy_values['status'], ['open', 'available'])
    
    def test_parse_config_auto_css_prefix(self):
        """Test that selectors without prefix get css: prefix added"""
        config_dict = {
            'selectors': {
                'status': '.status-indicator'  # No prefix
            },
            'normalization': {
                'status': {'type': 'text'}
            },
            'truthy_values': {
                'status': ['open']
            }
        }
        
        config = ConfigurationValidator.parse_config(config_dict)
        self.assertEqual(config.selectors['status'].selector_type, SelectorType.CSS)
        self.assertEqual(config.selectors['status'].selector, '.status-indicator')
    
    def test_parse_config_validation_error(self):
        """Test configuration parsing with validation errors"""
        config_dict = {
            'selectors': {'status': 'css:.status'},
            # Missing required keys
        }
        
        with self.assertRaises(ValueError) as context:
            ConfigurationValidator.parse_config(config_dict)
        
        self.assertIn('Configuration validation failed', str(context.exception))


class ConfigurationStorageTest(TestCase):
    """Test cases for ConfigurationStorage"""
    
    def test_config_to_dict(self):
        """Test converting HauntConfig to dictionary"""
        config = HauntConfig(
            selectors={
                'status': SelectorConfig(SelectorType.CSS, '.status')
            },
            normalization={
                'status': NormalizationConfig(
                    type=NormalizationType.TEXT,
                    transform='lowercase',
                    strip=True,
                    regex_pattern=r'Status: (\w+)',
                    regex_group=1
                )
            },
            truthy_values={
                'status': ['open', 'available']
            }
        )
        
        result = ConfigurationStorage.config_to_dict(config)
        
        expected = {
            'selectors': {
                'status': 'css:.status'
            },
            'normalization': {
                'status': {
                    'type': 'text',
                    'transform': 'lowercase',
                    'strip': True,
                    'format': None,
                    'regex_pattern': r'Status: (\w+)',
                    'regex_group': 1
                }
            },
            'truthy_values': {
                'status': ['open', 'available']
            }
        }
        
        self.assertEqual(result, expected)
    
    def test_dict_to_config(self):
        """Test converting dictionary to HauntConfig"""
        config_dict = {
            'selectors': {
                'status': 'css:.status'
            },
            'normalization': {
                'status': {
                    'type': 'text',
                    'transform': 'lowercase'
                }
            },
            'truthy_values': {
                'status': ['open']
            }
        }
        
        config = ConfigurationStorage.dict_to_config(config_dict)
        
        self.assertIsInstance(config, HauntConfig)
        self.assertEqual(config.selectors['status'].selector_type, SelectorType.CSS)
        self.assertEqual(config.normalization['status'].type, NormalizationType.TEXT)
        self.assertEqual(config.truthy_values['status'], ['open'])
    
    def test_roundtrip_conversion(self):
        """Test that config -> dict -> config preserves data"""
        original_config = HauntConfig(
            selectors={
                'status': SelectorConfig(SelectorType.XPATH, '//div[@class="status"]')
            },
            normalization={
                'status': NormalizationConfig(
                    type=NormalizationType.BOOLEAN,
                    strip=False
                )
            },
            truthy_values={
                'status': ['true', 'active']
            }
        )
        
        # Convert to dict and back
        config_dict = ConfigurationStorage.config_to_dict(original_config)
        restored_config = ConfigurationStorage.dict_to_config(config_dict)
        
        # Check that data is preserved
        self.assertEqual(
            original_config.selectors['status'].selector_type,
            restored_config.selectors['status'].selector_type
        )
        self.assertEqual(
            original_config.selectors['status'].selector,
            restored_config.selectors['status'].selector
        )
        self.assertEqual(
            original_config.normalization['status'].type,
            restored_config.normalization['status'].type
        )
        self.assertEqual(
            original_config.truthy_values,
            restored_config.truthy_values
        )