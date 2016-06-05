import datetime
from Doc2Vec import Doc2Vec
import os.path
from LimpiadorTweets import LimpiadorTweets 
from Config.Conf import Conf
import numpy as np

class GenerateVectorsFromTweets():
	"""docstring for GenerateVectorsFromText"""
	class __impl:
		""" Implementation of the singleton interface """

		def __init__(self):
			self.models_opened = {}

		def generateVectorText_topics(self, tweets, lang):
			text_final = u""
			for tweet in tweets:
				if tweet.lang == lang:
					tweetLimpio = LimpiadorTweets.clean(tweet.status)
					tweetSinStopWords = LimpiadorTweets.stopWordsByLanguagefilter(tweetLimpio, tweet.lang)
					tweetStemmed = LimpiadorTweets.stemmingByLanguage(tweetSinStopWords, tweet.lang)
					text_final += tweetStemmed + u" "

			return text_final

		def generateVectorText_semantic(self, tweets, lang):
			text_final = u""
			for tweet in tweets:
				if tweet.lang == lang:
					tweetLimpio = LimpiadorTweets.clean(tweet.status)
					tweetSinStopWords = LimpiadorTweets.stopWordsByLanguagefilter(tweetLimpio, tweet.lang)
					text_final += tweetSinStopWords + u" "

			return text_final

		def getVector_topics(self, tweets, lang):
			now = datetime.datetime.now()
			dia = now.day
			mes = now.month
			anyo = now.year
			#configuracion del sistema
			conf = Conf()
			path = conf.getAbsPath()

			model_loc = '%s/LuigiTasks/TrainText/Doc2VecLang_topics/%s/%s/%s_%s.model'%(path, anyo, mes, dia, lang)
			days_minus = 1
			while os.path.isfile(model_loc) == False and days_minus < 20:
				now = datetime.datetime.now() - datetime.timedelta(days=days_minus)
				dia = now.day
				mes = now.month
				anyo = now.year

				model_loc = '%s/LuigiTasks/TrainText/Doc2VecLang_topics/%s/%s/%s_%s.model'%(path, anyo, mes, dia, lang)
				days_minus += 1

			d2v = None
			if model_loc in self.models_opened:
				d2v = self.models_opened[model_loc]
			else:
				d2v = Doc2Vec()
				self.models_opened[model_loc] = d2v
			
			vectorText = self.generateVectorText_topics(tweets, lang).split(" ")
			vector = np.array(d2v.simulateVectorsFromVectorText(vectorText, model_loc))
			return vector / np.linalg.norm(vector)

		def getVector_semantic(self, tweets, lang):
			now = datetime.datetime.now()
			dia = now.day
			mes = now.month
			anyo = now.year
			#configuracion del sistema
			conf = Conf()
			path = conf.getAbsPath()

			model_loc = '%s/LuigiTasks/TrainText/Doc2VecLang_semantic/%s/%s/%s_%s.model'%(path, anyo, mes, dia, lang)
			days_minus = 1
			while os.path.isfile(model_loc) == False and days_minus < 20:
				now = datetime.datetime.now() - datetime.timedelta(days=days_minus)
				dia = now.day
				mes = now.month
				anyo = now.year

				model_loc = '%s/LuigiTasks/TrainText/Doc2VecLang_semantic/%s/%s/%s_%s.model'%(path, anyo, mes, dia, lang)
				days_minus += 1

			d2v = None
			if model_loc in self.models_opened:
				d2v = self.models_opened[model_loc]
			else:
				d2v = Doc2Vec()
				self.models_opened[model_loc] = d2v
			
			vectorText = self.generateVectorText_semantic(tweets, lang).split(" ")
			vector = np.array(d2v.simulateVectorsFromVectorText(vectorText, model_loc))
			return vector / np.linalg.norm(vector)


	# storage for the instance reference
	__instance = None

	def __init__(self):
		if GenerateVectorsFromTweets.__instance is None:
			GenerateVectorsFromTweets.__instance = GenerateVectorsFromTweets.__impl()

	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)
		