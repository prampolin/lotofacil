import urllib.request
import ssl

url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        print("Status:", response.status)
        print("Data:", response.read(200))
except Exception as e:
    print("Error:", e)
