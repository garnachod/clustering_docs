from collections import namedtuple

class Conf():
	"""docstring for SparkContexto"""
	class __impl:
		"""docstring for __impl"""
		def __init__(self):
			#dominio web (sin "http://" ni "/" final)
			self.domain = '0.0.0.0:8000'


			self.abspath = '/home/dani/proyecto'
	
			#vectors
			self.dimVectors = 50

		def getDomain(self):
			return self.domain

		def getAbsPath(self):
			return self.abspath

		def getDimVectors(self):
			return self.dimVectors



	# storage for the instance reference
	__instance = None

	def __init__(self):
		if Conf.__instance is None:
			Conf.__instance = Conf.__impl()

	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)
