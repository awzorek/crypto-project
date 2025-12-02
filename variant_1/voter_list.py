from Crypto.PublicKey import RSA
from Crypto import Random

import json

class VoterList:
    __list = {}

    def __init__(self):
        self.__list.clear()
        self.read()
    
    def generate(self, num : int):
        self.__list.clear()
        # 0 - registration server
        # 1 - ballot box server
        # 2 - root
        # 3-... - voters
        for i in range(num):
            key = RSA.generate(2048)
            # everytime e is 65537, can be set different in RSA.generate
            if i == 0: name = 'Registration Server'
            elif i == 1: name = 'Ballot Box Server'
            elif i == 2: name = 'Root'
            else: name = f"voter{i}"

            self.__list[i] = {
                'name' : name,
                'n' : key.n,
                'e' : key.e,
                'd' : key.d
            }
    
    def save(self):
        string = json.dumps(self.__list)
        with open('keys', 'w') as f:
            f.write(string)
    
    def read(self):
        with open('keys') as f:
            string = f.read()
            self.__list = json.loads(string)
    
    def get_private_key(self, i):
        d = self.__list[str(i)]
        return {
            'name': d['name'],
            'public_key': RSA.construct((d['n'], d['e'])),
            'private_key': RSA.construct((d['n'], d['e'], d['d'])),
        }

    def get_public_keys(self):
        keys = self.__list.keys()
        c = {}
        for k in keys:
            c[k] = {
                'name': self.__list[k]['name'],
                'public_key': RSA.construct((self.__list[k]['n'], self.__list[k]['e'])),
            }
        return c

    def length(self):
        return len(self.__list)