from drf_haystack.serializers import HaystackSerializer
from precise_bbcode.bbcode import get_parser
from rest_framework import serializers

from astrobin.search_indexes import NestedCommentIndex
from common.serializers import AvatarField
from .models import NestedComment


class NestedCommentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=NestedComment.objects.all(),
        allow_null=True
    )
    author_avatar = AvatarField(source='author', required=False)
    author_username = serializers.SerializerMethodField(read_only=True)
    author_display_name = serializers.SerializerMethodField(read_only=True)
    html = serializers.SerializerMethodField(read_only=True)

    def get_author_username(self, comment: NestedComment) -> str:
        return comment.author.username

    def get_author_display_name(self, comment: NestedComment) -> str:
        return comment.author.userprofile.get_display_name()

    def get_html(self, comment: NestedComment) -> str:
        parser = get_parser()
        return parser.render(comment.text)

    class Meta:
        model = NestedComment
        fields = (
            'id',
            'author',
            'author_avatar',
            'author_username',
            'author_display_name',
            'content_type',
            'object_id',
            'text',
            'html',
            'created',
            'updated',
            'deleted',
            'pending_moderation',
            'parent',
            'depth',
            'likes',
        )


class NestedCommentSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [NestedCommentIndex]
