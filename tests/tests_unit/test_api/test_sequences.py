import json
import math
import os
import re
from unittest import mock

import pytest

from cognite.client.data_classes import Sequence, SequenceData, SequenceFilter, SequenceList, SequenceUpdate
from cognite.client.experimental import CogniteClient
from tests.utils import jsgz_load

COGNITE_CLIENT = CogniteClient()
SEQ_API = COGNITE_CLIENT.sequences


@pytest.fixture
def mock_seq_response(rsps):
    response_body = {
        "items": [
            {
                "id": 0,
                "externalId": "string",
                "name": "stringname",
                "metadata": {"metadata-key": "metadata-value"},
                "assetId": 0,
                "description": "string",
                #                "securityCategories": [0],
                "createdTime": 0,
                "lastUpdatedTime": 0,
                "columns": [
                    {
                        "id": 0,
                        "valueType": "STRING",
                        "metadata": {"column-metadata-key": "column-metadata-value"},
                        "createdTime": 0,
                        "lastUpdatedTime": 0,
                    },
                    {
                        "id": 1,
                        "externalId": "column2",
                        "valueType": "DOUBLE",
                        "metadata": {"column-metadata-key": "column-metadata-value"},
                        "createdTime": 0,
                        "lastUpdatedTime": 0,
                    },
                ],
            }
        ]
    }
    url_pattern = re.compile(
        re.escape(SEQ_API._get_base_url_with_base_path()) + "/sequences(?:/byids|/list|/update|/delete|/search|$|\?.+)"
    )
    rsps.assert_all_requests_are_fired = False

    rsps.add(rsps.POST, url_pattern, status=200, json=response_body)
    rsps.add(rsps.GET, url_pattern, status=200, json=response_body)
    yield rsps


@pytest.fixture
def mock_sequences_empty(rsps):
    response_body = {"items": []}
    url_pattern = re.compile(
        re.escape(SEQ_API._get_base_url_with_base_path()) + "/sequences(?:/byids|/update|/list|/delete|/search|$|\?.+)"
    )
    rsps.assert_all_requests_are_fired = False

    rsps.add(rsps.POST, url_pattern, status=200, json=response_body)
    rsps.add(rsps.GET, url_pattern, status=200, json=response_body)
    yield rsps


@pytest.fixture
def mock_post_sequence_data(rsps):
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data", status=200, json={})
    yield rsps


@pytest.fixture
def mock_get_sequence_data(rsps):
    json = {
        "items": [
            {
                "id": 0,
                "externalId": "eid",
                "columns": [{"id": 0, "externalId": "ceid"}],
                "rows": [{"rowNumber": 0, "values": [1]}],
            }
        ]
    }
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data/list", status=200, json=json)
    yield rsps


@pytest.fixture
def mock_get_sequence_empty_data(rsps):
    json = {
        "items": [{"id": 0, "externalId": "eid", "columns": [{"id": 0, "externalId": "ceid"}, {"id": 1}], "rows": []}]
    }
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data/list", status=200, json=json)
    yield rsps


@pytest.fixture
def mock_get_sequence_data_many_columns(rsps):
    json = {
        "items": [
            {
                "id": 0,
                "externalId": "eid",
                "columns": [{"id": i, "externalId": "ceid" + str(i)} for i in range(0, 200)],
                "rows": [{"rowNumber": 0, "values": ["str"] * 200}],
            }
        ]
    }
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data/list", status=200, json=json)
    yield rsps


@pytest.fixture
def mock_get_sequence_data_no_extid_in_columns(rsps):
    json = {
        "items": [
            {
                "id": 0,
                "externalId": "eid",
                "columns": [{"id": 0}, {"id": 1, "externalId": "col2"}],
                "rows": [{"rowNumber": 0, "values": [1, 2]}],
            }
        ]
    }
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data/list", status=200, json=json)
    yield rsps


