from folderbox.file_ops import copy_items, create_folder, move_items, rename_item


def test_copy_file_and_generate_non_conflicting_name(tmp_path) -> None:
    source_dir = tmp_path / "source"
    destination = tmp_path / "destination"
    source_dir.mkdir()
    destination.mkdir()
    source = source_dir / "example.txt"
    source.write_text("folderbox", encoding="utf-8")

    first_copied, first_failures = copy_items([source], destination)
    second_copied, second_failures = copy_items([source], destination)

    assert first_failures == []
    assert second_failures == []
    assert first_copied == [destination / "example.txt"]
    assert second_copied == [destination / "example - 副本.txt"]
    assert second_copied[0].read_text(encoding="utf-8") == "folderbox"


def test_prevents_copying_directory_into_its_descendant(tmp_path) -> None:
    source = tmp_path / "source"
    child = source / "child"
    child.mkdir(parents=True)

    copied, failures = copy_items([source], child)

    assert copied == []
    assert len(failures) == 1
    assert failures[0][0] == source


def test_rename_item(tmp_path) -> None:
    source = tmp_path / "before.txt"
    source.write_text("content", encoding="utf-8")

    target = rename_item(source, "after.txt")

    assert target == tmp_path / "after.txt"
    assert target.exists()
    assert not source.exists()



def test_move_file(tmp_path) -> None:
    source_dir = tmp_path / "source"
    destination = tmp_path / "destination"
    source_dir.mkdir()
    destination.mkdir()
    source = source_dir / "move.txt"
    source.write_text("move me", encoding="utf-8")

    moved, failures = move_items([source], destination)

    assert failures == []
    assert moved == [destination / "move.txt"]
    assert moved[0].read_text(encoding="utf-8") == "move me"
    assert not source.exists()


def test_move_directory_into_same_folder_is_noop(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    moved, failures = move_items([source], tmp_path)

    assert failures == []
    assert moved == [source]
    assert source.exists()


def test_create_folder(tmp_path) -> None:
    created = create_folder(tmp_path, "Research")

    assert created == tmp_path / "Research"
    assert created.is_dir()
