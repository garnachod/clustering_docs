###Codigo para la descarga y proceso de URLs
import urllib
from HTMLParser import HTMLParser
import httplib
from urlparse import urlparse
import urllib2,cookielib
import os, sys
from multiprocessing import Pool
import networkx as nx
import re
import hashlib
import json
import time
import signal

exit = False

def handler(signum, frame):
	global exit    #Modify te global variable
	exit = True

signal.signal(signal.SIGINT, handler)

re_urls = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
################################
#
##Funciones para descargar un HTML
#
###############################
def Download_Item(item):
	"""
	Llama a la descarga de un item y almacena el elemento, esta fuera de la clase para poder utilizar 
	Parameters
	----------
	item : (url a descargar, path)
	Returns
	-------
	"Ok", item, localizacion de la descarga si se ha consultado correctamente
	"Error, item si hay un fallo
	"""
	try:
		#Llamada a la funcion para modificar las cabeceras y evitar que nos baneen
		url, path = item
		
		parser = urlparse(url) 
		loc = parser.netloc
		name = loc.split('.')
		ruta = ''
		route = ''

		#Url de tipo www.uam.es
		if len(name) >= 3:
			#print "---------name :", name[1]
			ruta = name[1] + "_" + hashFile(url[0:100])
			route = path + "/" + ruta + "."
			
		#Url de tipo uam.es
		else:
			#print "---------name :", name[0]
			ruta = name[0] + "_" + hashFile(item[0:100])
			route = path + "/" + ruta + "."
		
		if not os.path.exists(route+"text") and not os.path.exists(route+"image"):
			html_modificado, content_type = modificaCabecerasAndDownload(url)
			if html_modificado == None:
				return "Error", url

			route = route+content_type
			outfile = open(route, "w")
			

			outfile.write(html_modificado)
			outfile.close()
		elif os.path.exists(route+"text"):
			route = route+"text"
		elif os.path.exists(route+"image"):
			route = route+"image"

		return "Ok", url, route
	except Exception, e:
		return "Error", item, None

def Download_Item_noCon(item):
	#Llamada a la funcion para modificar las cabeceras y evitar que nos baneen
	url, path = item
	try:
		parser = urlparse(url) 
		loc = parser.netloc
		name = loc.split('.')
		ruta = ''
		route = '' 
		#Url de tipo www.uam.es
		if len(name) >= 3:
			#print "---------name :", name[1]
			ruta = name[1] + "_" + hashFile(url[0:100])
			route = path + "/" + ruta + "."
			
		#Url de tipo uam.es
		else:
			#print "---------name :", name[0]
			ruta = name[0] + "_" + hashFile(item[0:100])
			route = path + "/" + ruta + "."

		if os.path.exists(route+"text"):
			route = route+"text"
		elif os.path.exists(route+"image"):
			route = route+"image"
		elif os.path.exists(route+"application"):
			route = route+"application"
		
		if  os.path.exists(route):
			return "Ok", url, route
		else:
			return "Error", item, None
	except Exception, e:
		return "Error", item, None
	
	
#Funcion para accesos no autorizados (Modificando cabeceras)
def modificaCabecerasAndDownload(url):
	"""
	Modifica las cabeceras para evitar spidertraps y descarga una web
	Parameters
	----------
	url : url a descargar
	Returns
	-------
	contenido de la web descargada
	"""

	hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
		   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		   'Accept-Encoding': 'none',
		   'Accept-Language': 'en-US,en;q=0.8',
		   'Connection': 'keep-alive'}

	req = urllib2.Request(url, headers=hdr)
	
	try:
		print "------- Downloading: ", url
		page = urllib2.urlopen(req, timeout=10)
		response_headers = page.info()

		# This will just display all the dictionary key-value pairs.  Replace this
		# line with something useful.
		content_type =  response_headers.dict['content-type'].split("/")[0]

	except urllib2.HTTPError, e:
		print "ERROR -> Error en conexion con el Servidor: "
		return None
	except urllib2.URLError, e:
		print "ERROR -> Timed out!"
		return None
	except Exception, e:
		print "ERROR -> Otro error"
		return None
	content = page.read()

	return content, content_type

def hashFile(url):
	"""
	Generacion del hash de una url
	Parameters
	----------
	url : url a generar el hash
	Returns
	-------
	sha384 de la url
	"""

	hash_object = hashlib.sha384(url)
	hex_dig = hash_object.hexdigest()

	return hex_dig

