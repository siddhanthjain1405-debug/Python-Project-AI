import pytest

from memory_agent.memory import MemoryStoreError, collection_name_for


def test_add_and_count(store):
    store.add("My name is Ayush")
    assert store.count() == 1


def test_add_rejects_empty_and_too_long(store):
    with pytest.raises(MemoryStoreError):
        store.add("   ")
    with pytest.raises(MemoryStoreError):
        store.add("x" * 5000)


def test_ids_stay_unique_after_deletion(store):
    first = store.add("one")
    store.add("two")
    store.delete(first)
    store.add("three")  # original msg_{count+1} scheme would collide here
    assert store.count() == 2


def test_search_with_fewer_items_than_k(store):
    store.add("I like chess")
    assert store.search("chess", k=5) == ["I like chess"]


def test_search_empty_store_and_blank_query(store):
    assert store.search("anything") == []
    store.add("hello")
    assert store.search("   ") == []


def test_search_ranks_relevant_first(store):
    store.add("I live in Delhi")
    store.add("My favourite colour is blue")
    assert store.search("what colour do I like blue", k=1) == ["My favourite colour is blue"]


def test_list_items_newest_first_and_legacy_rows(store):
    store._collection.rows["msg_1"] = ("legacy memory", None)  # saved by the old version
    store.add("new memory")
    items = store.list_items()
    assert items[0].text == "new memory"
    assert items[-1].id == "msg_1" and items[-1].created_at == ""


def test_clear_and_export(store):
    store.add("a")
    store.add("b")
    assert '"text": "a"' in store.export_json()
    assert store.clear() == 2
    assert store.count() == 0
    assert store.clear() == 0


def test_collection_name_mapping():
    assert collection_name_for("default") == "personal_memory"
    assert collection_name_for("") == "personal_memory"
    assert collection_name_for("Ayush V!!") == "mem-ayush-v"
    name = collection_name_for("x" * 200)
    assert 3 <= len(name) <= 63
