import unittest
import os
import codecs
from LuigiTasks.extraccion import LimpiadorTextos


class ExtraccionTestCase(unittest.TestCase):

	def lipiadorTextos_1(self):
		"""
			Comprueba que el fichero se genera bien
		"""
		comand = "luigi --module LuigiTasks.extraccion LimpiadorTextos --carpeta /home/dani/proyecto/test"
		os.popen(comand)

		limp = LimpiadorTextos("/home/dani/proyecto/test")
		file = codecs.open(limp.output().path, "r", "utf-8")
		text = file.read()

		self.assertTrue("gallego_file.txt\nabc abc abcdcd adsf " in text)


class ExtraccionTestSuite(unittest.TestSuite):
	"""docstring for ExtraccionTestSuite"""
	def __init__(self):
		super(ExtraccionTestSuite, self).__init__()
		self.addTest(ExtraccionTestCase('lipiadorTextos_1'))


if __name__ == '__main__':
	ts = ExtraccionTestSuite()
	unittest.TextTestRunner(verbosity=2).run(ts)