@pytest.fixture
def mock_get_sequence_data_with_null(rsps):
    json = {
        "items": [
            {
                "id": 0,
                "externalId": "eid",
                "columns": [{"id": 0, "externalId": "intcol"}, {"id": 1, "externalId": "strcol"}],
                "rows": [{"rowNumber": 0, "values": [1, None]}, {"rowNumber": 1, "values": [None, "blah"]}],
            }
        ]
    }
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data/list", status=200, json=json)
    yield rsps


@pytest.fixture
def mock_delete_sequence_data(rsps):
    rsps.add(rsps.POST, SEQ_API._get_base_url_with_base_path() + "/sequences/data/delete", status=200, json={})
    yield rsps


class TestSequences:
    def test_retrieve_single(self, mock_seq_response):
        res = SEQ_API.retrieve(id=1)
        assert isinstance(res, Sequence)
        assert mock_seq_response.calls[0].response.json()["items"][0] == res.dump(camel_case=True)

    def test_column_ids(self, mock_seq_response):
        seq = SEQ_API.retrieve(id=1)
        assert isinstance(seq, Sequence)
        assert [0, 1] == seq.column_ids
        assert [None, "column2"] == seq.column_external_ids
        assert ["STRING", "DOUBLE"] == seq.column_value_types

    def test_retrieve_multiple(self, mock_seq_response):
        res = SEQ_API.retrieve_multiple(ids=[1])
        assert isinstance(res, SequenceList)
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)

    def test_list(self, mock_seq_response):
        res = SEQ_API.list()
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)

    def test_create_single(self, mock_seq_response):
        res = SEQ_API.create(Sequence(external_id="1", name="blabla", columns=[{}]))
        assert isinstance(res, Sequence)
        assert mock_seq_response.calls[0].response.json()["items"][0] == res.dump(camel_case=True)

    def test_create_columnid_passed(self, mock_seq_response):
        res = SEQ_API.create(Sequence(external_id="1", name="blabla", columns=[{"id": 1, "valueType": "STRING"}]))
        assert isinstance(res, Sequence)
        assert {"items": [{"name": "blabla", "externalId": "1", "columns": [{"valueType": "STRING"}]}]} == jsgz_load(
            mock_seq_response.calls[0].request.body
        )

    def test_create_multiple(self, mock_seq_response):
        res = SEQ_API.create([Sequence(external_id="1", name="blabla", columns=[{"externalId": "cid"}])])
        assert isinstance(res, SequenceList)
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)

    def test_iter_single(self, mock_seq_response):
        for asset in SEQ_API:
            assert mock_seq_response.calls[0].response.json()["items"][0] == asset.dump(camel_case=True)

    def test_iter_chunk(self, mock_seq_response):
        for assets in SEQ_API(chunk_size=1):
            assert mock_seq_response.calls[0].response.json()["items"] == assets.dump(camel_case=True)

    def test_delete_single(self, mock_seq_response):
        res = SEQ_API.delete(id=1)
        assert {"items": [{"id": 1}]} == jsgz_load(mock_seq_response.calls[0].request.body)
        assert res is None

    def test_delete_multiple(self, mock_seq_response):
        res = SEQ_API.delete(id=[1])
        assert {"items": [{"id": 1}]} == jsgz_load(mock_seq_response.calls[0].request.body)
        assert res is None

    def test_update_with_resource_class(self, mock_seq_response):
        res = SEQ_API.update(Sequence(id=1))
        assert isinstance(res, Sequence)
        assert mock_seq_response.calls[0].response.json()["items"][0] == res.dump(camel_case=True)

    def test_update_with_update_class(self, mock_seq_response):
        res = SEQ_API.update(SequenceUpdate(id=1).description.set("blabla"))
        assert isinstance(res, Sequence)
        assert mock_seq_response.calls[0].response.json()["items"][0] == res.dump(camel_case=True)

    def test_update_multiple(self, mock_seq_response):
        res = SEQ_API.update([SequenceUpdate(id=1).description.set("blabla")])
        assert isinstance(res, SequenceList)
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)

    def test_search(self, mock_seq_response):
        res = SEQ_API.search(filter=SequenceFilter(external_id_prefix="e"))
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)
        assert {
            "search": {"name": None, "description": None, "query": None},
            "filter": {"externalIdPrefix": "e"},
            "limit": None,
        } == jsgz_load(mock_seq_response.calls[0].request.body)

    @pytest.mark.parametrize("filter_field", ["is_string", "isString"])
    def test_search_dict_filter(self, mock_seq_response, filter_field):
        res = SEQ_API.search(filter={filter_field: True})
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)
        assert {
            "search": {"name": None, "description": None, "query": None},
            "filter": {"isString": True},
            "limit": None,
        } == jsgz_load(mock_seq_response.calls[0].request.body)

    def test_search_with_filter(self, mock_seq_response):
        res = SEQ_API.search(name="n", description="d", query="q", filter=SequenceFilter(last_updated_time={"max": 42}))
        assert mock_seq_response.calls[0].response.json()["items"] == res.dump(camel_case=True)
        req_body = jsgz_load(mock_seq_response.calls[0].request.body)
        assert 42 == req_body["filter"]["lastUpdatedTime"]["max"]
        assert {"name": "n", "description": "d", "query": "q"} == req_body["search"]

    def test_update_object(self):
        assert isinstance(
            SequenceUpdate(1)
            .asset_id.set(1)
            .asset_id.set(None)
            .description.set("")
            .description.set(None)
            .external_id.set("1")
            .external_id.set(None)
            .metadata.set({})
            .metadata.add({})
            .metadata.remove([])
            .name.set("")
            .name.set(None),
            SequenceUpdate,
        )

    def test_insert(self, mock_post_sequence_data):
        data = {i: [2 * i] for i in range(1, 11)}
        SEQ_API.data.insert(column_ids=[0], rows=data, external_id="eid")
        assert {
            "items": [
                {
                    "externalId": "eid",
                    "columns": [{"id": 0}],
                    "rows": [{"rowNumber": i, "values": [2 * i]} for i in range(1, 11)],
                }
            ]
        } == jsgz_load(mock_post_sequence_data.calls[0].request.body)

    def test_insert_missing_extid(self, mock_seq_response, mock_post_sequence_data):
        seq = SEQ_API.retrieve(id=1)
        with pytest.raises(ValueError):
            SEQ_API.data.insert(column_external_ids=seq.column_external_ids, rows={1: [0]}, external_id="eid")

    def test_insert_extid(self, mock_post_sequence_data):
        data = {i: [2 * i] for i in range(1, 11)}
        SEQ_API.data.insert(column_external_ids=["blah"], rows=data, external_id="eid")
        assert {
            "items": [
                {
                    "externalId": "eid",
                    "columns": [{"externalId": "blah"}],
                    "rows": [{"rowNumber": i, "values": [2 * i]} for i in range(1, 11)],
                }
            ]
        } == jsgz_load(mock_post_sequence_data.calls[0].request.body)

    def test_insert_tuple(self, mock_post_sequence_data):
        data = [(i, [2 * i]) for i in range(1, 11)]
        SEQ_API.data.insert(column_ids=[0], rows=data, external_id="eid")
        assert {
            "items": [
                {
                    "externalId": "eid",
                    "columns": [{"id": 0}],
                    "rows": [{"rowNumber": i, "values": [2 * i]} for i in range(1, 11)],
                }
            ]
        } == jsgz_load(mock_post_sequence_data.calls[0].request.body)

    def test_insert_raw(self, mock_post_sequence_data):
        data = [{"rowNumber": i, "values": [2 * i, "str"]} for i in range(1, 11)]
        SEQ_API.data.insert(column_ids=[0], rows=data, external_id="eid")
        assert {
            "items": [
                {
                    "externalId": "eid",
                    "columns": [{"id": 0}],
                    "rows": [{"rowNumber": i, "values": [2 * i, "str"]} for i in range(1, 11)],
                }
            ]
        } == jsgz_load(mock_post_sequence_data.calls[0].request.body)

    def test_retrieve_no_data(self, mock_seq_response, mock_get_sequence_empty_data):
        data = SEQ_API.data.retrieve(id=1, start=0, end=None)
        assert isinstance(data, SequenceData)
        assert 0 == len(data)
        assert 2 == len(data.column_ids)
        assert 2 == len(data.column_external_ids)

    def test_retrieve_by_id(self, mock_seq_response, mock_get_sequence_data):
        data = SEQ_API.data.retrieve(id=123, start=123, end=None)
        assert isinstance(data, SequenceData)
        assert 1 == len(data)

    def test_retrieve_by_external_id(self, mock_seq_response, mock_get_sequence_data):
        data = SEQ_API.data.retrieve(external_id="foo", start=1, end=1000)
        assert isinstance(data, SequenceData)
        assert 1 == len(data)

    def test_retrieve_missing_column_external_id(self, mock_seq_response, mock_get_sequence_data_no_extid_in_columns):
        data = SEQ_API.data.retrieve(id=123, start=123, end=None)
        assert isinstance(data, SequenceData)
        assert 1 == len(data)

    def test_delete_by_id(self, mock_delete_sequence_data):
        res = SEQ_API.data.delete(id=1, rows=[1, 2, 3])
        assert res is None
        assert {"items": [{"id": 1, "rows": [1, 2, 3]}]} == jsgz_load(mock_delete_sequence_data.calls[0].request.body)

    def test_delete_by_external_id(self, mock_delete_sequence_data):
        res = SEQ_API.data.delete(external_id="foo", rows=[1])
        assert res is None
        assert {"items": [{"externalId": "foo", "rows": [1]}]} == jsgz_load(
            mock_delete_sequence_data.calls[0].request.body
        )

    def test_retrieve_rows(self, mock_seq_response, mock_get_sequence_data):
        seq = SEQ_API.retrieve(id=1)
        data = seq.rows(start=0, end=None)
        assert isinstance(data, SequenceData)
        assert 1 == len(data)

    def test_rows_helper_functions(self, mock_seq_response, mock_get_sequence_data):
        seq = SEQ_API.retrieve(id=1)
        data = seq.rows(start=0, end=None)
        assert [1] == data[0]
        for r, v in data.items():
            assert 0 == r
            assert [1] == v
        col = data.get_column("ceid")
        assert isinstance(col, list)
        assert 1 == len(col)
        with pytest.raises(TypeError):
            sliced = data[1:23]
        with pytest.raises(ValueError):
            missingcol = data.get_column("doesnotexist")

    def test_sequence_builtins(self, mock_seq_response):
        r1 = SEQ_API.retrieve(id=0)
        r2 = SEQ_API.retrieve(id=0)
        assert r1 == r2
        assert r1.__eq__(r2)
        assert str(r1) == str(r2)
        assert mock_seq_response.calls[0].response.json()["items"][0] == r1.dump(camel_case=True)

    def test_sequence_data_builtins(self, mock_seq_response, mock_get_sequence_data):
        r1 = SEQ_API.data.retrieve(id=0, start=0, end=None)
        r2 = SEQ_API.data.retrieve(id=0, start=0, end=None)
        assert r1 == r2
        assert r1.__eq__(r2)
        assert str(r1) == str(r2)
        assert r1.dump() == r2.dump()
        list_request = [call for call in mock_get_sequence_data.calls if "/data/list" in call.request.url][0]
        response = list_request.response.json()["items"][0]
        data_dump = r1.dump(camel_case=True)
        print(response)
        for f in ["columns", "rows", "id"]:
            assert response[f] == data_dump[f]


