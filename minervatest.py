from minervalib.importer import MinervaImporter, TileData
from minervalib.client import MinervaClient
from minervalib.s3 import S3Uploader
from minervalib.fileutils import FileUtils
import io, sys, re
import logging

root = logging.getLogger()
logging_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging_level, format=FORMAT)

Region = "us-east-1"
Username = "juha_ruokonen@hms.harvard.edu"
Password = "Foobarz123!"
Endpoint = "https://3v21j4dh1d.execute-api.us-east-1.amazonaws.com/dev"
client_id = "cvuuuuogh6nmqm8491iiu1lh5"

client = MinervaClient(endpoint=Endpoint, region=Region, cognito_client_id=client_id)
client.authenticate(Username, Password)

imp = MinervaImporter(client, uploader=S3Uploader(region="us-east-1"))

files = ["C0-T0-Z0-L0-Y0-X0.png","C0-T0-Z0-L0-Y1-X0.png","C0-T0-Z0-L0-Y0-X1.png","C0-T0-Z0-L0-Y1-X1.png","C0-T0-Z0-L1-Y0-X0.png"]
directory = './grayscale/'
x = 0
print(files)

image_uuid = imp.create_image("directtest")

for filename in files:
    with open(directory + filename, 'rb') as file:
        data = io.BytesIO(file.read())
        level = re.search("L(\\d+)", filename).group(1)
        x = re.search("X(\\d+)", filename).group(1)
        y = re.search("Y(\\d+)", filename).group(1)
        tile_data = TileData(data, 0, 0, 0, int(level), int(y), int(x))
        imp.direct_import(tile_data, image_uuid, async_upload=True)

imp.wait_upload()



