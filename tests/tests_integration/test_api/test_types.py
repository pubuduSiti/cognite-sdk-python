from datetime import datetime
from unittest import mock

import pytest

import cognite.client.utils._time
from cognite.client import CogniteClient, utils
from cognite.client.data_classes import Type, TypeFilter, TypeList, TypeUpdate
from cognite.client.utils._auxiliary import random_string
from tests.utils import set_request_limit

COGNITE_CLIENT = CogniteClient()


@pytest.fixture
def new_type():
    type = COGNITE_CLIENT.types.create(Type(external_id=random_string(30)))
    yield type
    COGNITE_CLIENT.types.delete(id=type.id)
    assert COGNITE_CLIENT.types.retrieve(type.id) is None


@pytest.fixture
def post_spy():
    with mock.patch.object(COGNITE_CLIENT.type, "_post", wraps=COGNITE_CLIENT.types._post) as _:
        yield


class TestTypesAPI:
    def test_retrieve(self):
        res = COGNITE_CLIENT.types.list(limit=1)
        assert res[0] == COGNITE_CLIENT.types.retrieve(res[0].id)

    def test_retrieve_multiple(self):
        res_listed_ids = [e.id for e in COGNITE_CLIENT.types.list(limit=2)]
        res_lookup_ids = [e.id for e in COGNITE_CLIENT.types.retrieve_multiple(res_listed_ids)]
        for listed_id in res_listed_ids:
            assert listed_id in res_lookup_ids

    def test_list(self, post_spy):
        with set_request_limit(COGNITE_CLIENT.events, 10):
            res = COGNITE_CLIENT.types.list(limit=20)

        assert 20 == len(res)
        assert 2 == COGNITE_CLIENT.types._post.call_count

    def test_update(self, new_event):
        update_asset = TypeUpdate(new_event.id).description.set("bla")
        res = COGNITE_CLIENT.types.update(update_asset)
        assert "bla" == res.description