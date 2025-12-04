"""
Serializers for RSS feed items
"""
from rest_framework import serializers
from .models import RSSItem


class RSSItemSerializer(serializers.ModelSerializer):
    """Serializer for RSS items"""

    haunt_name = serializers.CharField(source='haunt.name', read_only=True)
    haunt_url = serializers.URLField(source='haunt.url', read_only=True)
    age_in_hours = serializers.ReadOnlyField()
    has_ai_summary = serializers.ReadOnlyField()
    change_summary = serializers.SerializerMethodField()

    class Meta:
        model = RSSItem
        fields = [
            'id', 'haunt', 'haunt_name', 'haunt_url', 'title', 'description',
            'link', 'guid', 'pub_date', 'change_data', 'ai_summary',
            'age_in_hours', 'has_ai_summary', 'change_summary', 'created_at'
        ]
        read_only_fields = ['id', 'guid', 'created_at']

    def get_change_summary(self, obj):
        """Get change summary"""
        return obj.get_change_summary()