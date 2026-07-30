import os


def test_outputs():
    outputs = [
        "/app/output/text_files.tar.gz",
        "/app/output/image_files.tar.gz",
        "/app/output/data_files.tar.gz"
    ]
    for filepath in outputs:
        assert os.path.exists(filepath), f"Missing expected output: {filepath}"
