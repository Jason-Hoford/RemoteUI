"""Atomic demo for the Image component. Port of DemoImage.kt."""
import sys, os, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000

# 100x100 ARGB_8888 PNG of a red filled circle at (50,50) r=40
# Extracted from the Kotlin-generated reference to ensure byte-identical output.
_CIRCLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABHNCSVQICAgIfAhkiAAAAAFzUkdC"
    "AK7OHOkAAATESURBVHic7Z1diJVFGMd/o+SdhuTCaiVbSB9mHxT0sRlrd0FgeyURRYXdJ3TRdUQg"
    "VndedhkURaQZXRVuqJgafViRJ8pEWxXypoINl7V/F3MEkz3tOzPve2bO+z4/eNiz8D5z5vz/Z2bO"
    "OfPxgmEYhmEYhmEYhmEY5eByV6AKglXAg8A6YBxY24/xK/4CnAfO9ePKx+eALxz8OdyatwjBBsEO"
    "wWeCeYESY17wqeBFwYbcr694BMsFWwRvCno1GLBU9ARvCKYEy3O//mIQLBM8Kzg1BBMGxa+CpwXL"
    "cuuRFcFWwXcZjbg6jgsez63L0BE8IDhcgAGD4qBgMrdOjSPYKNhXgOBV4yPBpty6NYLgGcFCASKH"
    "xoLg+dz61YbACV4tQNjUeEUj8r1tIIJrBB8UIGZd8Z5gRW5doxBcJzhQgIh1x4xgTW59gxDcJPil"
    "APGaip8FNzehXe19omAl8CVwS91lF0YPuL/u38dq/WYqb/D7tN8MgFuBd1XyQC/YWUB3MuzYmVv3"
    "RRFsL0CcXLEtt/7/QTCpen4iH9WYEzxch5bJ/Z/gBuArYCy9OiPN78C9Dn5LKaSOQX03ZgZ4DXan"
    "FpLUQvrN9GBqJVrG3Q6OxyantpDXEvPbyK6U5OgWItgC7E958hbzqIOZmMQUQw4Am2PzW87nzr9h"
    "g4nqsgTTmBn/x5TgsZjEqBYiP2jdGZPbIb51cE9oUrAh8k/ydWheR7ndwYmQhJguK6opdpTp0IQY"
    "Q4KfpMMEaxXUZcmvoT0bmtdhBFzv/NriSoS2kGnMjBAc8ERIQowhRhhBmlV+t8tPzV5gVFdd5GMe"
    "GKs61RvSQu7AzIhhBbCx6sUhhowvfYkxgMrahRgyEV4Po89E1QuthQyHRlqIGRKPdVmFYS2kMMyQ"
    "wpioemG3NzkWSIgh5xurRfuprJ0ZMhzMkMIwQwrDDCkMM6QwzJDCOFX1wpAJqrXAbEiOAfgJqjUO"
    "/qpyceUW0p+oPxpbqw6zv6oZEP5NfU/g9UagZqHLgG4DfgyqTrcRsM41NKjTXxbZC61VhzkaYgbE"
    "/bho3VZ1grUyQ5olWKvY7Qiz+CNbjcH0nB9zg4idD9kemdcldsQkpWxpmwGmYvNbTvSWthRDbEv0"
    "YCYdHI5JjJ7CdXAI2Bub32L2xpoB6QcHbAK+wU6Gvswl/MEBP8QWkLTIwcH3wNspZbSMt1LMgHoO"
    "nxnDnyC3PrWsEecM/vCZCymFJC8Dcv4UnGlgLrWsEeZvYGuqGVDTuiznt0m/UEdZI8pzzo+lZSE7"
    "4q8s5E+x/rgAkYYVn6jmGdQmjoldBRwh4necEaORY2IbmR+XP0L1CHBtE+UXwB94M37KXZHKCFYK"
    "9hTQrdQd++R3JI8e/TGlTQP963WPGVkQPCW4WICgsTGn0s7mTUXwkGC2AHFD46zgrtz6NYJgtfyt"
    "6kahtVyUv4Xf6ty6NY5gQvBhAaIvFv8I3lEXN7nKH1F+rAATLscxwX25dcmK/CexbYKTGY04KXhS"
    "bfgEVRfyt17dLNglODEEE3ryH2MfkU2wLY38zYlfFhwSXKrBgAX5+0e9pIJvTjwSTVT+iKP1wI39"
    "WOwx+Emi0/2/Z676/7TzWwMMwzAMwzAMwzAMwzAq8i+SMdZzITqiqwAAAABJRU5ErkJggg=="
)


def demo_image():
    ctx = RcContext(400, 400)
    with ctx.root():
        image_id = ctx.add_bitmap_data(100, 100, _CIRCLE_PNG)
        ctx.image(Modifier().size(200).background(LTGRAY), image_id, 1, 1.0)
    return ctx


if __name__ == '__main__':
    ctx = demo_image()
    data = ctx.encode()
    print(f"DemoImage: {len(data)} bytes")
    ctx.save("demo_image.rc")
    print("Saved demo_image.rc")
