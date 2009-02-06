import time
import socket
import xmlrpclib

import re

class RPCGateway(object):
    def __init__(self, host, port, protocol):
        self.protocol = protocol
        self.host = host
        self.port = port

    def get_url(self):

        """Get the url
        """
        return "%s://%s:%s/"%(self.protocol, self.host, self.port)

    def listdb(self):
        """Get the list of databases.
        """
        pass

    def login(self, db, user, password):
        pass

    def execute(self, obj, method, *args):
        pass



class RPCSession(object):
    def __init__(self,url):

        m = re.match('^(http[s]?://|socket://)([\w.\-]+):(\d{1,5})$', url or '')

        self.host = m.group(2)
        self.port = m.group(3)
        self.protocol = m.group(1)
        if not m:
            return -1
        if self.protocol == 'http://' or self.protocol == 'http://':
            self.gateway = XMLRPCGateway(self.host, self.port, 'http')
        elif self.protocol == 'socket://':
            self.gateway = NETRPCGateway(self.host, self.port)

    def listdb(self):
        return self.gateway.listdb()

    def login(self, db, user, password):

        if password is None:
            return -1

        uid = self.gateway.login(db, user or '', password or '')

        if uid <= 0:
            return -1

        self.uid = uid
        self.db = db
        self.password = password
        self.open = True
        return uid


    def execute(self, obj, method, *args):
        try:
            result = self.gateway.execute(obj, method, *args)
            return self.__convert(result)
        except Exception,e:
          import traceback,sys
          info = reduce(lambda x, y: x+y, traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))

    def __convert(self, result):

        if isinstance(result, basestring):
            # try to convert into unicode string
            try:
                return ustr(result)
            except Exception, e:
                return result

        elif isinstance(result, list):
            return [self.__convert(val) for val in result]

        elif isinstance(result, tuple):
            return tuple([self.__convert(val) for val in result])

        elif isinstance(result, dict):
            newres = {}
            for key, val in result.items():
                newres[key] = self.__convert(val)

            return newres

        else:
            return result

class XMLRPCGateway(RPCGateway):
    """XML-RPC implementation.
    """
    def __init__(self, host, port, protocol='http'):

        super(XMLRPCGateway, self).__init__(host, port, protocol)
        self.url =  self.get_url() + 'xmlrpc/'

    def listdb(self):

        sock = xmlrpclib.ServerProxy(self.url + 'db')
        try:
            return sock.list()
        except Exception, e:
            return -1

    def login(self, db, user, password):
        sock = xmlrpclib.ServerProxy(self.url + 'common')
        try:
            res = sock.login(db, user, password)
        except Exception, e:
            return -1

        return res

    def execute(self, sDatabase,UID,sPassword,obj, method, *args):
        sock = xmlrpclib.ServerProxy(self.url + 'object')
        return sock.execute(sDatabase,UID,sPassword, obj ,method,*args)



class NETRPCGateway(RPCGateway):
    def __init__(self, host, port):

        super(NETRPCGateway, self).__init__(host, port, 'socket')

    def listdb(self):
        sock = mysocket()
        try:
            sock.connect(self.host, self.port)
            sock.mysend(('db', 'list'))
            res = sock.myreceive()
            sock.disconnect()
            return res
        except Exception, e:
            return -1

    def login(self, db, user, password):
        sock = mysocket()
        try:
            sock.connect(self.host, self.port)
            sock.mysend(('common', 'login', db, user, password))
            res = sock.myreceive()
            sock.disconnect()
        except Exception, e:
            return -1
        return res
    def execute(self,obj, method, *args):
        sock = mysocket()
        try:
            sock.connect(self.host, self.port)
            t1=(('object', 'execute',obj,method,)+args)
            sock.mysend(t1)
            res=sock.myreceive()
            sock.disconnect()
            return res

        except Exception,e:
            import traceback,sys
            info = reduce(lambda x, y: x+y, traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))

session = None