class Crawler(object):
	"""
	Crawler implementado por:
	Daniel Garnacho
	Carlos Rosado
	"""
	def __init__(self, numberOfThreads = 8, numBatchPages = 48):
		"""
		Inicializacion
		Parameters
		----------
		numberOfThreads : numero de procesos paralelos
		numBatchPages : numero de paginas a sacar de la frontera
		"""
		super(Crawler, self).__init__()
		self.DG = nx.DiGraph()
		self.numberDownloads = 0
		self.numberOfThreads = numberOfThreads
		self.numBatchPages = numBatchPages
		self.save_folder = None
		self.iniHosts = {}
		self.p = Pool(self.numberOfThreads) #number of threads to use
	#Funcion para descargar los items desde una url
	def Download_Items(self, conexion=True):
		"""
		Bucle principal de descarga
		"""
		#Inicializacion de variables
		items = None
		if conexion == True:
			items = self.getItems(numberMax = self.numBatchPages)
		else:
			items = self.getItems(numberMax = self.numBatchPages * 10, conexion = conexion)
		i = 0
		print "\n"
		print "-----------------------------------------------"
		print "Download Pags:..........."
		print "-----------------------------------------------"	
		#Creacion de directorio REsults
		if not os.path.exists("Results"):
			os.makedirs("Results")

		resultados_descarga = True
		if conexion == True:
			resultados_descarga = self.p.map(Download_Item, items)
		else:
			resultados_descarga = self.p.map(Download_Item_noCon, items)
			

		for resultado in resultados_descarga:
			if resultado[0] == 'Ok':
				self.setUrlDownloaded(resultado[1])
				self.processPage(resultado[1], resultado[2])
			else:
				if conexion == True:
					self.setUrlError(resultado[1])

		print "---**************************************---"
		print "Las URL han sido descargadas correctamente"
		print "---**************************************---"


	@staticmethod
	def isHostEqual(url1, url2):
		"""
		Comprueba si dos urls tienen el mismo host
		Parameters
		----------
		url1 : url a comprobar con url2
		url2 : url a comprobar
		Returns
		-------
		True si tienen el mismo Host
		"""
		host1 = urlparse(url1).netloc
		host2 = urlparse(url2).netloc
		if host1 == host2:
			return True

		return False

	@staticmethod
	def areHostEqualInList(url, listUrls):
		"""
		Comprueba si hay un host igual en la lista de urls
		Sirve para evitar sobre carga de los servidores
		Parameters
		----------
		url : url a comprobar si esta el servidor en la lista de urls
		listUrls : lista de urls para comprobar
		Returns
		-------
		True si hay un host igual, False en caso contrario
		"""
		flag = False
		for urlcompare, path in listUrls:
			if Crawler.isHostEqual(url, urlcompare):
				flag = True
				break

		return flag

	def processPage(self, url, discLocation):
		"""
		Procesamiento de una pagina, busca los links, los procesa y los inserta en el grafo
		Parameters
		----------
		url : url que se esta procesando
		discLocation : localizacion fisica de la web ya descargada
		"""
		parsed = urlparse(url)
		hostAndProtocol = parsed.scheme + "://" + parsed.netloc
		with open(discLocation) as fin:
			data = fin.read()
			urls = re.findall('<a .* href="?\'?([^"\'>]*)', data, re.VERBOSE)
			#print urls
			for url_ in urls:
				if len(url_) >= 5 and len(url_) < 128:
					if " " not in url_ and ";" not in url_ and "javascript" not in url_ and "mailto:" not in url_:
						if "#" in url_:
							url_ = url_.split("#")[0]

						
						if len(url_) > 1:
							if url_[0] == "/":
								try:
									urlEntradaCrawler = hostAndProtocol + url_
									self.pushUrl(urlEntradaCrawler)
									self.addLink(url, urlEntradaCrawler)
								except Exception, e:
									pass
								
							elif url_[0] == ".":
								urlEntradaCrawler = ""
								splitedURL = url.split("/")
								for ruta in splitedURL[:(len(splitedURL)-1)]:
									urlEntradaCrawler += ruta + "/"

								urlEntradaCrawler += url_
								self.pushUrl(urlEntradaCrawler)
								self.addLink(url, urlEntradaCrawler)
							else:
								self.pushUrl(url_)
								self.addLink(url, url_)

		#self.getItems()




	def getItems(self, numberMax = 30, conexion=True):
		"""
		Extraccion de la frontera
		Parameters
		----------
		numberMax : numero maximo de urls a devolver
		Returns
		-------
		lista de urls que se pueden descargar
		"""
		pages = nx.pagerank(self.DG)
		pagesList = []
		for page in pages:
			pagesList.append((page, pages[page]))

		pages = sorted(pagesList, key=lambda x: x[1], reverse=True)
		ret = []

		#print pages
		for url, pagerank in pages:
			#evita descargar paginas ya descargadas
			if self.DG.node[url]['downloaded'] == False:
				#evita muchas conexiones al mismo host
				if conexion == True:
					if Crawler.areHostEqualInList(url, ret) == False:
						location = self.save_folder + "/" + urlparse(url).netloc
						ret.append((url, location))
				else:
					location = self.save_folder + "/" + urlparse(url).netloc
					ret.append((url, location))

			if len(ret) >= numberMax:
				break

		#items = [("https://www.uam.es/ss/Satellite/es/home/", location), ...]
		#return items
		return ret

	

	def urlFilter(self, url):
		"""
		Filtro de urls que entran al sistema
		por el momento no se filtran las webs, para hacer un crawler de una web concreta o webs anyadir las reglas
		Parameters
		----------
		url : nodo a pasar el filtro
		Returns
		-------
		True si se puede insertar, False en caso contrario
		"""
		if urlparse(url).netloc in self.iniHosts:
			return True
		else:
			return False

	def setUrlDownloaded(self, url):
		"""
		Anyade una propiedad al nodo como descargado
		Parameters
		----------
		url : nodo que se ha descargado
		"""
		self.DG.node[url]['downloaded'] = True
		self.numberDownloads += 1

	def setUrlError(self, url):
		"""
		Anyade una propiedad al nodo como fallido, esto es, no se ha podido descargar 
		y no se volvera a intentar
		Parameters
		----------
		url : nodo que ha fallado
		"""
		if url in self.DG.node:
			self.DG.node[url]['downloaded'] = "error"

	def pushUrl(self, url):
		"""
		Anyade un nodo al grafo si no existe ese nodo ya.
		Parameters
		----------
		url : nodo a insertar
		"""
		if self.DG.has_node(url) == False:
			if re_urls.match(url) != None:
				if self.urlFilter(url):
					self.DG.add_node(url, downloaded=False)
	#1 -> 2
	def addLink(self, url1, url2):
		"""
		Anyade un link de la url1 a la url2
		Parameters
		----------
		url1 : nodo que apunta a la url2
		url2 : nodo que es apuntado por url1
		"""
		if re_urls.match(url2) != None:
			if self.urlFilter(url2):
				self.DG.add_edge(url1,url2)

	
	def initializateJSON(self, jsonLoaded):
		self.save_folder = jsonLoaded["folder"]
		if not os.path.exists(self.save_folder):
			os.mkdir(self.save_folder)
		for link in jsonLoaded["pages"]:
			self.iniHosts[urlparse(link).netloc] = True
			self.pushUrl(link)
			if not os.path.exists(self.save_folder+"/"+urlparse(link).netloc):
				os.mkdir(self.save_folder+"/"+urlparse(link).netloc)


	def getNumberOfDownloads(self):
		"""
		Numero de webs descargadas y almacenadas en disco
		Returns
		-------
		numero de webs descargadas
		"""
		return self.numberDownloads

	def getNumberOfNodes(self):
		"""
		Dado el grafo almacenado se devuelve el numero de nodos
		Returns
		-------
		Numero de links o nodos almacenados
		"""
		return nx.number_of_nodes(self.DG)

	def saveGraph(self):
		"""
		Almacena un grafo en disco en formato gexf, Gephi
		"""
		if self.save_folder == None:
			nx.write_gexf(self.DG, "graph.gexf")
		else:
			nx.write_gexf(self.DG, self.save_folder + "/" + "graph.gexf")

	def readGraph(self):
		"""
		Lee un grafo guardado y lo almacena en el objeto principal
		Si el grafo no existe, se deja el grafo vacio.
		"""
		try:
			self.DG = nx.read_gexf("graph.gexf")
		except Exception, e:
			pass
		
		


###Main de Prueba
if __name__ == "__main__":                                                                
	jsonFile = "formatoCrawler.json"
	c = Crawler()
	c.initializateJSON(json.loads(open(jsonFile, "r").read()))
	lastNumberDownloads = 0

	while True:
		c.Download_Items(conexion=False)
		if c.getNumberOfDownloads() == lastNumberDownloads:
			break
		lastNumberDownloads = c.getNumberOfDownloads()
		print c.getNumberOfDownloads()

	while c.getNumberOfDownloads() < 10000 and exit == False:
		c.Download_Items()
		time.sleep(5)
		if c.getNumberOfDownloads() == lastNumberDownloads:
			break
		lastNumberDownloads = c.getNumberOfDownloads()
		print c.getNumberOfNodes()


	c.saveGraph()
	#parser_HTML("0.html")