from unittest.mock import patch

import pytest

from federation.entities.activitypub.entities import ActivitypubFollow, ActivitypubAccept, ActivitypubProfile
from federation.entities.activitypub.mappers import message_to_objects, get_outbound_entity
from federation.entities.base import Accept, Follow, Profile
from federation.tests.fixtures.payloads import (
    ACTIVITYPUB_FOLLOW, ACTIVITYPUB_PROFILE, ACTIVITYPUB_PROFILE_INVALID, ACTIVITYPUB_UNDO_FOLLOW)


class TestActivitypubEntityMappersReceive:
    @patch.object(ActivitypubFollow, "post_receive", autospec=True)
    def test_message_to_objects__calls_post_receive_hook(self, mock_post_receive):
        message_to_objects(ACTIVITYPUB_FOLLOW, "https://example.com/actor")
        assert mock_post_receive.called

    def test_message_to_objects__follow(self):
        entities = message_to_objects(ACTIVITYPUB_FOLLOW, "https://example.com/actor")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubFollow)
        assert entity.actor_id == "https://example.com/actor"
        assert entity.target_id == "https://example.org/actor"
        assert entity.following is True

    def test_message_to_objects__unfollow(self):
        entities = message_to_objects(ACTIVITYPUB_UNDO_FOLLOW, "https://example.com/actor")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubFollow)
        assert entity.actor_id == "https://example.com/actor"
        assert entity.target_id == "https://example.org/actor"
        assert entity.following is False

    @pytest.mark.skip
    def test_message_to_objects_mentions_are_extracted(self):
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE_WITH_MENTION, "alice@alice.diaspora.example.org"
        )
        assert len(entities) == 1
        post = entities[0]
        assert post._mentions == {'jaywink@jasonrobinson.me'}

    @pytest.mark.skip
    def test_message_to_objects_simple_post(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "alice@alice.diaspora.example.org")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, DiasporaPost)
        assert isinstance(post, Post)
        assert post.raw_content == "((status message))"
        assert post.guid == "((guidguidguidguidguidguidguid))"
        assert post.handle == "alice@alice.diaspora.example.org"
        assert post.public == False
        assert post.created_at == datetime(2011, 7, 20, 1, 36, 7)
        assert post.provider_display_name == "Socialhome"

    @pytest.mark.skip
    def test_message_to_objects_post_with_photos(self):
        entities = message_to_objects(DIASPORA_POST_WITH_PHOTOS, "alice@alice.diaspora.example.org")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, DiasporaPost)
        photo = post._children[0]
        assert isinstance(photo, DiasporaImage)
        assert photo.remote_path == "https://alice.diaspora.example.org/uploads/images/"
        assert photo.remote_name == "1234.jpg"
        assert photo.raw_content == ""
        assert photo.linked_type == "Post"
        assert photo.linked_guid == "((guidguidguidguidguidguidguid))"
        assert photo.height == 120
        assert photo.width == 120
        assert photo.guid == "((guidguidguidguidguidguidguif))"
        assert photo.handle == "alice@alice.diaspora.example.org"
        assert photo.public == False
        assert photo.created_at == datetime(2011, 7, 20, 1, 36, 7)

    @pytest.mark.skip
    def test_message_to_objects_comment(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        assert len(entities) == 1
        comment = entities[0]
        assert isinstance(comment, DiasporaComment)
        assert isinstance(comment, Comment)
        assert comment.target_guid == "((parent_guidparent_guidparent_guidparent_guid))"
        assert comment.guid == "((guidguidguidguidguidguid))"
        assert comment.handle == "alice@alice.diaspora.example.org"
        assert comment.participation == "comment"
        assert comment.raw_content == "((text))"
        assert comment.signature == "((signature))"
        assert comment._xml_tags == [
            "guid", "parent_guid", "text", "author",
        ]
        mock_validate.assert_called_once_with()

    @pytest.mark.skip
    def test_message_to_objects_like(self, mock_validate):
        entities = message_to_objects(
            DIASPORA_POST_LIKE, "alice@alice.diaspora.example.org", sender_key_fetcher=Mock()
        )
        assert len(entities) == 1
        like = entities[0]
        assert isinstance(like, DiasporaLike)
        assert isinstance(like, Reaction)
        assert like.target_guid == "((parent_guidparent_guidparent_guidparent_guid))"
        assert like.guid == "((guidguidguidguidguidguid))"
        assert like.handle == "alice@alice.diaspora.example.org"
        assert like.participation == "reaction"
        assert like.reaction == "like"
        assert like.signature == "((signature))"
        assert like._xml_tags == [
            "parent_type", "guid", "parent_guid", "positive", "author",
        ]
        mock_validate.assert_called_once_with()

    def test_message_to_objects_profile(self):
        entities = message_to_objects(ACTIVITYPUB_PROFILE, "http://example.com/1234")
        assert len(entities) == 1
        profile = entities[0]
        assert profile.id == "https://diaspodon.fr/users/jaywink"
        assert profile.handle == ""
        assert profile.name == "Jason Robinson"
        assert profile.image_urls == {
            "large": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-4"
                     "3e9-4266-9b9a-b74a61ae4167.jpg?1538505110",
            "medium": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-4"
                      "3e9-4266-9b9a-b74a61ae4167.jpg?1538505110",
            "small": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-4"
                     "3e9-4266-9b9a-b74a61ae4167.jpg?1538505110",
        }
        assert profile.gender == ""
        assert profile.raw_content == "<p>Temp account while implementing AP for Socialhome.</p><p><a href=\"" \
                                      "https://jasonrobinson.me\" rel=\"nofollow noopener\" target=\"_blank\">" \
                                      "<span class=\"invisible\">https://</span><span class=\"\">jasonrobinson." \
                                      "me</span><span class=\"invisible\"></span></a> / <a href=\"https://social" \
                                      "home.network\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"i" \
                                      "nvisible\">https://</span><span class=\"\">socialhome.network</span><span c" \
                                      "lass=\"invisible\"></span></a> / <a href=\"https://feneas.org\" rel=\"nofoll" \
                                      "ow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><spa" \
                                      "n class=\"\">feneas.org</span><span class=\"invisible\"></span></a></p>"
        assert profile.location == ""
        assert profile.public is True
        assert profile.nsfw is False
        assert profile.tag_list == []

    @pytest.mark.skip
    def test_message_to_objects_receiving_actor_id_is_saved(self):
        # noinspection PyTypeChecker
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE,
            "alice@alice.diaspora.example.org",
            user=Mock(id="bob@example.com")
        )
        entity = entities[0]
        assert entity._receiving_actor_id == "bob@example.com"

    @pytest.mark.skip
    def test_message_to_objects_retraction(self):
        entities = message_to_objects(DIASPORA_RETRACTION, "bob@example.com")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaRetraction)
        assert entity.handle == "bob@example.com"
        assert entity.target_guid == "x" * 16
        assert entity.entity_type == "Post"

    @pytest.mark.skip
    def test_message_to_objects_accounce(self):
        entities = message_to_objects(DIASPORA_RESHARE, "alice@example.org")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaReshare)
        assert entity.handle == "alice@example.org"
        assert entity.guid == "a0b53e5029f6013487753131731751e9"
        assert entity.provider_display_name == ""
        assert entity.target_handle == "bob@example.com"
        assert entity.target_guid == "a0b53bc029f6013487753131731751e9"
        assert entity.public is True
        assert entity.entity_type == "Post"
        assert entity.raw_content == ""

    @pytest.mark.skip
    def test_message_to_objects_reshare_extra_properties(self):
        entities = message_to_objects(DIASPORA_RESHARE_WITH_EXTRA_PROPERTIES, "alice@example.org")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaReshare)
        assert entity.raw_content == "Important note here"
        assert entity.entity_type == "Comment"

    @patch("federation.entities.activitypub.mappers.logger.error")
    def test_invalid_entity_logs_an_error(self, mock_logger):
        entities = message_to_objects(ACTIVITYPUB_PROFILE_INVALID, "http://example.com/1234")
        assert len(entities) == 0
        assert mock_logger.called

    def test_adds_source_protocol_to_entity(self):
        entities = message_to_objects(ACTIVITYPUB_PROFILE, "http://example.com/1234")
        assert entities[0]._source_protocol == "activitypub"

    def test_source_object(self):
        entities = message_to_objects(ACTIVITYPUB_PROFILE, "http://example.com/1234")
        entity = entities[0]
        assert entity._source_object == ACTIVITYPUB_PROFILE

    @pytest.mark.skip
    def test_element_to_objects_calls_retrieve_remote_profile(self, mock_retrieve, mock_validate):
        message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org")
        mock_retrieve.assert_called_once_with("alice@alice.diaspora.example.org")

    @pytest.mark.skip
    def test_element_to_objects_verifies_handles_are_the_same(self, mock_check):
        message_to_objects(DIASPORA_POST_SIMPLE, "bob@example.org")
        mock_check.assert_called_once_with("bob@example.org", "alice@alice.diaspora.example.org")

    @pytest.mark.skip
    def test_element_to_objects_returns_no_entity_if_handles_are_different(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "bob@example.org")
        assert not entities


class TestGetOutboundEntity:
    def test_already_fine_entities_are_returned_as_is(self, private_key):
        entity = ActivitypubAccept()
        assert get_outbound_entity(entity, private_key) == entity
        entity = ActivitypubFollow()
        assert get_outbound_entity(entity, private_key) == entity
        entity = ActivitypubProfile()
        assert get_outbound_entity(entity, private_key) == entity

    def test_accept_is_converted_to_activitypubaccept(self, private_key):
        entity = Accept()
        assert isinstance(get_outbound_entity(entity, private_key), ActivitypubAccept)

    def test_follow_is_converted_to_activitypubfollow(self, private_key):
        entity = Follow()
        assert isinstance(get_outbound_entity(entity, private_key), ActivitypubFollow)

    def test_profile_is_converted_to_activitypubprofile(self, private_key):
        entity = Profile()
        assert isinstance(get_outbound_entity(entity, private_key), ActivitypubProfile)
