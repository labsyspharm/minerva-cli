from minervalib.importer import MinervaImporter
from test.mocks import MinervaMockClient, MockS3Uploader
from minervalib.fileutils import FileUtils

def test_import():
    importer = MinervaImporter(MinervaMockClient(), MockS3Uploader())
    importer.import_files(files=["/foo/image1.tif", "/foo/image2.rcpnl"])

def test_key():
    win_filename = "C:\\project1\\images\\test.rcpnl"
    key = FileUtils.get_key(win_filename)
    assert key == "/project1/images/test.rcpnl"

    unix_filename = "/home/user/project1/images/test.rcpnl"
    key = FileUtils.get_key(unix_filename)
    assert key == "/home/user/project1/images/test.rcpnl"

