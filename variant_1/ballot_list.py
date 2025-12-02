from tools import aes_decrypt

class BallotList:
    __list = {}

    def __init__(self):
        self.__list.clear()

    def append_m_BS(self, m_BS : str):
        i = len(self.__list)
        self.__list[i] = {
            'm_BS' : m_BS,
            'BS' : ''
        }
        return i
    
    def add_key(self, i : int, key : bytes):
        m_BS = self.__list[i]['m_BS']
        self.__list[i]['BS'] = aes_decrypt(m_BS, key).decode()
    
    def get_list(self):
        return self.__list
    
    def check_if_published(self, i, m_BS):
        return self.__list[i]['m_BS'] == m_BS