from Config.Conf import Conf
from extraccion import LimpiadorFromCrawler
from ProcesadoresTexto.Doc2Vec import Doc2Vec, LabeledLineSentence
import luigi

class TrainDoc2Vec(luigi.Task):
	"""
		command line usage:
			luigi --module LuigiTasks.entrenamientoTexto TrainDoc2Vec --carpeta PATH
	"""
	carpeta = luigi.Parameter()

	def requires(self):
		return LimpiadorFromCrawler(self.carpeta)

	def output(self):
		return luigi.LocalTarget('%s/train/check.txt'%self.carpeta)

	def run(self):
		d2v = Doc2Vec()
		input_path = self.input().path
		save_location = self.output().path.replace("txt", "d2v")
		dimension = Conf().getDimVectors()
		with self.output().open("w") as fout:
			d2v.train(input_path, save_location, dimension, epochs = 20, method="DBOW", ides="String")
			fout.write("OK")
		



