#!/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import json
import tornado.httpserver
from tornado.ioloop import PeriodicCallback
import tornado.web
import tornado.websocket
import tornado.escape
import copy
from tornado.web import url
import base64
from datetime import datetime
import requests

class Map():
    name = "item_none"
    map_icons = list()
    map_texts = list()

    def __init__(self, name, map_icons, map_texts):
        self.name = name
        self.map_icons = copy.deepcopy(map_icons)
        self.map_texts = copy.deepcopy(map_texts)

class MapIconItem():
    type = ""
    x = 0
    y = 0

    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y

class MapTextItem():
    text = ""
    size = 0
    color = 0
    bg_color = 0
    x = 0
    y = 0

    def __init__(self, text, size, color, bg_color, x, y):
        self.text = text
        self.size = size
        self.color = color
        self.bg_color = bg_color
        self.x = x
        self.y = y

class Client():
    WSHandler = None
    map_name = None

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class WSHandler(tornado.websocket.WebSocketHandler):
    TAG_REPORT_MAP_ICON = "report_map_icon"
    TAG_REPORT_MAP_TEXT = "report_map_text"
    TAG_REPORT_MAP = "report_map"
    TAG_REPORT_CLEAR_MAP = "report_clear_map"
    TAG_REPORT_REMOVE_MAP_ICON = "report_remove_map_icon"
    TAG_REPORT_REMOVE_MAP_TEXT = "report_remove_map_text"
    TAG_REPORT_SEND_MAP_IMAGE = "report_send_map_image"
    TAG_NOTIFY_REMOVE_MAP_ICON = "notify_remove_map_icon"
    TAG_NOTIFY_REMOVE_MAP_TEXT = "notify_remove_map_text"
    TAG_NOTIFY_MAP_ICON = "notify_map_icon"
    TAG_NOTIFY_MAP_TEXT = "notify_map_text"
    TAG_NOTIFY_MAP = "notify_map" 
 
    clients = list()
    maps = (Map("item_fort_all", list(), list()), Map("item_fort_center", list(), list()), Map("item_fort_all_2", list(), list()))
 
    def __init__(self, application, request, **kwargs):    
        super(WSHandler, self).__init__(application, request, **kwargs)        

    def open(self):
        client = Client()
        client.WSHandler = self
        client.map_name = "item_none"
        WSHandler.clients.append(client)
        print("WebSocket opened")

    def getMyClient(self):
        for client in WSHandler.clients:
            if self is client.WSHandler:
                return client

    def on_message(self, message):
        my_client = self.getMyClient()        
        delimiter_pos = message.find(",")
        if (delimiter_pos != -1):
            tag = message[0:delimiter_pos]
            payload = message[delimiter_pos + 1:]
        else:
            tag = message
            payload = ""

        self.write_message("echo:" + tag)
        
        if tag == WSHandler.TAG_REPORT_MAP:
            # Change map
            self.notifyRemoveAllMapIcon()
            my_client.map_name = copy.deepcopy(payload)
            
            self.notifyMap(my_client.map_name)
            self.notifyInformation()        
        elif tag == WSHandler.TAG_REPORT_MAP_ICON:
            client_map_name = my_client.map_name
            delimiter_pos = payload.find(",")
            type = payload[0:delimiter_pos]
            payload2 = payload[delimiter_pos + 1:]
            delimiter_pos = payload2.find(",")
            x = payload2[0:delimiter_pos]
            payload3 = payload2[delimiter_pos + 1:]
            y = payload3

            # Put icon
            map_icon = MapIconItem(type, x, y) 
            for map in WSHandler.maps:
                if map.name == client_map_name:
                    map.map_icons.append(map_icon)

            self.notifyNewMapIconMapMembers(map_icon, client_map_name)
        elif tag == WSHandler.TAG_REPORT_REMOVE_MAP_ICON:
            client_map_name = my_client.map_name
            # Remove icon
            for map in WSHandler.maps:
                if map.name == client_map_name:
                    for map_icon in map.map_icons:
                        if id(map_icon) == payload:
                            map.map_icons.remove(map_icon)
            self.notifyRemoveMapIconMapMembers(payload, client_map_name)
        elif tag == WSHandler.TAG_REPORT_REMOVE_MAP_TEXT:
            client_map_name = my_client.map_name
            # Remove text
            for map in WSHandler.maps:
                if map.name == client_map_name:
                    for map_text in map.map_texts:
                        if id(map_text) == payload:
                            map.map_texts.remove(map_text)
            self.notifyRemoveMapTextMapMembers(payload, client_map_name)
        elif tag == WSHandler.TAG_REPORT_CLEAR_MAP:
            client_map_name = my_client.map_name
            self.notifyRemoveAllMapIconMapMembers(client_map_name)
            # Remove all icons
            for map in WSHandler.maps:
                if map.name == client_map_name:
                    for map_icon in map.map_icons:
                        map.map_icons.remove(map_icon)
                    for map_text in map.map_texts:
                        map.map_texts.remove(map_text)
        elif tag == WSHandler.TAG_REPORT_MAP_TEXT:    # tag_report_map_text:str,x,y
            client_map_name = my_client.map_name
            delimiter_pos = payload.find(",")
            text = payload[0:delimiter_pos]
            payload2 = payload[delimiter_pos + 1:]
            delimiter_pos = payload2.find(",")
            size = payload2[0:delimiter_pos]
            payload3 = payload2[delimiter_pos + 1:]
            delimiter_pos = payload3.find(",")
            color = payload3[0:delimiter_pos]
            payload4 = payload3[delimiter_pos + 1:]
            delimiter_pos = payload4.find(",")
            bg_color = payload4[0:delimiter_pos]
            payload5 = payload4[delimiter_pos + 1:]
            delimiter_pos = payload5.find(",")
            x = payload5[0:delimiter_pos]
            payload6 = payload5[delimiter_pos + 1:]
            y = payload6
            # Put text
            map_text = MapTextItem(text, size, color, bg_color, x, y) 
            for map in WSHandler.maps:
                if map.name == client_map_name:
                    map.map_texts.append(map_text)
            self.notifyNewMapTextMapMembers(map_text, client_map_name)
        elif tag == WSHandler.TAG_REPORT_SEND_MAP_IMAGE:    # tag_report_send_map_image:dataURL
            delimiter_pos = payload.find(",")
            type = payload[0:delimiter_pos]
            payload2 = payload[delimiter_pos + 1:]
            delimiter_pos = payload2.find(",")
            size = payload2[0:delimiter_pos]
            payload3 = payload2[delimiter_pos + 1:]
            today = datetime.today()
            time_str = ('%04d' % today.year) + ('%02d' % today.month) + ('%02d' % today.day) + ('%02d' % today.hour) + ('%02d' % today.minute) + ('%02d' % today.second) + ('%08d' % today.microsecond)
            filename = 'map_image_' + time_str + '.png'
            dirname = 'static/upload/'
            f = open(dirname + filename, 'wb')
            f.write(base64.b64decode(payload2))
            f.close()
            img_url = 'http://tk2-233-26477.vs.sakura.ne.jp:8888/static/upload/' + filename
            webhook_url = base64.b64decode(payload3)
            session = requests.session()
            params = {'content' : img_url}
            request = session.post(webhook_url, data=params)

    def on_close(self):
        for client in WSHandler.clients:
            if self is client.WSHandler:
                WSHandler.clients.remove(client)
        print("WebSocket closed")

    def dumpMaps():
        print("dumpMaps Start")
        print("WSHandler.maps:" + str(id(WSHandler.maps)))
        for map in WSHandler.maps:
            print(map.name + ":" + str(id(map)))
            for map_icon in map.map_icons:
                print(map_icon.type)

            for map_text in map.map_texts:
                print(map_text.text)
        print("dumpMaps End")

    def sendMapMembers(self, message, map_name):
        if len(WSHandler.clients) == 0:
            return
        for client in WSHandler.clients:
            if client.map_name == map_name:
                client.WSHandler.write_message(message)


    def notifyRemoveAllMapIcon(self):
        my_client = self.getMyClient()        
        client_map_name = my_client.map_name
        for map in WSHandler.maps:
            if map.name == client_map_name:
                for map_icon in map.map_icons:
                    self.write_message(WSHandler.TAG_NOTIFY_REMOVE_MAP_ICON + "," + str(id(map_icon)))

                for map_text in map.map_texts:
                    self.write_message(WSHandler.TAG_NOTIFY_REMOVE_MAP_TEXT + "," + str(id(map_text)))
    def notifyMap(self, map_name):
        self.write_message(WSHandler.TAG_NOTIFY_MAP + "," + map_name)

    def notifyInformation(self):
        my_client = self.getMyClient()        
        client_map_name = my_client.map_name
        WSHandler.dumpMaps()
        for map in WSHandler.maps:
            if map.name == client_map_name:
                for map_icon in map.map_icons:
                    self.write_message(WSHandler.TAG_NOTIFY_MAP_ICON + "," + str(id(map_icon)) + "," + map_icon.type + "," + str(map_icon.x) + "," + str(map_icon.y))
                for map_text in map.map_texts:
                    self.write_message(WSHandler.TAG_NOTIFY_MAP_TEXT + "," + str(id(map_text)) + "," + map_text.text + "," + map_text.size + "," + map_text.color + "," + map_text.bg_color + "," + str(map_text.x) + "," + str(map_text.y))
    def notifyNewMapIconMapMembers(self, map_icon, map_name):
        self.sendMapMembers(WSHandler.TAG_NOTIFY_MAP_ICON + "," + str(id(map_icon)) + "," + map_icon.type + "," + str(map_icon.x) + "," + str(map_icon.y), map_name)

    def notifyNewMapTextMapMembers(self, map_text, map_name):
        # notify_map_text:id,text,size,color,bg_color,x,y
        self.sendMapMembers(WSHandler.TAG_NOTIFY_MAP_TEXT + "," + str(id(map_text)) + "," + map_text.text + "," + map_text.size + "," + map_text.color + "," + map_text.bg_color + "," + str(map_text.x) + "," + str(map_text.y), map_name)

    def notifyRemoveMapIconMapMembers(self, id, map_name):
        self.sendMapMembers(WSHandler.TAG_NOTIFY_REMOVE_MAP_ICON + "," + id, map_name)

    def notifyRemoveMapTextMapMembers(self, id, map_name):
        self.sendMapMembers(WSHandler.TAG_NOTIFY_REMOVE_MAP_TEXT + "," + id, map_name)
    
    def notifyRemoveAllMapIconMapMembers(self, client_map_name):
        for map in WSHandler.maps:
            if map.name == client_map_name:
                for map_icon in map.map_icons:
                    self.sendMapMembers(WSHandler.TAG_NOTIFY_REMOVE_MAP_ICON + "," + str(id(map_icon)), client_map_name)
                for map_text in map.map_texts:
                    self.sendMapMembers(WSHandler.TAG_NOTIFY_REMOVE_MAP_TEXT + "," + str(id(map_text)), client_map_name)

application = tornado.web.Application([
    (r"/blackspinel/pocketarena/index", MainHandler),
    (r"/blackspinel/pocketarena/ws", WSHandler),
    ],
    template_path=os.path.join(os.getcwd(),  "templates"),
    static_path=os.path.join(os.getcwd(),  "static"),
)

if __name__ == "__main__":
    application.listen(8888)
    print("Server is up ...")
    tornado.ioloop.IOLoop.instance().start()

