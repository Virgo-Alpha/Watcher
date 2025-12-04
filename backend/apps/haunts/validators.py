"""
Security validators for haunt management
"""
import ipaddress
from urllib.parse import urlparse
from rest_framework import serializers


class URLSecurityValidator:
    """
    Validator to prevent SSRF attacks by blocking private IPs and localhost
    """
    
    ALLOWED_SCHEMES = ['http', 'https']
    BLOCKED_HOSTNAMES = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '0:0:0:0:0:0:0:1']
    
    @classmethod
    def validate_url(cls, url: str) -> str:
        """
        Validate URL to prevent SSRF attacks
        
        Args:
            url: URL to validate
            
        Returns:
            Validated URL
            
        Raises:
            serializers.ValidationError: If URL is invalid or blocked
        """
        if not url:
            raise serializers.ValidationError("URL is required")
        
        try:
            parsed = urlparse(url)
            
            # Only allow HTTP and HTTPS schemes
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                raise serializers.ValidationError(
                    f"Only {', '.join(cls.ALLOWED_SCHEMES).upper()} URLs are allowed"
                )
            
            # Validate hostname exists
            hostname = parsed.hostname
            if not hostname:
                raise serializers.ValidationError("Invalid URL: missing hostname")
            
            # Check for blocked hostnames
            if hostname.lower() in cls.BLOCKED_HOSTNAMES:
                raise serializers.ValidationError(
                    "Access to localhost is not allowed"
                )
            
            # Block private IP ranges
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise serializers.ValidationError(
                        "Access to private IP addresses is not allowed"
                    )
            except ValueError:
                # Not an IP address, hostname is valid
                pass
            
            return url
            
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(f"Invalid URL format: {str(e)}")
    
    @classmethod
    def is_safe_url(cls, url: str) -> bool:
        """
        Check if URL is safe without raising exceptions
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is safe, False otherwise
        """
        try:
            cls.validate_url(url)
            return True
        except serializers.ValidationError:
            return False
