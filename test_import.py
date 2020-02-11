from minervalib.importer import MinervaImporter
from test.mocks import MinervaMockClient, MockS3Uploader

def test_import():
    importer = MinervaImporter(MinervaMockClient(), MockS3Uploader())
    importer.import_files(files=["/foo/image1.tif", "/foo/image2.rcpnl"])