@pytest.mark.dsl
class TestSequencesPandasIntegration:
    def test_retrieve_dataframe(self, mock_seq_response, mock_get_sequence_data):
        df = SEQ_API.data.retrieve_dataframe(external_id="foo", start=1000000, end=1100000)
        assert {"ceid"} == set(df.columns)
        assert df.shape[0] > 0
        assert df.index == [0]

    def test_retrieve_dataframe_columns_mixed(self, mock_seq_response, mock_get_sequence_data_no_extid_in_columns):
        data = SEQ_API.data.retrieve(external_id="foo", start=1000000, end=1100000)
        assert isinstance(data, SequenceData)
        assert [0, 1] == list(data.to_pandas().columns)
        assert [0, 1] == list(data.to_pandas(column_names="id").columns)
        assert [None, "col2"] == list(data.to_pandas(column_names="externalId").columns)
        with pytest.raises(ValueError):
            data.to_pandas(column_names="badvalue")

    def test_retrieve_dataframe_columns_many_extid(self, mock_get_sequence_data_many_columns):
        data = SEQ_API.data.retrieve(external_id="foo", start=1000000, end=1100000)
        assert isinstance(data, SequenceData)
        print(data.to_pandas())
        assert ["ceid" + str(i) for i in range(200)] == list(data.to_pandas().columns)
        assert ["ceid" + str(i) for i in range(200)] == list(data.to_pandas(column_names="externalId").columns)
        assert list(range(200)) == list(data.to_pandas(column_names="id").columns)

    def test_retrieve_dataframe_convert_null(self, mock_seq_response, mock_get_sequence_data_with_null):
        df = SEQ_API.data.retrieve_dataframe(external_id="foo", start=0, end=None)
        assert {"strcol", "intcol"} == set(df.columns)
        assert "None" not in df.strcol
        assert df.strcol.isna().any()
        assert df.intcol.isna().any()
        assert 2 == df.shape[0]

    def test_retrieve_empty_dataframe(self, mock_seq_response, mock_get_sequence_empty_data):
        import pandas as pd

        df = SEQ_API.data.retrieve_dataframe(id=1, start=0, end=None)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert 2 == len(df.columns)

    def test_sequences_list_to_pandas(self, mock_seq_response):
        import pandas as pd

        df = SEQ_API.list().to_pandas()
        assert isinstance(df, pd.DataFrame)
        assert 1 == df.shape[0]
        assert {"metadata-key": "metadata-value"} == df["metadata"][0]

    def test_sequences_list_to_pandas_empty(self, mock_sequences_empty):
        import pandas as pd

        df = SEQ_API.list().to_pandas()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_sequencess_to_pandas(self, mock_seq_response):
        import pandas as pd

        df = SEQ_API.retrieve(id=1).to_pandas()
        assert isinstance(df, pd.DataFrame)
        assert "metadata" not in df.columns
        assert "string" == df.loc["description"][0]
        assert "metadata-value" == df.loc["metadata-key"][0]

    def test_insert_dataframe_ids(self, mock_post_sequence_data):
        import pandas as pd

        df = pd.DataFrame(index=[123, 456])
        df[3] = [1, 2]
        df[4] = [5.0, 6.0]
        res = SEQ_API.data.insert_dataframe(df, id=42)
        assert res is None
        request_body = jsgz_load(mock_post_sequence_data.calls[0].request.body)
        assert {
            "items": [
                {
                    "id": 42,
                    "columns": [{"id": 3}, {"id": 4}],
                    "rows": [{"rowNumber": 123, "values": [1, 5.0]}, {"rowNumber": 456, "values": [2, 6.0]}],
                }
            ]
        } == request_body

    def test_insert_dataframe_extids(self, mock_post_sequence_data):
        import pandas as pd

        df = pd.DataFrame(index=[123, 456])
        df["aa"] = [1, 2]
        df["bb"] = [5.0, 6.0]
        res = SEQ_API.data.insert_dataframe(df, id=42, external_id_headers=True)
        assert res is None
        request_body = jsgz_load(mock_post_sequence_data.calls[0].request.body)
        assert {
            "items": [
                {
                    "id": 42,
                    "columns": [{"externalId": "aa"}, {"externalId": "bb"}],
                    "rows": [{"rowNumber": 123, "values": [1, 5.0]}, {"rowNumber": 456, "values": [2, 6.0]}],
                }
            ]
        } == request_body