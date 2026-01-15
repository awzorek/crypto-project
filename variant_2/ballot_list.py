from tools import verify_blind_signature

class BallotList:
    __list = {}

    def __init__(self):
        self.__list.clear()

    def append(self, BS : str, signed_t, hash_t) -> int:
        i = len(self.__list)
        self.__list[i] = {
            'BS' : BS,
            't' : hash_t,
            'signed_t' : signed_t,
        }
        return i
    
    def get_list(self):
        return self.__list
    
    def check_if_published(self, BS, hash_t, reg_serv_pub_key):
        for e in self.__list.values():
            if e['BS'] == BS and e['t'] == hash_t:
                return verify_blind_signature(e['signed_t'], e['t'], reg_serv_pub_key)
        return False
    
    def check_if_voted(self, hash_t, signed_t):
        for e in self.__list.values():
            if e['t'] == hash_t and e['signed_t'] == signed_t:
                return True
        return False