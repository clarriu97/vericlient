import io
import json
import tarfile

from vericlient.vcsp.batch import APPLICANTS_FILE, build_batch_archive, sample_filename


def test_archive_holds_the_samples_and_an_applicants_file():
    entries = [
        ("one.wav", b"first-sample", {"subject_id": "a"}),
        ("two.wav", b"second-sample", {"subject_id": "b"}),
    ]

    archive = build_batch_archive(entries)

    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        names = tar.getnames()
        assert sorted(names) == sorted(["one.wav", "two.wav", APPLICANTS_FILE])
        assert tar.extractfile("one.wav").read() == b"first-sample"
        applicants = json.loads(tar.extractfile(APPLICANTS_FILE).read())

    # The `file://` scheme is the only one the service accepts; anything else is rejected
    # with "'<scheme>' is not a valid scheme".
    assert [a["sample"] for a in applicants] == ["file://one.wav", "file://two.wav"]
    assert [a["applicant"] for a in applicants] == [{"subject_id": "a"}, {"subject_id": "b"}]


def test_sample_filename_prefers_what_the_caller_gave():
    assert sample_filename("/data/audio.wav", 0, "explicit.wav") == "explicit.wav"


def test_sample_filename_falls_back_to_the_path():
    assert sample_filename("/data/nested/audio.wav", 0, None) == "audio.wav"


def test_sample_filename_generates_one_for_bytes():
    assert sample_filename(b"raw", 3, None) == "sample_3"
