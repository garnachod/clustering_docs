from Config.Conf import Conf
from ProcesadoresTexto.LimpiadorText import LimpiadorText
import luigi
import os
import codecs
from PyPDF2 import PdfFileReader


def cleanFile(path):
	retorno = ""
	try:
		with codecs.open(path, "r", "utf-8") as fin:
			all_text = fin.read()
			
			retorno = cleanText(all_text)
	except Exception, e:
		pass
	

	return retorno

def cleanText(text):
	retorno = ""
	if text is None:
		return retorno
	if len(text) < 10:
		return retorno

	text = LimpiadorText.getTextHTML(text)
	retorno = LimpiadorText.clean(text)
	retorno = LimpiadorText.stopWordsByLanguagefilter(retorno, "es")
	retorno = LimpiadorText.stemmingByLanguage(retorno, "es")

	return retorno

def readPDF(file):
		returnText = u""
		try:
			with open(file, 'rb') as inputfile:
				ipdf = PdfFileReader(inputfile)
				for page in xrange(min(ipdf.getNumPages(), 10)):
					ipdf_p1 = ipdf.getPage(page)
					ipdf_text = ipdf_p1.extractText()
					returnText += ipdf_text

			return returnText
		except Exception, e:
			return None

class LimpiadorTextos(luigi.Task):
	"""
		command line usage:
			luigi --module LuigiTasks.extraccion LimpiadorTextos --carpeta PATH
	"""
	carpeta = luigi.Parameter()
	
	def output(self):
		return luigi.LocalTarget('%s/limpiado.txt'%self.carpeta, format=luigi.format.TextFormat(encoding='utf8'))

	def run(self):
		with self.output().open("w") as fout:
			for root, dirs, files in os.walk(self.carpeta):
				for directory in dirs:
					for root, dirs, files in os.walk(self.carpeta + "/"+ directory):
						for file in files:
							fout.write(directory.replace("_", "") + u"_"+ file.replace("_", "") + u"\n")
							clean = cleanFile(self.carpeta + "/"+ directory+ "/" + file)
							fout.write(clean + u"\n")



class PDFToText(luigi.Task):
	"""docstring for PDFToText"""
	carpeta = luigi.Parameter()
	
	def output(self):
		return luigi.LocalTarget('%s/limpiado_pdfs.txt'%self.carpeta, format=luigi.format.TextFormat(encoding='utf8'))


	def run(self):
		with self.output().open("w") as fout:
			for root, dirs, files in os.walk(self.carpeta):
				for directory in dirs:
					for root, dirs, files in os.walk(self.carpeta + "/"+ directory):
						for file in files:
							clean = readPDF(self.carpeta + "/"+ directory+ "/" + file)
							if clean != None:
								fout.write(clean + u"\n")
	
class LimpiadorFromCrawler(luigi.Task):
	"""
		command line usage:
			luigi --module LuigiTasks.extraccion LimpiadorFromCrawler --carpeta PATH
	"""
	carpeta = luigi.Parameter()
	
	def output(self):
		return luigi.LocalTarget('%s/limpiado.txt'%self.carpeta, format=luigi.format.TextFormat(encoding='utf8'))

	def run(self):
		with self.output().open("w") as fout:
			for root, dirs, files in os.walk(self.carpeta):
				for directory in dirs:
					for root, dirs, files in os.walk(self.carpeta + "/"+ directory):
						for file in files:
							clean = ""
							if ".application" in file:
								clean = readPDF(self.carpeta + "/"+ directory+ "/" + file)
								clean = cleanText(clean)
							elif ".image" in file:
								pass
							elif ".text" in file:
								clean = cleanFile(self.carpeta + "/"+ directory+ "/" + file)

							if clean != "":
								fout.write(directory.replace("_", "") + u"_"+ file.replace("_", "") + u"\n")
								fout.write(clean + u"\n")