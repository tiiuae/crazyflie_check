import asyncio
import qtm
import colorama
import time
import sys
import time

import xml.etree.cElementTree as ET

def check_qtm():
    asyncio.ensure_future(setup())
    asyncio.get_event_loop().run_forever()

labels = []
last_update = 0
did_print = False

def on_packet(packet):
    global last_update, did_print
    """ Callback function that is called everytime a data packet arrives from QTM """
    #print("Framenumber: {}".format(packet.framenumber))
    header, bodies = packet.get_6d()
    #print("Component info: {}".format(header))
    now = round(time.time() * 1000)
    if now - last_update < 500:
        return
    if bodies is None:
        print("No bodies!")
    else:
        if did_print:
            for i in range(len(labels)+1):
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
        
        did_print = True

        print("====== Visible Drones ======")
        for rigid in labels:
            index = labels.index(rigid)
            body = bodies[index]
            x = str(round(body[0][0] / 1000, 3))
            y = str(round(body[0][1] / 1000, 3))
            z = str(round(body[0][2] / 1000, 3))
            print(colorama.Fore.CYAN + "(" + colorama.Fore.YELLOW + rigid + colorama.Fore.CYAN + ")\t" + colorama.Fore.WHITE
                    + x + ", " + y + ", " + z)
    last_update = now




async def setup():
    global labels
    """ Main function """
    connection = await qtm.connect(host="192.168.254.1", version="1.20", timeout=5)
    if connection is None:
        print("Connection failed")
        return
    
    params = await connection.get_parameters(parameters=["6d"])
    xml = ET.fromstring(params)
    labels = [label.text for label in xml.iter('Name')]
    print(labels)
    await connection.stream_frames(components=["6d"], on_packet=on_packet)


